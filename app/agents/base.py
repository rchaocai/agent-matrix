"""
Agent基类

所有Agent的抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, config: dict, skills_registry=None, llm_service=None):
        self.config = config
        self.agent_config = config.get('agent', {})
        self.agent_id = self.agent_config.get('id')
        self.name = self.agent_config.get('name')
        self.enabled = self.agent_config.get('enabled', True)
        self.persona = self.agent_config.get('persona', {})
        # LLM 提供商配置（Agent 级别）
        self.llm_provider = self.agent_config.get('llm_provider', 'deepseek')
        self.skill_chain = self.agent_config.get('skill_chain', [])
        self.skills_registry = skills_registry
        self.llm_service = llm_service  # LLM 服务实例
        self.state = {}
        # 绑定的账户ID（用于发布）
        self.account_id = self.agent_config.get('account_id')

    def set_llm_service(self, llm_service):
        """设置 LLM 服务"""
        self.llm_service = llm_service

    def get_llm_provider(self) -> str:
        """获取 Agent 的 LLM 提供商"""
        return self.llm_provider

    @abstractmethod
    async def execute(self, input_data: Any = None) -> Dict[str, Any]:
        """
        执行Agent的技能链

        Args:
            input_data: 输入数据

        Returns:
            执行结果
        """
        result = input_data or {}

        # 按顺序执行技能链
        for skill_config in self.skill_chain:
            skill_name = skill_config.get('skill')
            skill_config_data = skill_config.get('config', {})

            # 将 Agent ID 添加到配置中
            skill_config_data['agent_id'] = self.agent_id

            logger.info(f"Agent {self.agent_id} 执行技能: {skill_name}")

            try:
                result = await self._execute_skill(skill_name, result, skill_config_data)
            except Exception as e:
                logger.error(f"执行技能 {skill_name} 失败: {str(e)}", exc_info=True)
                raise

        return result

    async def _execute_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict
    ) -> Any:
        """
        执行单个技能

        Args:
            skill_name: 技能名称
            input_data: 输入数据
            config: 技能配置

        Returns:
            技能执行结果
        """
        if self.skills_registry:
            # 传递 LLM 服务给 Skill（如果 Skill 需要）
            return await self.skills_registry.execute_skill(
                skill_name,
                input_data,
                config,
                llm_service=self.llm_service,
                llm_provider=self.llm_provider
            )
        else:
            # 简单实现，后续会被SkillLoader替代
            logger.warning(f"Skills registry未初始化，跳过技能: {skill_name}")
            return input_data

    def get_persona(self) -> Dict:
        """获取Agent人设"""
        return self.persona

    def is_enabled(self) -> bool:
        """检查Agent是否启用"""
        return self.enabled
