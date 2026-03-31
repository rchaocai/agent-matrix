"""
系统设置API路由
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from app.config import settings
from app.core.llm_service import LLMService
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_settings() -> Dict[str, Any]:
    """获取系统设置"""
    return {
        "systemName": "觉知矩阵",
        "language": "zh-CN",
        "timezone": "Asia/Shanghai",
        "theme": "zen",
        "llm": {
            "defaultProvider": settings.llm_default_provider,
            "providers": {
                "qianwen": {
                    "enabled": bool(settings.llm_providers.get("qianwen", {}).get("api_key")),
                    "model": settings.llm_providers.get("qianwen", {}).get("model", "qwen-plus")
                },
                "deepseek": {
                    "enabled": bool(settings.llm_providers.get("deepseek", {}).get("api_key")),
                    "model": settings.llm_providers.get("deepseek", {}).get("model", "deepseek-chat")
                },
                "wenxin": {
                    "enabled": bool(settings.llm_providers.get("wenxin", {}).get("api_key")),
                    "model": settings.llm_providers.get("wenxin", {}).get("model", "ernie-bot")
                }
            }
        },
        "review": {
            "sensitiveWordEnabled": True,
            "sensitiveCategories": ["politics", "porn", "violence", "spam", "illegal"],
            "customWords": "",
            "qualityScoreEnabled": True,
            "minQualityScore": 60,
            "weights": {
                "readability": 30,
                "completeness": 40,
                "attractiveness": 30
            }
        },
        "notification": {
            "enabled": True,
            "channels": ["email"],
            "events": {
                "agentCompleted": True,
                "contentApproved": True,
                "contentRejected": True,
                "publishSuccess": True,
                "publishFailed": True,
                "systemError": True
            }
        }
    }


@router.put("/")
async def update_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    """更新系统设置"""
    try:
        # 更新LLM配置
        if "llm" in data:
            llm_config = data["llm"]

            # 验证配置
            provider = llm_config.get("provider") or llm_config.get("defaultProvider")
            if provider:
                if provider == "deepseek":
                    api_key = llm_config.get("apiKey") or llm_config.get("api_key")
                    if api_key:
                        from app.config import settings
                        settings.DEEPSEEK_API_KEY = api_key
                        base_url = llm_config.get("baseUrl") or llm_config.get("base_url")
                        if base_url:
                            settings.DEEPSEEK_BASE_URL = base_url
                        logger.info(f"DeepSeek配置已更新")

                elif provider == "openai":
                    api_key = llm_config.get("apiKey") or llm_config.get("api_key")
                    if api_key:
                        settings.OPENAI_API_KEY = api_key
                        base_url = llm_config.get("baseUrl") or llm_config.get("base_url")
                        if base_url:
                            settings.OPENAI_BASE_URL = base_url
                        logger.info(f"OpenAI配置已更新")

        # 更新调度配置
        if "scheduler" in data:
            scheduler_config = data["scheduler"]
            # TODO: 实现调度器配置更新
            logger.info(f"调度器配置已更新")

        # TODO: 保存到配置文件（可选）
        # config_path = Path("config/settings.yaml")
        # with open(config_path, 'w', encoding='utf-8') as f:
        #     yaml.dump(data, f, allow_unicode=True)

        return {"success": True, "message": "设置已保存"}

    except Exception as e:
        logger.error(f"更新设置失败: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/test-llm")
async def test_llm_connection(provider: str = Query(...)) -> Dict[str, Any]:
    """测试LLM连接"""
    try:
        if provider == "deepseek":
            from app.config import settings
            if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "sk-xxx":
                return {
                    "success": False,
                    "message": "DeepSeek API密钥未配置或为默认值"
                }

            llm_service = LLMService(provider="deepseek")
            result = await llm_service.generate("测试", max_tokens=10)

            return {
                "success": True,
                "message": f"{provider} 连接测试成功",
                "response": result[:100] if result else "无响应"
            }

        elif provider == "openai":
            from app.config import settings
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-xxx":
                return {
                    "success": False,
                    "message": "OpenAI API密钥未配置或为默认值"
                }

            llm_service = LLMService(provider="openai")
            result = await llm_service.generate("Hello", max_tokens=10)

            return {
                "success": True,
                "message": f"{provider} 连接测试成功",
                "response": result[:100] if result else "无响应"
            }

        else:
            return {"success": False, "message": f"不支持的LLM提供商: {provider}"}

    except Exception as e:
        logger.error(f"LLM连接测试失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}"
        }
