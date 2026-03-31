"""
LLM 服务 - 统一的大语言模型调用接口

提供统一的 LLM 调用接口，屏蔽不同提供商的差异。
"""

import os
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from enum import Enum


logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """LLM 提供商类型"""
    DEEPSEEK = "deepseek"
    QIANWEN = "qianwen"
    WENXIN = "wenxin"
    OPENROUTER = "openrouter"


class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成文本

        Args:
            prompt: 用户提示词
            max_tokens: 最大生成 token 数
            temperature: 温度参数 (0-2)
            system_message: 系统消息

        Returns:
            包含 generated_text, tokens_used, model, provider 等字段的字典
        """
        pass

    @abstractmethod
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        基于历史对话生成文本

        Args:
            messages: 消息历史 [{"role": "user", "content": "..."}, ...]
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Returns:
            包含 generated_text, tokens_used, model, provider 等字段的字典
        """
        pass


class DeepSeekProvider(LLMProvider):
    """DeepSeek 提供商"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://api.deepseek.com')
        self.model = kwargs.get('model', 'deepseek-chat')
        self._client = None

    async def _get_client(self):
        """获取异步客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 DeepSeek 生成文本"""
        try:
            client = await self._get_client()

            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                'generated_text': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': self.model,
                'provider': LLMProviderType.DEEPSEEK
            }

        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.DEEPSEEK
            }

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """基于历史对话生成"""
        try:
            client = await self._get_client()

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                'generated_text': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': self.model,
                'provider': LLMProviderType.DEEPSEEK
            }

        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.DEEPSEEK
            }


class QianwenProvider(LLMProvider):
    """通义千问提供商"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'qwen-plus')
        # 初始化 dashscope
        try:
            import dashscope
            dashscope.api_key = api_key
        except ImportError:
            logger.warning("dashscope 未安装")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用通义千问生成文本"""
        try:
            import dashscope
            from dashscope import Generation

            messages = [{'role': 'user', 'content': prompt}]
            if system_message:
                messages.insert(0, {'role': 'system', 'content': system_message})

            response = Generation.call(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                result_format='message'
            )

            if response.status_code == 200:
                return {
                    'generated_text': response.output.choices[0]['message']['content'],
                    'tokens_used': response.usage.total_tokens,
                    'model': self.model,
                    'provider': LLMProviderType.QIANWEN
                }
            else:
                return {
                    'error': response.message,
                    'provider': LLMProviderType.QIANWEN
                }

        except Exception as e:
            logger.error(f"通义千问 API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.QIANWEN
            }

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """基于历史对话生成"""
        try:
            import dashscope
            from dashscope import Generation

            response = Generation.call(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                result_format='message'
            )

            if response.status_code == 200:
                return {
                    'generated_text': response.output.choices[0]['message']['content'],
                    'tokens_used': response.usage.total_tokens,
                    'model': self.model,
                    'provider': LLMProviderType.QIANWEN
                }
            else:
                return {
                    'error': response.message,
                    'provider': LLMProviderType.QIANWEN
                }

        except Exception as e:
            logger.error(f"通义千问 API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.QIANWEN
            }


class WenxinProvider(LLMProvider):
    """文心一言提供商"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.secret_key = kwargs.get('secret_key', '')
        self.model = kwargs.get('model', 'ERNIE-4.0-8K')
        self._access_token = None

    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self._access_token:
            return self._access_token

        import aiohttp
        import json

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                result = await resp.json()
                self._access_token = result.get('access_token')
                return self._access_token

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用文心一言生成文本"""
        try:
            import aiohttp

            access_token = await self._get_access_token()
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"

            messages = []
            if system_message:
                messages.append({"role": "user", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()

                    if 'error_code' not in result:
                        return {
                            'generated_text': result.get('result', ''),
                            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                            'model': self.model,
                            'provider': LLMProviderType.WENXIN
                        }
                    else:
                        return {
                            'error': result.get('error_msg', 'Unknown error'),
                            'provider': LLMProviderType.WENXIN
                        }

        except Exception as e:
            logger.error(f"文心一言 API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.WENXIN
            }

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """基于历史对话生成"""
        try:
            import aiohttp

            access_token = await self._get_access_token()
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"

            payload = {
                "messages": messages,
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()

                    if 'error_code' not in result:
                        return {
                            'generated_text': result.get('result', ''),
                            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                            'model': self.model,
                            'provider': LLMProviderType.WENXIN
                        }
                    else:
                        return {
                            'error': result.get('error_msg', 'Unknown error'),
                            'provider': LLMProviderType.WENXIN
                        }

        except Exception as e:
            logger.error(f"文心一言 API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.WENXIN
            }


class OpenRouterProvider(LLMProvider):
    """OpenRouter 提供商 - 支持多个免费模型"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'https://openrouter.ai/api/v1')
        # 默认使用免费的Qwen3 Next 80B模型
        self.model = kwargs.get('model', 'qwen/qwen3-next-80b-a3b-instruct:free')
        self._client = None

    async def _get_client(self):
        """获取异步客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/agent-matrix",
                    "X-Title": "Agent Matrix"
                }
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 OpenRouter 生成文本"""
        try:
            client = await self._get_client()

            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                'generated_text': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': self.model,
                'provider': LLMProviderType.OPENROUTER
            }

        except Exception as e:
            logger.error(f"OpenRouter API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.OPENROUTER
            }

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """基于历史对话生成"""
        try:
            client = await self._get_client()

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                'generated_text': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': self.model,
                'provider': LLMProviderType.OPENROUTER
            }

        except Exception as e:
            logger.error(f"OpenRouter API 调用失败: {str(e)}")
            return {
                'error': str(e),
                'provider': LLMProviderType.OPENROUTER
            }


