"""
渲染 API 路由
提供独立的文本转图片渲染接口
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import uuid

from app.skills.skills.generation.render.scripts.render import RenderEngine
from app.skills.skills.generation.template_generator.scripts.generator import TemplateGenerator
from app.core.llm_service import create_llm_service_from_env

logger = logging.getLogger(__name__)

router = APIRouter()


class RenderRequest(BaseModel):
    """渲染请求模型"""

    title: str = Field(..., description="标题文本")
    content: str = Field(..., description="正文内容")
    platform: str = Field(default="xiaohongshu", description="目标平台 (xiaohongshu, douyin)")
    template: str = Field(default="minimal", description="模板名称")
    color_scheme: Optional[str] = Field(default=None, description="配色方案名称")
    font_scheme: Optional[str] = Field(default=None, description="字体方案名称")
    max_length: Optional[int] = Field(default=None, description="单张最大字数（超过自动分页）")
    split_long: bool = Field(default=True, description="是否自动分割长文")
    output_dir: str = Field(default="data/images/drafts", description="输出目录")
    author: Optional[str] = Field(default=None, description="作者名称（显示在页脚）")


class RenderResponse(BaseModel):
    """渲染响应模型"""

    status: str = Field(..., description="状态 (success/error)")
    images: List[Dict[str, Any]] = Field(..., description="生成的图片信息列表")
    total_pages: int = Field(..., description="总页数")
    total_images: int = Field(..., description="总图片数")
    platform: str = Field(..., description="使用的平台")
    template: str = Field(..., description="使用的模板")


class PreviewRequest(BaseModel):
    """预览请求模型"""

    template: str = Field(..., description="模板名称")
    platform: str = Field(default="xiaohongshu", description="目标平台")
    color_scheme: Optional[str] = Field(default=None, description="配色方案名称")
    sample: bool = Field(default=True, description="是否使用示例内容")
    title: Optional[str] = Field(default=None, description="自定义标题")
    content: Optional[str] = Field(default=None, description="自定义内容")
    author: Optional[str] = Field(default=None, description="自定义作者")


@router.post("/from-text", response_model=RenderResponse, summary="渲染文本为图片")
async def render_from_text(request: RenderRequest):
    """
    将文本内容渲染为平台图文卡片

    ## 功能说明
    - 接收标题和正文内容
    - 根据目标平台应用相应的排版规则
    - 自动处理长文分割（超过字数限制）
    - 输出高清 PNG 图片

    ## 请求参数
    - **title**: 标题文本
    - **content**: 正文内容
    - **platform**: 目标平台 (xiaohongshu, douyin)
    - **template**: 模板名称
    - **max_length**: 单张最大字数（可选，默认使用平台配置）
    - **split_long**: 是否自动分割长文（默认 true）
    - **output_dir**: 输出目录（默认 data/images）
    - **author**: 作者名称（可选）

    ## 返回结果
    ```json
    {
      "status": "success",
      "images": [
        {
          "index": 1,
          "path": "/data/images/20250226/xiaohongshu_minimal_1.png",
          "url": "http://localhost:8000/static/images/..."
        }
      ],
      "total_pages": 1,
      "total_images": 1
    }
    ```
    """
    try:
        # 创建渲染引擎
        engine = RenderEngine()

        # 准备额外选项
        options = {}
        if request.author:
            options["author"] = request.author

        # 执行渲染
        result = await engine.render(
            title=request.title,
            content=request.content,
            platform=request.platform,
            template=request.template,
            color_scheme=request.color_scheme,
            font_scheme=request.font_scheme,
            max_length=request.max_length,
            split_long=request.split_long,
            output_dir=request.output_dir,
            **options,
        )

        # 构建图片信息列表
        images = []
        for i, image_path in enumerate(result.get("rendered_images", []), 1):
            # 生成相对路径用于 URL
            path_obj = Path(image_path)
            relative_path = path_obj.relative_to("data")
            url = f"/static/{relative_path}"

            images.append(
                {
                    "index": i,
                    "path": image_path,
                    "url": url,
                }
            )

        return RenderResponse(
            status="success",
            images=images,
            total_pages=result.get("total_pages", 0),
            total_images=len(images),
            platform=result.get("platform", request.platform),
            template=result.get("template", request.template),
        )

    except Exception as e:
        logger.error(f"渲染失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


@router.get("/templates/html", summary="获取模板HTML预览")
async def get_template_html(
    template: str = Query(..., description="模板名称"),
    platform: str = Query(default="xiaohongshu", description="目标平台"),
    color_scheme: Optional[str] = Query(None, description="配色方案名称"),
    sample: bool = Query(True, description="是否使用示例内容"),
    title: Optional[str] = Query(None, description="自定义标题"),
    content: Optional[str] = Query(None, description="自定义内容"),
    author: Optional[str] = Query(None, description="自定义作者")
):
    """
    获取模板的HTML预览（不渲染为图片）

    ## 优势
    - 极快响应，无需启动浏览器
    - 无需下载图片文件
    - 前端用iframe显示即可
    - 适合实时预览

    ## 返回结果
    返回HTML字符串
    """
    try:
        # 确定使用的内容
        if sample:
            sample_content = {
                "xiaohongshu": {
                    "title": "禅修的智慧",
                    "content": "禅修的核心智慧在于觉知当下。当我们放下过去的执念和未来的焦虑，专注于当下的呼吸和感受，内心便能得到真正的宁静。",
                    "author": "@佛学行者",
                },
                "douyin": {
                    "title": "短视频创作技巧",
                    "content": "创作优质短视频的三个关键：1. 抓住前3秒黄金时间 2. 保持内容节奏紧凑 3. 引导用户互动",
                    "author": "@创作达人",
                },
            }
            sample = sample_content.get(platform, sample_content["xiaohongshu"])
        else:
            sample = {
                "title": title or "标题",
                "content": content or "在这里输入内容...",
                "author": author,
            }

        # 创建渲染引擎
        engine = RenderEngine()

        # 获取配置并应用配色方案
        config = engine.platform_adapter.get_config(platform)
        if color_scheme:
            scheme_colors = engine.platform_adapter.get_color_scheme(
                platform, template, color_scheme
            )
            if scheme_colors:
                import copy
                config = copy.deepcopy(config)
                config['colors'] = {**config['colors'], **scheme_colors}

        # 只生成HTML，不渲染为图片
        html = engine.template_manager.render_template(
            template_name=template,
            platform=platform,
            title=sample["title"],
            content=sample["content"],
            config=config,
            author=sample.get("author"),
        )

        return {
            "status": "success",
            "html": html,
            "platform": platform,
            "template": template,
        }
    except Exception as e:
        logger.error(f"获取HTML预览失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取HTML预览失败: {str(e)}")


@router.post("/preview", summary="预览模板效果")
async def preview_template(request: PreviewRequest):
    """
    生成模板预览图

    ## 功能说明
    使用示例内容生成预览图，用于查看模板效果和调试配置

    ## 请求参数
    - **template**: 模板名称
    - **platform**: 目标平台
    - **color_scheme**: 配色方案名称（可选）
    - **sample**: 是否使用示例内容（默认 true）
    - **title**: 自定义标题（sample=false时使用）
    - **content**: 自定义内容（sample=false时使用）
    - **author**: 自定义作者（可选）

    ## 返回结果
    返回预览图片的 URL

    ## 缓存机制
    - 如果是sample预览，会缓存图片到 data/images/preview_cache/ 目录
    - 缓存文件名格式：{platform}_{template}_{color_scheme or 'default'}.png
    - 非sample预览（自定义内容）不使用缓存
    """
    try:
        # 确定使用的内容
        if request.sample:
            sample_content = {
                "xiaohongshu": {
                    "title": "禅修的智慧",
                    "content": "禅修的核心智慧在于觉知当下。当我们放下过去的执念和未来的焦虑，专注于当下的呼吸和感受，内心便能得到真正的宁静。",
                    "author": "@佛学行者",
                },
                "douyin": {
                    "title": "短视频创作技巧",
                    "content": "创作优质短视频的三个关键：1. 抓住前3秒黄金时间 2. 保持内容节奏紧凑 3. 引导用户互动",
                    "author": "@创作达人",
                },
            }
            sample = sample_content.get(request.platform, sample_content["xiaohongshu"])
        else:
            # 使用自定义内容
            sample = {
                "title": request.title or "标题",
                "content": request.content or "在这里输入内容...",
                "author": request.author,
            }

        # 如果是sample预览，尝试使用缓存
        if request.sample:
            cache_dir = Path("data/images/preview_cache")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # 生成缓存文件名
            color_scheme_suffix = request.color_scheme or "default"
            cache_filename = f"{request.platform}_{request.template}_{color_scheme_suffix}.png"
            cache_path = cache_dir / cache_filename

            # 检查缓存是否存在
            if cache_path.exists():
                logger.info(f"使用缓存的预览图: {cache_path}")
                relative_path = cache_path.relative_to("data")
                url = f"/static/{relative_path}"

                return {
                    "status": "success",
                    "image_url": url,
                    "platform": request.platform,
                    "template": request.template,
                    "cached": True,
                }

        # 创建渲染引擎
        engine = RenderEngine()

        # 执行渲染（传入 color_scheme）
        output_dir = "data/images/preview" if not request.sample else "data/images/preview_cache"
        result = await engine.render(
            title=sample["title"],
            content=sample["content"],
            platform=request.platform,
            template=request.template,
            color_scheme=request.color_scheme,
            split_long=False,
            output_dir=output_dir,
            author=sample.get("author"),
        )

        # 构建响应
        if result.get("rendered_images"):
            image_path = result["rendered_images"][0]

            # 如果是sample预览，将生成的图片移动到缓存位置
            if request.sample:
                cache_dir = Path("data/images/preview_cache")
                cache_dir.mkdir(parents=True, exist_ok=True)

                color_scheme_suffix = request.color_scheme or "default"
                cache_filename = f"{request.platform}_{request.template}_{color_scheme_suffix}.png"
                cache_path = cache_dir / cache_filename

                # 移动文件到缓存位置
                import shutil
                shutil.move(image_path, str(cache_path))
                image_path = str(cache_path)

            path_obj = Path(image_path)
            relative_path = path_obj.relative_to("data")
            url = f"/static/{relative_path}"

            return {
                "status": "success",
                "image_url": url,
                "platform": request.platform,
                "template": request.template,
                "cached": False,
            }

        raise HTTPException(status_code=500, detail="预览生成失败")

    except Exception as e:
        logger.error(f"预览生成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览生成失败: {str(e)}")


@router.get("/templates/color-schemes", summary="获取模板配色方案")
async def get_color_schemes(platform: Optional[str] = Query(None, description="平台名称")):
    """
    获取所有模板的配色方案配置

    ## 请求参数
    - **platform**: 可选，指定平台名称

    ## 返回结果
    返回每个模板的配色方案列表
    """
    try:
        engine = RenderEngine()

        if platform:
            platforms = [platform]
        else:
            platforms = engine.get_supported_platforms()

        result = {}
        for plat in platforms:
            result[plat] = engine.platform_adapter.get_all_color_schemes(plat)

        return {
            "status": "success",
            "platforms": result
        }
    except Exception as e:
        logger.error(f"获取配色方案失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/font-schemes", summary="获取模板字体方案")
async def get_font_schemes(platform: Optional[str] = Query(None, description="平台名称")):
    """
    获取所有模板的字体方案配置

    ## 请求参数
    - **platform**: 可选，指定平台名称

    ## 返回结果
    返回每个模板的字体方案列表
    """
    try:
        engine = RenderEngine()

        if platform:
            platforms = [platform]
        else:
            platforms = engine.get_supported_platforms()

        result = {}
        for plat in platforms:
            result[plat] = engine.platform_adapter.get_all_font_schemes(plat)

        return {
            "status": "success",
            "platforms": result
        }
    except Exception as e:
        logger.error(f"获取字体方案失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms", summary="获取支持的平台列表")
async def get_platforms():
    """
    获取支持的平台列表

    ## 返回结果
    返回所有支持的平台及其配置信息
    """
    try:
        engine = RenderEngine()
        platforms = engine.get_supported_platforms()

        return {
            "status": "success",
            "platforms": platforms,
            "total": len(platforms),
        }

    except Exception as e:
        logger.error(f"获取平台列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取平台列表失败: {str(e)}")


@router.get("/templates", summary="获取支持的模板列表")
async def get_templates(platform: Optional[str] = Query(None, description="筛选平台")):
    """
    获取支持的模板列表

    ## 请求参数
    - **platform**: 可选，筛选特定平台的模板

    ## 返回结果
    返回可用的模板列表
    """
    try:
        # 扫描模板目录
        templates_dir = Path("app/skills/skills/generation/render/assets/templates")

        templates = {}
        for platform_dir in templates_dir.iterdir():
            if platform_dir.is_dir() and platform_dir.name != "base":
                platform_name = platform_dir.name
                if platform and platform != platform_name:
                    continue

                platform_templates = [
                    f.stem for f in platform_dir.glob("*.html") if f.is_file()
                ]
                templates[platform_name] = platform_templates

        return {
            "status": "success",
            "templates": templates,
        }

    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.post("/batch", summary="批量渲染")
async def render_batch(
    items: List[RenderRequest],
    platform: Optional[str] = Query(None, description="统一指定平台"),
    template: Optional[str] = Query(None, description="统一指定模板"),
):
    """
    批量渲染多个内容

    ## 请求参数
    - **items**: 渲染请求列表
    - **platform**: 可选，统一指定平台（覆盖单个请求中的平台）
    - **template**: 可选，统一指定模板（覆盖单个请求中的模板）

    ## 返回结果
    返回所有渲染结果
    """
    try:
        engine = RenderEngine()

        # 准备批量渲染参数
        batch_items = []
        for item in items:
            batch_items.append(
                {
                    "title": item.title,
                    "content": item.content,
                    "author": item.author,
                }
            )

        # 使用统一的平台和模板（如果指定）
        render_platform = platform or (items[0].platform if items else "xiaohongshu")
        render_template = template or (items[0].template if items else "minimal")

        # 执行批量渲染
        results = await engine.render_batch(
            items=batch_items,
            platform=render_platform,
            template=render_template,
        )

        # 构建响应
        formatted_results = []
        for i, result in enumerate(results):
            if "error" in result:
                formatted_results.append(
                    {
                        "index": i,
                        "status": "error",
                        "error": result["error"],
                    }
                )
            else:
                images = []
                for j, image_path in enumerate(result.get("rendered_images", []), 1):
                    path_obj = Path(image_path)
                    relative_path = path_obj.relative_to("data")
                    url = f"/static/{relative_path}"
                    images.append({"index": j, "path": image_path, "url": url})

                formatted_results.append(
                    {
                        "index": i,
                        "status": "success",
                        "images": images,
                        "total_pages": result.get("total_pages", 0),
                    }
                )

        return {
            "status": "success",
            "results": formatted_results,
            "total_items": len(items),
        }

    except Exception as e:
        logger.error(f"批量渲染失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量渲染失败: {str(e)}")


class GenerateTemplateRequest(BaseModel):
    """AI生成模板请求模型"""
    description: str = Field(..., description="风格描述")
    platform: str = Field(default="xiaohongshu", description="目标平台")
    style: str = Field(default="modern", description="参考风格")


class SaveTemplateRequest(BaseModel):
    """保存模板请求模型"""
    template_html: str = Field(..., description="模板HTML代码")
    template_name: str = Field(..., description="模板名称")
    platform: str = Field(default="xiaohongshu", description="目标平台")


@router.post("/generate-template", summary="AI生成模板")
async def generate_template(request: Request, req: GenerateTemplateRequest):
    """
    使用AI生成自定义模板

    ## 功能说明
    - 接收用户的风格描述
    - 调用LLM生成模板代码
    - 验证生成的模板
    - 返回模板和预览信息

    ## 请求参数
    - **description**: 风格描述（如："粉色渐变背景、大字体标题、优雅杂志风格"）
    - **platform**: 目标平台（xiaohongshu, douyin）
    - **style**: 参考风格（modern, elegant, vibrant）

    ## 返回结果
    ```json
    {
      "template_html": "...",
      "template_name": "custom_a1b2c3d4",
      "preview_url": "/static/...",
      "code_quality": 95
    }
    ```
    """
    try:
        # 创建模板生成器
        generator = TemplateGenerator()

        # 获取LLM服务
        llm_service = create_llm_service_from_env()

        # 构建提示词（使用replace避免format与Jinja2语法冲突）
        prompt_template = generator._load_prompt_template()
        prompt = prompt_template
        prompt = prompt.replace("{description}", req.description)
        prompt = prompt.replace("{platform}", req.platform)
        prompt = prompt.replace("{style}", req.style)

        logger.info(f"提示词长度: {len(prompt)} 字符")

        # 调用LLM
        llm_result = await llm_service.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.8
        )

        logger.info(f"LLM结果类型: {type(llm_result)}, 字段: {llm_result.keys() if isinstance(llm_result, dict) else 'N/A'}")

        if "error" in llm_result:
            error_msg = llm_result.get('error', 'Unknown error')
            logger.error(f"LLM生成失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"LLM生成失败: {error_msg}")

        # 提取生成的文本
        template_html = llm_result.get("generated_text", "").strip()
        logger.info(f"生成的HTML长度: {len(template_html)} 字符")
        logger.info(f"生成的HTML（前200字符）: {template_html[:200]}")

        # 如果生成的文本包含在代码块中，提取出来
        if "```" in template_html:
            lines = template_html.split("\n")
            in_code_block = False
            code_lines = []
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    code_lines.append(line)
            template_html = "\n".join(code_lines).strip()
            logger.info(f"提取代码块后的HTML长度: {len(template_html)} 字符")

        # 检查是否为空
        if not template_html:
            raise HTTPException(status_code=500, detail="LLM返回空内容")

        # 验证模板（捕获所有异常）
        try:
            validation = generator.validate_template(template_html, req.platform)
            logger.info(f"验证结果: valid={validation['valid']}, errors={validation.get('errors', [])}")
        except Exception as e:
            logger.error(f"模板验证异常: {str(e)}", exc_info=True)
            validation = {
                "valid": False,
                "errors": [f"验证异常: {str(e)}"],
                "quality_score": 50
            }

        # 生成模板名称
        import uuid
        template_name = f"custom_{uuid.uuid4().hex[:8]}"

        return {
            "status": "success",
            "template_html": template_html,
            "template_name": template_name,
            "preview_url": f"/static/previews/{req.platform}/{template_name}.png",
            "code_quality": validation.get("quality_score", 70),
            "errors": validation.get("errors", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI生成模板失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI生成模板失败: {str(e)}")


@router.post("/save-template", summary="保存生成的模板")
async def save_template(req: SaveTemplateRequest):
    """
    保存AI生成的模板

    ## 功能说明
    - 接收生成的模板HTML
    - 保存到模板目录
    - 返回保存结果

    ## 请求参数
    - **template_html**: 模板HTML代码
    - **template_name**: 模板名称
    - **platform**: 目标平台

    ## 返回结果
    ```json
    {
      "success": true,
      "template_name": "custom_a1b2c3d4",
      "template_path": "...",
      "message": "模板保存成功"
    }
    ```
    """
    try:
        # 创建模板生成器
        generator = TemplateGenerator()

        # 保存模板
        result = await generator.save_template(
            template_html=req.template_html,
            template_name=req.template_name,
            platform=req.platform
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "status": "success",
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存模板失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存模板失败: {str(e)}")


@router.get("/templates/detail", summary="获取模板详细信息")
async def get_templates_detail(platform: Optional[str] = Query(None, description="筛选平台")):
    """
    获取所有模板的详细信息（包括用户生成的自定义模板）

    ## 请求参数
    - **platform**: 可选，筛选特定平台的模板

    ## 返回结果
    ```json
    {
      "status": "success",
      "templates": {
        "xiaohongshu": [
          {
            "name": "modern",
            "platform": "xiaohongshu",
            "is_custom": false,
            "path": "..."
          }
        ]
      }
    }
    ```
    """
    try:
        # 创建模板生成器
        generator = TemplateGenerator()

        # 获取模板列表
        templates = generator.list_templates(platform=platform)

        return {
            "status": "success",
            "templates": templates
        }

    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.delete("/templates/{platform}/{template_name}", summary="删除模板")
async def delete_template(platform: str, template_name: str):
    """
    删除自定义模板

    ## 请求参数
    - **platform**: 平台名称（xiaohongshu, douyin）
    - **template_name**: 模板名称

    ## 返回结果
    ```json
    {
      "status": "success",
      "message": "模板删除成功"
    }
    ```

    ## 注意事项
    - 只能删除自定义模板（模板名以custom_开头）
    - 预设模板无法删除
    """
    try:
        # 检查是否为自定义模板
        if not template_name.startswith("custom_"):
            raise HTTPException(
                status_code=400,
                detail="只能删除自定义模板"
            )

        # 构建模板路径
        template_path = Path(f"app/skills/skills/generation/render/assets/templates/{platform}/{template_name}.html")

        # 检查模板是否存在
        if not template_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"模板 {template_name} 不存在"
            )

        # 删除模板文件
        template_path.unlink()

        logger.info(f"模板已删除: {platform}/{template_name}")

        return {
            "status": "success",
            "message": "模板删除成功",
            "template_name": template_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模板失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")


@router.post("/clear-cache", summary="清除预览缓存")
async def clear_preview_cache():
    """
    清除所有预览图片缓存

    ## 功能说明
    删除 data/images/preview_cache/ 目录下的所有缓存文件

    ## 返回结果
    ```json
    {
      "status": "success",
      "deleted_count": 10,
      "message": "已清除 10 个缓存文件"
    }
    ```
    """
    try:
        cache_dir = Path("data/images/preview_cache")

        if not cache_dir.exists():
            return {
                "status": "success",
                "deleted_count": 0,
                "message": "缓存目录不存在，无需清除"
            }

        # 统计并删除所有缓存文件
        cache_files = list(cache_dir.glob("*.png"))
        deleted_count = 0

        for cache_file in cache_files:
            try:
                cache_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除缓存文件失败 {cache_file}: {e}")

        logger.info(f"已清除 {deleted_count} 个预览缓存文件")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"已清除 {deleted_count} 个缓存文件"
        }

    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.get("/images/stats", summary="获取图片存储统计")
async def get_image_stats():
    """
    获取图片存储统计信息

    ## 返回结果
    ```json
    {
      "status": "success",
      "stats": {
        "temp": {"count": 10, "size_mb": 2.5},
        "drafts": {"count": 50, "size_mb": 15.0},
        "preview": {"count": 5, "size_mb": 1.0},
        "preview_cache": {"count": 20, "size_mb": 3.0}
      },
      "total_size_mb": 21.5
    }
    ```
    """
    try:
        images_dir = Path("data/images")
        stats = {}
        total_size = 0

        categories = ["temp", "drafts", "preview", "preview_cache"]
        
        for category in categories:
            category_dir = images_dir / category
            if category_dir.exists():
                files = list(category_dir.rglob("*.png"))
                size = sum(f.stat().st_size for f in files if f.is_file())
                stats[category] = {
                    "count": len(files),
                    "size_mb": round(size / 1024 / 1024, 2)
                }
                total_size += size
            else:
                stats[category] = {"count": 0, "size_mb": 0}

        return {
            "status": "success",
            "stats": stats,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }

    except Exception as e:
        logger.error(f"获取图片统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图片统计失败: {str(e)}")


@router.delete("/images/temp", summary="清理临时图片")
async def clear_temp_images():
    """
    清理临时图片目录

    ## 功能说明
    删除 data/images/temp/ 目录下的所有图片文件

    ## 返回结果
    ```json
    {
      "status": "success",
      "deleted_count": 10,
      "freed_mb": 2.5,
      "message": "已清理 10 个临时图片，释放 2.5 MB"
    }
    ```
    """
    try:
        temp_dir = Path("data/images/temp")

        if not temp_dir.exists():
            return {
                "status": "success",
                "deleted_count": 0,
                "freed_mb": 0,
                "message": "临时图片目录不存在，无需清理"
            }

        deleted_count = 0
        freed_size = 0

        for png_file in temp_dir.rglob("*.png"):
            try:
                freed_size += png_file.stat().st_size
                png_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除临时图片失败 {png_file}: {e}")

        logger.info(f"已清理 {deleted_count} 个临时图片，释放 {freed_size / 1024 / 1024:.2f} MB")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "freed_mb": round(freed_size / 1024 / 1024, 2),
            "message": f"已清理 {deleted_count} 个临时图片，释放 {freed_size / 1024 / 1024:.2f} MB"
        }

    except Exception as e:
        logger.error(f"清理临时图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理临时图片失败: {str(e)}")


@router.delete("/images/preview", summary="清理预览图片")
async def clear_preview_images():
    """
    清理预览图片目录

    ## 功能说明
    删除 data/images/preview/ 目录下的所有图片文件

    ## 返回结果
    ```json
    {
      "status": "success",
      "deleted_count": 10,
      "freed_mb": 2.5,
      "message": "已清理 10 个预览图片，释放 2.5 MB"
    }
    ```
    """
    try:
        preview_dir = Path("data/images/preview")

        if not preview_dir.exists():
            return {
                "status": "success",
                "deleted_count": 0,
                "freed_mb": 0,
                "message": "预览图片目录不存在，无需清理"
            }

        deleted_count = 0
        freed_size = 0

        for png_file in preview_dir.rglob("*.png"):
            try:
                freed_size += png_file.stat().st_size
                png_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除预览图片失败 {png_file}: {e}")

        logger.info(f"已清理 {deleted_count} 个预览图片，释放 {freed_size / 1024 / 1024:.2f} MB")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "freed_mb": round(freed_size / 1024 / 1024, 2),
            "message": f"已清理 {deleted_count} 个预览图片，释放 {freed_size / 1024 / 1024:.2f} MB"
        }

    except Exception as e:
        logger.error(f"清理预览图片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理预览图片失败: {str(e)}")
