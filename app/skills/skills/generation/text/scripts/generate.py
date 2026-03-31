"""
文本生成脚本

此脚本本身不包含任何 LLM 提供商实现，
而是通过 LLM 服务统一接口调用大语言模型。
"""

import os
import sys
import json
import argparse
import asyncio
import re
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)


def remove_ai_traces(text: str) -> str:
    """
    移除AI生成的明显痕迹

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return text

    # 移除括号中的AI说明（通常是最后一行）
    lines = text.split('\n')
    filtered_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过这些明显的AI痕迹模式
        ai_trace_patterns = [
            r'（全文遵循.*原则.*',
            r'\(全文遵循.*原则.*\)',
            r'（注意.*：.*',
            r'\(注意.*:.*\)',
            r'（本内容.*AI.*',
            r'\(本内容.*AI.*',
            r'^【.*】$',  # 单独的【标题】占位符
            r'^【标题】$',
            r'^【正文】$',
        ]

        is_ai_trace = False
        for pattern in ai_trace_patterns:
            if re.search(pattern, stripped):
                is_ai_trace = True
                break

        # 如果是最后一行或倒数第二行，且是AI说明，跳过
        if is_ai_trace and i >= len(lines) - 2:
            continue

        # 移除emoji后面单独的说明文字
        if '#' in stripped and '：' in stripped:
            # 可能是 "#标签1 #标签2 （说明）" 的格式
            tag_part = stripped.split('#')[0].rstrip()
            if tag_part:
                filtered_lines.append(tag_part)
                continue

        filtered_lines.append(line)

    # 重新组合文本
    cleaned = '\n'.join(filtered_lines)

    # 清理多余的空行
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned


def parse_generated_text(text: str) -> Dict[str, Any]:
    """
    解析生成的文本，提取标题、标签和正文

    支持的格式：
    - 【标题】：使用【】包裹的标题
    - #标签：使用#开头的标签
    - 剩余部分为正文内容

    Args:
        text: 生成的原始文本

    Returns:
        {
            "title": "标题",
            "content": "正文内容",
            "tags": ["标签1", "标签2"],
            "raw": "原始文本"
        }
    """
    if not text:
        return {
            "title": "",
            "content": "",
            "tags": [],
            "parsed_title": "",
            "parsed_content": "",
            "raw": ""
        }

    title = ""
    content = text.strip()
    tags = []

    # 清理文本：移除占位符行
    lines = content.split('\n')
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过占位符行：【标题】、【正文】、标题：、正文：
        if stripped in ['【标题】', '【正文】', '标题：', '标题:', '正文：', '正文:']:
            continue
        filtered_lines.append(line)
    content = '\n'.join(filtered_lines).strip()

    # 清理开头的"标题："或"正文："占位符
    content = re.sub(r'^(标题|正文)[：:]\s*', '', content)

    # 1. 提取标题（格式：【标题】）
    # 支持标题在开头或单独一行
    lines = content.split('\n')
    first_line = lines[0].strip() if lines else ""

    # 检查第一行是否是标题
    title_match = re.match(r'^【([^】]+)】\s*$', first_line)
    if title_match:
        title = title_match.group(1).strip()
        # 移除标题行，保留剩余内容
        content = '\n'.join(lines[1:]).strip()
    else:
        # 尝试在全文开头查找标题
        title_pattern = r'^【([^】]+)】\s*'
        title_match = re.match(title_pattern, content)
        if title_match:
            title = title_match.group(1).strip()
            content = content[title_match.end():].strip()

    # 2. 提取标签（格式：#标签）
    # 匹配 # 后面的中文、英文、数字等字符，直到遇到空格或结束
    tag_pattern = r'#([^\s#]+)'
    tags_found = re.findall(tag_pattern, content)

    if tags_found:
        tags = [tag.strip() for tag in tags_found if tag.strip()]
        tags = list(dict.fromkeys(tags))

        # 从正文中移除标签行（单独成行的标签）
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            # 检查是否是纯标签行（以#开头且主要是标签）
            if line_stripped.startswith('#'):
                # 计算这一行有多少个#号
                hash_count = line_stripped.count('#')
                # 如果#号数量>=2，说明是多个标签，移除整行
                if hash_count >= 2:
                    continue
            filtered_lines.append(line)

        content = '\n'.join(filtered_lines).strip()

        # 再次清理正文中可能残留的标签
        content = re.sub(tag_pattern, '', content).strip()

    # 3. 清理正文内容
    # 移除多余的空行
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = content.strip()

    # 4. 如果没有提取到标题，尝试从正文中提取第一行作为标题
    if not title and content:
        first_content_line = content.split('\n')[0].strip()
        # 如果第一行较短（<50字）且不为空，可以作为标题
        if len(first_content_line) < 50 and first_content_line:
            title = first_content_line
            # 从正文中移除标题行
            remaining = content.split('\n')[1:]
            content = '\n'.join(remaining).strip()

    # 5. 最后的备用方案：如果仍然没有标题，内容不为空，取内容前30字
    if not title and content:
        title = content[:30].strip()
        if len(content) > 30:
            title += "..."

    return {
        "title": title or "AI生成内容",  # 添加默认值
        "content": content,
        "tags": tags,
        "parsed_title": title,  # 新增：解析出的标题
        "parsed_content": content,  # 新增：解析出的正文
        "raw": text
    }


async def generate_text(
    llm_service,
    prompt_template: str,
    content: Optional[str] = None,
    variables: Optional[dict] = None,
    max_tokens: int = 500,
    temperature: float = 1.0,
    system_message: Optional[str] = None,
    provider: Optional[str] = None
) -> dict:
    """
    使用 LLM 服务生成文本

    此函数不关心具体使用的是哪个 LLM 提供商，
    所有实现细节由 LLM 服务层处理。

    Args:
        llm_service: LLM 服务实例
        prompt_template: Prompt 模板，支持 {variable} 占位符
        content: 内容字符串（会作为 {content} 变量）
        variables: 额外的变量字典
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        system_message: 系统消息
        provider: LLM 提供商（可选，默认使用 Agent 的提供商）

    Returns:
        生成结果字典
    """
    # 添加日志
    import logging
    logger = logging.getLogger(__name__)
    
    # 准备模板变量
    template_vars = variables or {}

    # 如果提供了 content，添加到变量中
    if content:
        template_vars['content'] = content
        
        # 智能映射：如果模板需要topic变量但未提供，使用content作为topic
        if '{topic}' in prompt_template and 'topic' not in template_vars:
            template_vars['topic'] = content
            logger.info("模板需要topic变量，用户未提供，使用content作为topic")

    # 使用 LLM 服务生成文本
    result = await llm_service.generate_from_template(
        template=prompt_template,
        variables=template_vars,
        provider=provider,
        max_tokens=max_tokens,
        temperature=temperature,
        system_message=system_message
    )

    # 解析生成的文本，提取标题和标签
    generated_text = result.get('generated_text', '') or result.get('text', '')
    
    logger.info(f"LLM生成结果: tokens_used={result.get('tokens_used')}, "
               f"generated_text长度={len(generated_text)}, "
               f"max_tokens={max_tokens}")
    
    if generated_text:
        # 先清理AI生成痕迹
        cleaned_text = remove_ai_traces(generated_text)

        # 再解析结构
        parsed = parse_generated_text(cleaned_text)

        # 合并解析结果到返回值
        result.update({
            'generated_text': cleaned_text,
            'original_text': generated_text,
            'parsed_title': parsed.get('title', ''),
            'parsed_content': parsed.get('content', cleaned_text),
            'parsed_tags': parsed.get('tags', []),
        })
        # 始终使用解析后的标题和内容
        if parsed.get('title'):
            result['title'] = parsed['title']
        # 始终使用解析后的内容（不含标签）
        if parsed.get('content'):
            result['content'] = parsed['content']
        if parsed.get('tags'):
            result['tags'] = parsed['tags']

    return result


async def main():
    """主函数"""
    # 延迟导入，避免循环依赖
    from app.core.llm_service import create_llm_service_from_env

    parser = argparse.ArgumentParser(description='文本生成工具')
    parser.add_argument('--prompt', required=True, help='Prompt 模板')
    parser.add_argument('--content', help='输入内容')
    parser.add_argument('--variables', help='额外变量 (JSON 格式)')
    parser.add_argument('--max-tokens', type=int, default=500,
                       help='最大生成 token 数')
    parser.add_argument('--temperature', type=float, default=1.0,
                       help='温度参数（0-2）')
    parser.add_argument('--system-message', help='系统消息')
    parser.add_argument('--provider', help='LLM 提供商（可选）')

    args = parser.parse_args()

    # 创建 LLM 服务
    llm_service = create_llm_service_from_env()

    # 解析额外变量
    variables = {}
    if args.variables:
        try:
            variables = json.loads(args.variables)
        except json.JSONDecodeError:
            print(f"错误: variables 必须是有效的 JSON 格式", file=sys.stderr)
            sys.exit(1)

    # 执行生成
    result = await generate_text(
        llm_service=llm_service,
        prompt_template=args.prompt,
        content=args.content,
        variables=variables,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        system_message=args.system_message,
        provider=args.provider
    )

    # 输出 JSON 结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