class LLMService:
    """
    LLM 服务 - 统一的大语言模型调用接口

    这是唯一需要知道具体 LLM 提供商实现的地方。
    Skill 通过此服务调用 LLM，无需知道具体使用的是哪个提供商。
    """

    def __init__(self, api_keys: Dict[str, str], default_provider: str = LLMProviderType.DEEPSEEK):
        """
        初始化 LLM 服务

        Args:
            api_keys: API 密钥字典 {provider_name: api_key}
            default_provider: 默认提供商
        """
        self.api_keys = api_keys
        self.default_provider = default_provider
        self._providers: Dict[LLMProviderType, LLMProvider] = {}

    def _get_provider(self, provider_type: LLMProviderType) -> Optional[LLMProvider]:
        """
        获取提供商实例

        Args:
            provider_type: 提供商类型

        Returns:
            提供商实例
        """
        if provider_type in self._providers:
            return self._providers[provider_type]

        api_key = self.api_keys.get(provider_type)
        if not api_key:
            logger.error(f"未找到 {provider_type} 的 API 密钥")
            return None

        # 创建提供商实例
        if provider_type == LLMProviderType.DEEPSEEK:
            provider = DeepSeekProvider(api_key)
        elif provider_type == LLMProviderType.QIANWEN:
            provider = QianwenProvider(api_key)
        elif provider_type == LLMProviderType.WENXIN:
            provider = WenxinProvider(
                api_key,
                secret_key=self.api_keys.get('wenxin_secret', '')
            )
        elif provider_type == LLMProviderType.OPENROUTER:
            provider = OpenRouterProvider(api_key)
        else:
            logger.error(f"不支持的提供商类型: {provider_type}")
            return None

        self._providers[provider_type] = provider
        return provider

    async def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成文本

        Args:
            prompt: 用户提示词
            provider: 提供商类型 (deepseek/qianwen/wenxin)，默认使用 default_provider
            max_tokens: 最大生成 token 数
            temperature: 温度参数 (0-2)
            system_message: 系统消息

        Returns:
            包含 generated_text, tokens_used, model, provider 等字段的字典
        """
        provider_type = LLMProviderType(provider or self.default_provider)
        llm_provider = self._get_provider(provider_type)

        if not llm_provider:
            return {
                'error': f'无法初始化 LLM 提供商: {provider_type}',
                'provider': provider_type
            }

        return await llm_provider.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_message=system_message
        )

    async def generate_from_template(
        self,
        template: str,
        variables: Dict[str, str],
        provider: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于模板生成文本

        Args:
            template: 提示词模板，支持 {variable} 占位符
            variables: 变量字典
            provider: 提供商类型
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            system_message: 系统消息

        Returns:
            包含 generated_text, tokens_used, model, provider 等字段的字典
        """
        # 替换模板变量
        prompt = template
        for key, value in variables.items():
            # 将非字符串类型转换为字符串
            if not isinstance(value, str):
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                else:
                    value = str(value)
            prompt = prompt.replace(f'{{{key}}}', value)

        return await self.generate_text(
            prompt=prompt,
            provider=provider,
            max_tokens=max_tokens,
            temperature=temperature,
            system_message=system_message
        )

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        基于历史对话生成文本

        Args:
            messages: 消息历史
            provider: 提供商类型
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Returns:
            包含 generated_text, tokens_used, model, provider 等字段的字典
        """
        provider_type = LLMProviderType(provider or self.default_provider)
        llm_provider = self._get_provider(provider_type)

        if not llm_provider:
            return {
                'error': f'无法初始化 LLM 提供商: {provider_type}',
                'provider': provider_type
            }

        return await llm_provider.generate_with_history(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )


def create_llm_service_from_config(config: Dict[str, Any]) -> LLMService:
    """
    从配置创建 LLM 服务

    Args:
        config: 配置字典，格式如下:
            {
                "default_provider": "deepseek",
                "api_keys": {
                    "deepseek": "sk-xxx",
                    "qianwen": "sk-yyy",
                    "wenxin": "sk-zzz",
                    "wenxin_secret": "secret-aaa"
                }
            }

    Returns:
        LLMService 实例
    """
    return LLMService(
        api_keys=config.get('api_keys', {}),
        default_provider=config.get('default_provider', LLMProviderType.DEEPSEEK)
    )


def create_llm_service_from_env() -> LLMService:
    """
    从环境变量创建 LLM 服务

    环境变量:
        - DEEPSEEK_API_KEY
        - QIANWEN_API_KEY
        - WENXIN_API_KEY
        - WENXIN_SECRET_KEY
        - LLM_DEFAULT_PROVIDER (可选，默认 deepseek)

    Returns:
        LLMService 实例
    """
    api_keys = {}
    if os.getenv('DEEPSEEK_API_KEY'):
        api_keys['deepseek'] = os.getenv('DEEPSEEK_API_KEY')
    if os.getenv('QIANWEN_API_KEY'):
        api_keys['qianwen'] = os.getenv('QIANWEN_API_KEY')
    if os.getenv('WENXIN_API_KEY'):
        api_keys['wenxin'] = os.getenv('WENXIN_API_KEY')
    if os.getenv('WENXIN_SECRET_KEY'):
        api_keys['wenxin_secret'] = os.getenv('WENXIN_SECRET_KEY')
    if os.getenv('OPENROUTER_API_KEY'):
        api_keys['openrouter'] = os.getenv('OPENROUTER_API_KEY')

    default_provider = os.getenv('LLM_DEFAULT_PROVIDER', 'deepseek')

    return LLMService(
        api_keys=api_keys,
        default_provider=default_provider
    )
