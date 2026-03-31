"""
审核设置API路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.models.review_settings import ReviewSettings

logger = logging.getLogger(__name__)

router = APIRouter()


class ReviewSettingsResponse(BaseModel):
    """审核设置响应模型"""
    sensitive_word_enabled: bool = Field(..., description="启用敏感词检测")
    sensitive_categories: List[str] = Field(..., description="检测类别")
    custom_words: Optional[str] = Field(default=None, description="自定义敏感词")
    quality_score_enabled: bool = Field(..., description="启用质量评分")
    min_quality_score: int = Field(..., description="最低质量阈值")
    weights: dict = Field(..., description="评分权重")


class ReviewSettingsUpdate(BaseModel):
    """审核设置更新模型"""
    sensitive_word_enabled: Optional[bool] = None
    sensitive_categories: Optional[List[str]] = None
    custom_words: Optional[str] = None
    quality_score_enabled: Optional[bool] = None
    min_quality_score: Optional[int] = None
    weights: Optional[dict] = None


@router.get("", response_model=ReviewSettingsResponse, summary="获取审核设置")
async def get_review_settings():
    """
    获取审核设置

    ## 返回结果
    ```json
    {
      "sensitive_word_enabled": true,
      "sensitive_categories": ["politics", "porn", "violence"],
      "custom_words": "",
      "quality_score_enabled": true,
      "min_quality_score": 60,
      "weights": {
        "readability": 30,
        "completeness": 40,
        "attractiveness": 30
      }
    }
    ```
    """
    try:
        settings = await ReviewSettings.get_settings()
        
        return ReviewSettingsResponse(
            sensitive_word_enabled=settings.sensitive_word_enabled,
            sensitive_categories=settings.sensitive_categories,
            custom_words=settings.custom_words,
            quality_score_enabled=settings.quality_score_enabled,
            min_quality_score=settings.min_quality_score,
            weights=settings.weights
        )
    except Exception as e:
        logger.error(f"获取审核设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取审核设置失败: {str(e)}")


@router.put("", response_model=ReviewSettingsResponse, summary="更新审核设置")
async def update_review_settings(data: ReviewSettingsUpdate):
    """
    更新审核设置

    ## 请求参数
    - **sensitive_word_enabled**: 是否启用敏感词检测
    - **sensitive_categories**: 检测类别
    - **custom_words**: 自定义敏感词
    - **quality_score_enabled**: 是否启用质量评分
    - **min_quality_score**: 最低质量阈值
    - **weights**: 评分权重

    ## 返回结果
    ```json
    {
      "sensitive_word_enabled": true,
      "sensitive_categories": ["politics", "porn", "violence"],
      ...
    }
    ```
    """
    try:
        settings = await ReviewSettings.get_settings()
        
        if data.sensitive_word_enabled is not None:
            settings.sensitive_word_enabled = data.sensitive_word_enabled
        
        if data.sensitive_categories is not None:
            settings.sensitive_categories = data.sensitive_categories
        
        if data.custom_words is not None:
            settings.custom_words = data.custom_words
        
        if data.quality_score_enabled is not None:
            settings.quality_score_enabled = data.quality_score_enabled
        
        if data.min_quality_score is not None:
            settings.min_quality_score = data.min_quality_score
        
        if data.weights is not None:
            settings.weights = data.weights
        
        await settings.save()
        
        logger.info(f"审核设置已更新: {data}")
        
        return ReviewSettingsResponse(
            sensitive_word_enabled=settings.sensitive_word_enabled,
            sensitive_categories=settings.sensitive_categories,
            custom_words=settings.custom_words,
            quality_score_enabled=settings.quality_score_enabled,
            min_quality_score=settings.min_quality_score,
            weights=settings.weights
        )
    except Exception as e:
        logger.error(f"更新审核设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新审核设置失败: {str(e)}")
