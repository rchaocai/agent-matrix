"""
Agent管理器

管理Agent的生命周期
"""

from typing import Dict, List, Optional
from pathlib import Path
import yaml
import logging

from app.agents.base import BaseAgent
from app.agents.agent_factory import AgentFactory
from app.models import Agent, Task
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class AgentManager:
    """Agent生命周期管理"""

    def __init__(self):
        from app.config import settings
        self.settings = settings
        self.agent_factory = AgentFactory()
        self.active_agents: Dict[str, BaseAgent] = {}
        self.skills_registry = None  # 将在SkillLoader实现后注入
        self.llm_service = None  # LLM 服务

    def set_skills_registry(self, skills_registry):
        """设置技能注册表"""
        self.skills_registry = skills_registry
        self.agent_factory.skills_registry = skills_registry

    def set_llm_service(self, llm_service):
        """设置 LLM 服务"""
        self.llm_service = llm_service
        # 更新所有活跃 Agent 的 LLM 服务
        for agent in self.active_agents.values():
            agent.set_llm_service(llm_service)

    async def load_agents_from_config(self):
        """从配置文件加载所有Agent"""
        # 确保数据库已初始化
        from tortoise import Tortoise
        if not Tortoise._inited:
            from app.config import settings
            await Tortoise.init(
                db_url=settings.database_url,
                modules={'models': ['app.models.agent', 'app.models.content',
                                   'app.models.task', 'app.models.draft']}
            )

        agents_dir = Path(self.settings.agents_config_dir)
        if not agents_dir.exists():
            logger.warning(f"Agent配置目录不存在: {agents_dir}")
            return

        config_files = list(agents_dir.glob("*.yaml"))
        logger.info(f"发现 {len(config_files)} 个Agent配置文件")

        for config_file in config_files:
            await self.load_agent(config_file)

    async def load_agent(self, config_path: Path) -> Optional[BaseAgent]:
        """
        从配置文件加载Agent

        Args:
            config_path: 配置文件路径

        Returns:
            Agent实例
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            agent_id = config.get('agent', {}).get('id')
            if not agent_id:
                logger.error(f"配置文件缺少agent.id: {config_path}")
                return None

            # 创建Agent实例，传递 LLM 服务
            agent = self.agent_factory.create_agent(config, llm_service=self.llm_service)

            # 保存到数据库
            agent_model = await Agent.get_or_none(id=agent_id)
            if agent_model:
                await agent_model.update_from_dict({
                    'name': agent.name,
                    'config': yaml.dump(config, allow_unicode=True),
                    'enabled': agent.enabled
                })
                await agent_model.save()
                # 从数据库获取绑定的账户ID
                if agent_model.account_id:
                    agent.account_id = agent_model.account_id
                    logger.info(f"Agent {agent_id} 从数据库加载绑定账户: {agent_model.account_id}")
            else:
                agent_model = await Agent.create(
                    id=agent_id,
                    name=agent.name,
                    config=yaml.dump(config, allow_unicode=True),
                    enabled=agent.enabled
                )
                logger.info(f"Agent {agent_id} 新创建到数据库")

            # 如果Agent启用，加入活跃列表
            if agent.is_enabled():
                self.active_agents[agent_id] = agent
                logger.info(f"Agent加载成功: {agent_id}, account_id={getattr(agent, 'account_id', None)}")

                # 调度Agent（如果配置了schedule）
                from app.main import scheduler_service
                if scheduler_service:
                    await scheduler_service.schedule_agent(config)

            return agent

        except Exception as e:
            logger.error(f"加载Agent失败 {config_path}: {str(e)}", exc_info=True)
            return None

    async def run_agent(self, agent_id: str):
        """
        执行Agent

        Args:
            agent_id: Agent ID
        """
        from datetime import datetime

        agent = self.active_agents.get(agent_id)
        if not agent:
            logger.error(f"Agent不存在或未启用: {agent_id}")
            return

        # 创建任务记录
        task = await Task.create(
            agent_id=agent_id,
            agent_name=agent.name,  # 记录Agent名称
            status="running",
            started_at=datetime.now(timezone.utc),
            skill_results=[],  # 初始化空数组
            metadata={}
        )

        skill_results = []
        try:
            # 执行Agent，拦截skill执行结果
            result = await self._execute_agent_with_tracking(agent, skill_results)

            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            # 确保result是JSON可序列化的
            import json
            try:
                # 转换为JSON字符串
                task.result = json.dumps(result, ensure_ascii=False)
            except (TypeError, ValueError):
                # 如果无法序列化，转换为字符串
                task.result = json.dumps({"raw": str(result)}, ensure_ascii=False)

            # 转换skill_results为JSON字符串
            task.skill_results = json.dumps(skill_results, ensure_ascii=False)
            
            # 转换metadata为JSON字符串
            task.metadata = json.dumps({}, ensure_ascii=False)
            
            await task.save()

            logger.info(f"Agent {agent_id} 执行完成，结果: {result}")

        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.now(timezone.utc)
            task.error = str(e)
            # 转换skill_results为JSON字符串
            task.skill_results = json.dumps(skill_results, ensure_ascii=False)
            # 转换metadata为JSON字符串
            task.metadata = json.dumps({}, ensure_ascii=False)
            await task.save()
            logger.error(f"Agent {agent_id} 执行失败: {str(e)}", exc_info=True)
            raise

    async def _execute_agent_with_tracking(self, agent, skill_results: list):
        """
        执行Agent并跟踪每个skill的结果
        """
        import logging
        logger = logging.getLogger(__name__)

        result = {}
        for skill_config in agent.skill_chain:
            skill_name = skill_config.get('skill')
            skill_config_data = skill_config.get('config', {})
            skill_config_data['agent_id'] = agent.agent_id
            
            # 传递 Agent 顶层的 account_id 到每个 skill
            if hasattr(agent, 'account_id') and agent.account_id:
                skill_config_data['account_id'] = agent.account_id
                logger.info(f"Agent {agent.agent_id} 传递 account_id={agent.account_id} 到 skill {skill_name}")
            else:
                logger.warning(f"Agent {agent.agent_id} 没有 account_id，hasattr={hasattr(agent, 'account_id')}, value={getattr(agent, 'account_id', None)}")

            skill_result = {
                "skill": skill_name,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
                "result": None
            }

            logger.info(f"Agent {agent.agent_id} 执行技能: {skill_name}")

            try:
                result = await agent._execute_skill(skill_name, result, skill_config_data)
                
                # 检查返回结果中的 success 字段
                if isinstance(result, dict) and result.get('success') is False:
                    skill_result["status"] = "failed"
                    skill_result["error"] = result.get('error', '执行失败')
                    skill_result["result"] = result
                    skill_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    logger.warning(f"技能 {skill_name} 返回失败: {result.get('error')}")
                    skill_results.append(skill_result)
                    # 不继续执行后续skill，直接返回
                    return result
                else:
                    skill_result["status"] = "success"
                    skill_result["result"] = result
                    skill_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    skill_results.append(skill_result)
            except Exception as e:
                skill_result["status"] = "failed"
                skill_result["error"] = str(e)
                skill_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                logger.error(f"执行技能 {skill_name} 失败: {str(e)}", exc_info=True)
                skill_results.append(skill_result)
                raise  # 继续抛出异常，中断后续skill

        return result

    async def stop_agent(self, agent_id: str):
        """停止Agent"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            logger.info(f"Agent已停止: {agent_id}")

    async def reload_agent(self, agent_id: str):
        """重新加载Agent配置"""
        await self.stop_agent(agent_id)
        yaml_filename = f"{agent_id}.yaml" if agent_id.endswith('_agent') else f"{agent_id}_agent.yaml"
        config_path = Path(self.settings.agents_config_dir) / yaml_filename
        if config_path.exists():
            await self.load_agent(config_path)

    def get_active_agents(self) -> List[str]:
        """获取活跃Agent列表"""
        return list(self.active_agents.keys())

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取指定Agent"""
        return self.active_agents.get(agent_id)
