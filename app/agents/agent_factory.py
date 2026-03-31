"""
Agent工厂

用于创建Agent实例
"""

from typing import Dict, Type
from app.agents.base import BaseAgent
import logging


logger = logging.getLogger(__name__)


class AgentFactory:
    """Agent工厂类"""

    def __init__(self, skills_registry=None):
        self.skills_registry = skills_registry
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._register_default_agent()

    def _register_default_agent(self):
        """注册默认Agent类"""

        class DefaultAgent(BaseAgent):
            """默认Agent实现"""

            async def execute(self, input_data=None):
                """执行技能链"""
                return await super().execute(input_data)

        self.agent_classes['default'] = DefaultAgent

    def register_agent_class(self, agent_type: str, agent_class: Type[BaseAgent]):
        """注册自定义Agent类"""
        self.agent_classes[agent_type] = agent_class
        logger.info(f"已注册Agent类: {agent_type}")

    def create_agent(self, config: dict, llm_service=None) -> BaseAgent:
        """
        创建Agent实例

        Args:
            config: Agent配置
            llm_service: LLM服务实例

        Returns:
            Agent实例
        """
        agent_type = config.get('agent', {}).get('type', 'default')

        agent_class = self.agent_classes.get(agent_type, BaseAgent)

        if agent_class == BaseAgent:
            # 如果是BaseAgent，创建一个简单的实现
            class SimpleAgent(BaseAgent):
                async def execute(self, input_data=None):
                    return await super().execute(input_data)

            agent_class = SimpleAgent

        agent = agent_class(config, self.skills_registry, llm_service)
        logger.info(f"创建Agent: {agent.agent_id}")
        return agent
