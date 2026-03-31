"""
Skill加载器

遵循Anthropic Agent Skills标准，实现渐进式披露架构
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import re
import json
import subprocess
import logging
import sys


logger = logging.getLogger(__name__)


def extract_content_from_data(input_data: Any, fallback: str = '') -> str:
    """
    从 input_data 中提取内容，支持多种可能的字段名

    Args:
        input_data: 输入数据（可能是dict、str或其他类型）
        fallback: 找不到内容时返回的默认值

    Returns:
        提取出的内容字符串
    """
    if isinstance(input_data, dict):
        # 按优先级尝试多个可能的字段名
        content = (input_data.get('parsed_content') or
                  input_data.get('content') or
                  input_data.get('generated_text') or
                  input_data.get('text') or
                  input_data.get('cleaned_text') or
                  fallback)

        # 如果找到的是列表（如items或topics），取第一个的内容
        if isinstance(content, list) and content:
            first_item = content[0]
            if isinstance(first_item, dict):
                content = first_item.get('content') or first_item.get('text') or first_item.get('topic') or fallback
            else:
                content = str(first_item) if first_item else fallback

        # 如果还是没找到内容，尝试从topics字段提取
        if not content or content == fallback:
            topics = input_data.get('topics')
            if topics and isinstance(topics, list) and topics:
                first_topic = topics[0]
                if isinstance(first_topic, dict):
                    content = first_topic.get('topic') or first_topic.get('content') or first_topic.get('text') or fallback

        return content if isinstance(content, str) else fallback
    elif isinstance(input_data, str):
        return input_data
    else:
        return str(input_data) if input_data else fallback


def extract_title_from_data(input_data: Any, fallback: str = '') -> str:
    """
    从 input_data 中提取标题，支持多种可能的字段名

    Args:
        input_data: 输入数据
        fallback: 找不到标题时返回的默认值

    Returns:
        提取出的标题字符串
    """
    if isinstance(input_data, dict):
        title = (input_data.get('parsed_title') or
                input_data.get('title') or
                input_data.get('generated_title') or
                fallback)

        # 如果找到的是列表（如items），取第一个的标题
        if isinstance(title, list) and title:
            first_item = title[0]
            if isinstance(first_item, dict):
                title = first_item.get('title', fallback)
            else:
                title = str(first_item) if first_item else fallback

        return title if isinstance(title, str) else fallback
    return fallback


def resolve_variable_expression(expression: str, input_data: Any) -> Any:
    """
    解析变量表达式，从 input_data 中提取值
    
    支持的表达式格式：
    - {topics[0].topic} - 数组索引 + 属性访问
    - {topics[0]} - 数组索引
    - {topic} - 简单属性访问
    
    Args:
        expression: 变量表达式（不包含大括号）
        input_data: 输入数据
        
    Returns:
        解析出的值
    """
    if not expression or not input_data:
        logger.warning(f"变量解析失败: expression={expression}, input_data为空")
        return None
    
    try:
        # 匹配数组索引和属性访问
        # 例如：topics[0].topic
        pattern = r'(\w+)(?:\[(\d+)\])?(?:\.(\w+))?'
        match = re.match(pattern, expression)
        
        if not match:
            logger.warning(f"变量表达式格式不匹配: {expression}")
            return None
        
        key = match.group(1)  # topics
        index = match.group(2)  # 0
        attr = match.group(3)  # topic
        
        logger.debug(f"解析变量: key={key}, index={index}, attr={attr}")
        
        # 从 input_data 中获取值
        if isinstance(input_data, dict):
            value = input_data.get(key)
            logger.debug(f"  input_data[{key}] = {type(value)}, 值: {value if not isinstance(value, (list, dict)) else f'<{type(value).__name__}>'}")
        else:
            logger.warning(f"input_data不是dict类型: {type(input_data)}")
            return None
        
        # 处理数组索引
        if index is not None:
            if isinstance(value, list):
                index_num = int(index)
                logger.debug(f"  数组索引: {index_num}, 数组长度: {len(value)}")
                if 0 <= index_num < len(value):
                    value = value[index_num]
                    logger.debug(f"  value[{index_num}] = {type(value)}, 值: {value if not isinstance(value, (list, dict)) else f'<{type(value).__name__}>'}")
                else:
                    logger.warning(f"数组索引越界: {index_num}, 数组长度: {len(value)}")
                    return None
            else:
                logger.warning(f"尝试对非列表类型进行索引访问: {type(value)}")
                return None
        
        # 处理属性访问
        if attr:
            if isinstance(value, dict):
                value = value.get(attr)
                logger.debug(f"  value.{attr} = {value}")
            else:
                logger.warning(f"尝试对非dict类型进行属性访问: {type(value)}")
                return None
        
        return value
        
    except Exception as e:
        logger.error(f"解析变量表达式失败: {expression}, 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def resolve_variables_from_input_data(variables: dict, input_data: Any) -> dict:
    """
    解析所有变量，支持从 input_data 中提取值
    
    Args:
        variables: 变量字典，可能包含表达式
        input_data: 输入数据
        
    Returns:
        解析后的变量字典
    """
    resolved = {}
    
    for key, value in variables.items():
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            # 这是一个表达式，需要解析
            expression = value[1:-1]  # 去掉大括号
            resolved_value = resolve_variable_expression(expression, input_data)
            
            if resolved_value is not None:
                resolved[key] = resolved_value
            else:
                logger.warning(f"无法解析变量表达式: {value}")
                resolved[key] = value  # 保留原始值
        else:
            # 普通值，直接使用
            resolved[key] = value
    
    # 如果解析失败，尝试从topics[0]中提取所有可用字段
    if not resolved and isinstance(input_data, dict) and 'topics' in input_data:
        topics = input_data['topics']
        if isinstance(topics, list) and topics:
            first_topic = topics[0]
            if isinstance(first_topic, dict):
                logger.info(f"topics[0] 可用字段: {list(first_topic.keys())}")
                logger.info(f"topics[0] 内容: {first_topic}")
    
    return resolved


class SkillLoader:
    """
    Skill加载器，遵循Agent Skills标准

    支持渐进式披露架构:
    - Level 1: 元数据 (name + description) - 始终加载
    - Level 2: 指令 (SKILL.md正文) - 触发时加载
    - Level 3: 资源 (scripts, references, assets) - 按需加载
    """

    # 默认脚本文件名映射
    DEFAULT_SCRIPTS = {
        'collection.rss': 'fetch_rss.py',
        'collection.topic_discovery': 'discover.py',
        'processing.clean': 'clean_text.py',
        'processing.format': 'format_text.py',
    }

    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.metadata_cache: Dict[str, Dict] = {}  # Level 1: 元数据缓存
        self.instructions_cache: Dict[str, str] = {}  # Level 2: 指令缓存
        self.skills = []  # 技能列表

    def discover_skills(self):
        """
        发现所有Skill并缓存元数据 (Level 1)

        扫描skills目录，加载所有SKILL.md的元数据部分
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills目录不存在: {self.skills_dir}")
            return

        # 使用递归搜索找到所有SKILL.md文件
        for skill_path in self.skills_dir.rglob('SKILL.md'):
            try:
                metadata = self._parse_frontmatter(skill_path)
                skill_name = metadata.get('name')
                if skill_name:
                    self.metadata_cache[skill_name] = {
                        'path': skill_path.parent,
                        'metadata': metadata
                    }
                    logger.debug(f"发现Skill: {skill_name}")
            except Exception as e:
                logger.error(f"加载Skill元数据失败 {skill_path}: {str(e)}")

        logger.info(f"发现 {len(self.metadata_cache)} 个Skill")

    def get_skill_metadata(self, skill_name: str) -> Optional[Dict]:
        """
        获取Skill元数据 (Level 1)

        Args:
            skill_name: Skill名称

        Returns:
            Skill元数据字典
        """
        return self.metadata_cache.get(skill_name, {}).get('metadata')

    def get_all_metadata(self) -> Dict[str, Dict]:
        """获取所有Skill的元数据"""
        return {
            name: data['metadata']
            for name, data in self.metadata_cache.items()
        }

    def get_skill_instructions(self, skill_name: str) -> Optional[str]:
        """
        获取Skill完整指令 (Level 2)

        Args:
            skill_name: Skill名称

        Returns:
            SKILL.md正文内容
        """
        if skill_name not in self.metadata_cache:
            logger.warning(f"Skill不存在: {skill_name}")
            return None

        # 检查缓存
        if skill_name in self.instructions_cache:
            return self.instructions_cache[skill_name]

        # 读取SKILL.md
        skill_path = self.metadata_cache[skill_name]['path']
        skill_md = skill_path / 'SKILL.md'

        if not skill_md.exists():
            logger.error(f"SKILL.md不存在: {skill_md}")
            return None

        try:
            content = self._read_md_content(skill_md)
            self.instructions_cache[skill_name] = content
            return content
        except Exception as e:
            logger.error(f"读取Skill指令失败 {skill_name}: {str(e)}")
            return None

    async def execute_skill_script(
        self,
        skill_name: str,
        script_name: str,
        **kwargs
    ) -> Optional[str]:
        """
        执行Skill脚本 (Level 3)

        Args:
            skill_name: Skill名称
            script_name: 脚本文件名
            **kwargs: 传递给脚本的参数

        Returns:
            脚本执行结果
        """
        if skill_name not in self.metadata_cache:
            logger.warning(f"Skill不存在: {skill_name}")
            return None

        skill_path = self.metadata_cache[skill_name]['path']
        script_path = skill_path / 'scripts' / script_name

        if not script_path.exists():
            logger.error(f"脚本不存在: {script_path}")
            return None

        try:
            # 构建命令行参数
            cmd = ['python', str(script_path)]
            for key, value in kwargs.items():
                # 将 snake_case 转换为 kebab-case (max_items -> --max-items)
                arg_name = key.replace('_', '-')
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"--{arg_name}")
                else:
                    cmd.extend([f"--{arg_name}", str(value)])

            # 执行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                logger.error(f"脚本执行失败: {result.stderr}")
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"脚本执行超时: {script_name}")
            return None
        except Exception as e:
            logger.error(f"执行脚本失败 {skill_name}.{script_name}: {str(e)}")
            return None

    async def read_reference(self, skill_name: str, ref_name: str) -> Optional[str]:
        """
        读取参考文档 (Level 3)

        Args:
            skill_name: Skill名称
            ref_name: 参考文档名称

        Returns:
            参考文档内容
        """
        if skill_name not in self.metadata_cache:
            return None

        skill_path = self.metadata_cache[skill_name]['path']
        ref_path = skill_path / 'references' / ref_name

        if not ref_path.exists():
            logger.warning(f"参考文档不存在: {ref_path}")
            return None

        try:
            return ref_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"读取参考文档失败: {str(e)}")
            return None

    def list_skill_names(self) -> List[str]:
        """列出所有可用的Skill名称"""
        return list(self.metadata_cache.keys())

    def _parse_frontmatter(self, md_path: Path) -> Dict:
        """
        解析SKILL.md的YAML frontmatter

        Args:
            md_path: SKILL.md文件路径

        Returns:
            元数据字典
        """
        content = md_path.read_text(encoding='utf-8')

        # 匹配 YAML frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                metadata = yaml.safe_load(match.group(1))
                return metadata or {}
            except yaml.YAMLError as e:
                logger.error(f"解析YAML frontmatter失败: {str(e)}")
                return {}

        return {}

    def _read_md_content(self, md_path: Path) -> str:
        """
        读取Markdown文件内容（去除frontmatter）

        Args:
            md_path: Markdown文件路径

        Returns:
            Markdown正文内容
        """
        content = md_path.read_text(encoding='utf-8')

        # 移除YAML frontmatter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

        return content.strip()


class SkillRegistry:
    """
    Skill注册表

    提供统一的Skill执行接口
    """

    def __init__(self, skills_dir: str):
        self.loader = SkillLoader(skills_dir)
        self._initialized = False

    async def initialize(self):
        """初始化，发现所有Skill"""
        if not self._initialized:
            self.loader.discover_skills()
            self._initialized = True

    async def execute_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict,
        llm_service=None,
        llm_provider: str = None
    ) -> Any:
        """
        执行Skill

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置
            llm_service: LLM服务实例（可选，用于需要LLM的Skill）
            llm_provider: LLM提供商（可选）

        Returns:
            Skill执行结果
        """
        # 判断 Skill 类型（在获取指令之前判断，因为某些skill不需要指令文本）
        # 只处理真正的LLM生成类skill
        is_generation = (skill_name == 'generation.text' or
                        skill_name == 'generation.render' or
                        skill_name == 'generation.template_generator')
        is_review = skill_name.startswith('review.')
        is_publishing = skill_name.startswith('publishing.')
        is_conditional = skill_name.startswith('conditional.')
        # Python类实现的skill（有__init__.py文件）
        is_python_class = skill_name in ['processing.analyze_topic', 'collection.topic_discovery']

        if is_generation and llm_service:
            # 对于需要 LLM 的生成类 Skill，使用直接调用方式
            return await self._execute_llm_skill(
                skill_name,
                input_data,
                config,
                llm_service,
                llm_provider
            )
        elif is_python_class:
            # 处理Python类实现的Skill
            return await self._execute_python_class_skill(
                skill_name,
                input_data,
                config,
                llm_service,
                llm_provider
            )
        elif is_review:
            # 处理审核相关技能（不需要LLM）
            return await self._execute_review_skill(
                skill_name,
                input_data,
                config,
                llm_service,
                llm_provider
            )
        elif is_publishing:
            # 处理发布相关技能
            return await self._execute_publishing_skill(
                skill_name,
                input_data,
                config
            )
        elif is_conditional:
            # 处理条件判断技能
            return await self._execute_conditional_skill(
                skill_name,
                input_data,
                config
            )

        # 对于其他 Skill，需要指令文本
        instructions = self.loader.get_skill_instructions(skill_name)
        if not instructions:
            logger.error(f"Skill指令不存在: {skill_name}")
            return input_data

        # 对于其他 Skill，使用脚本执行方式
        script_name = config.get('script')
        if not script_name and skill_name in self.loader.DEFAULT_SCRIPTS:
            # 使用默认脚本文件名
            script_name = self.loader.DEFAULT_SCRIPTS[skill_name]
            logger.info(f"使用默认脚本: {script_name}")
        
        if script_name:
            # 过滤掉内部配置参数，只传递脚本需要的参数
            internal_params = {'script', 'variables', 'agent_id', 'account_id', 'condition',
                             'true_action', 'false_action', 'skip_on_failure',
                             'metadata', 'platform', 'input', 'output_key',
                             'llm_provider', 'model', 'prompt_template', 'temperature', 'max_tokens'}
            script_config = {k: v for k, v in config.items() if k not in internal_params}

            # 将 input_data 传递给脚本（仅在有意义的情况下）
            # 对于 RSS 采集返回的列表，取第一条内容
            script_input = None
            if input_data:
                if isinstance(input_data, dict):
                    # RSS 采集返回 {items: [...], total: N}
                    if 'items' in input_data and input_data['items']:
                        # 取第一篇文章的内容
                        script_input = input_data['items'][0].get('content', '')
                    elif 'content' in input_data:
                        script_input = input_data['content']
                    elif 'text' in input_data:
                        script_input = input_data['text']
                elif isinstance(input_data, str) and input_data.strip():
                    script_input = input_data

                # 只有当有实际内容时才添加 input 参数
                if script_input and 'input' not in config:
                    script_config['input'] = script_input

            result = await self.loader.execute_skill_script(
                skill_name,
                script_name,
                **script_config
            )

            # 检查脚本执行结果
            if result is None:
                # 脚本执行失败，抛出异常中断后续skill
                raise RuntimeError(f"Skill {skill_name} 脚本执行失败")

            try:
                parsed_result = json.loads(result)

                # 检查返回的数据是否有效
                if isinstance(parsed_result, dict):
                    # 检查是否有错误字段
                    if 'error' in parsed_result:
                        raise RuntimeError(f"Skill {skill_name} 执行失败: {parsed_result['error']}")

                    # 只对采集类skill检查total字段
                    if skill_name.startswith('collection.'):
                        if parsed_result.get('total', 0) == 0:
                            raise RuntimeError(f"Skill {skill_name} 未采集到任何数据")

                    # 记录非采集类skill的关键返回字段
                    if not skill_name.startswith('collection.'):
                        logger.info(f"Skill {skill_name} 返回: {list(parsed_result.keys())}, text/content长度: {len(parsed_result.get('text') or parsed_result.get('content') or '')}")

                        # 合并输入数据和脚本结果
                        parsed_result = {**input_data, **parsed_result} if isinstance(input_data, dict) else parsed_result

                return parsed_result
            except json.JSONDecodeError:
                return result
        else:
            # 没有脚本配置，抛出异常
            raise RuntimeError(f"Skill {skill_name} 缺少脚本配置")

    async def _execute_python_class_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict,
        llm_service=None,
        llm_provider: str = None
    ) -> Any:
        """
        执行Python类实现的Skill

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置
            llm_service: LLM服务实例
            llm_provider: LLM提供商

        Returns:
            Skill执行结果
        """
        try:
            # 获取 skill 路径
            skill_info = self.loader.metadata_cache.get(skill_name, {})
            if not skill_info:
                logger.error(f"Skill 路径不存在: {skill_name}")
                return input_data

            skill_path = skill_info.get('path')
            if not skill_path:
                logger.error(f"Skill path 不存在: {skill_name}")
                return input_data

            # 导入 skill 模块
            script_path = skill_path / 'scripts'

            # 根据skill名称导入对应的类
            if skill_name == 'processing.analyze_topic':
                sys.path.insert(0, str(script_path))
                from analyze import TopicAnalysisSkill
                skill_class = TopicAnalysisSkill
            elif skill_name == 'collection.topic_discovery':
                sys.path.insert(0, str(script_path))
                from discover import TopicDiscoverySkill
                skill_class = TopicDiscoverySkill
            else:
                logger.error(f"未知的Python类 Skill: {skill_name}")
                return input_data

            # 创建skill实例并执行
            skill = skill_class()
            
            # 设置LLM服务（如果skill需要）
            if hasattr(skill, 'set_llm_service'):
                skill.set_llm_service(llm_service)
            
            result = await skill.execute(config)
            return result
        except Exception as e:
            logger.error(f"执行Python类 Skill 失败 {skill_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"执行Python类 Skill 失败: {str(e)}"
            }

    async def _execute_llm_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict,
        llm_service,
        llm_provider: str = None
    ) -> Any:
        """
        执行需要 LLM 服务的 Skill

        这些 Skill 通过直接导入模块执行，而不是通过 subprocess，
        以便可以直接传递 LLM 服务实例。

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置
            llm_service: LLM服务实例
            llm_provider: LLM提供商

        Returns:
            Skill执行结果
        """
        try:
            # 获取 skill 路径
            skill_info = self.loader.metadata_cache.get(skill_name, {})
            if not skill_info:
                logger.error(f"Skill 路径不存在: {skill_name}")
                return input_data

            skill_path = skill_info.get('path')
            if not skill_path:
                logger.error(f"Skill path 不存在: {skill_name}")
                return input_data

            # 导入 skill 模块
            script_path = skill_path / 'scripts'

            if skill_name == 'generation.text':
                # 导入文本生成模块
                sys.path.insert(0, str(script_path))
                from generate import generate_text
                from app.models import PromptTemplate

                # 准备参数
                prompt_template = config.get('prompt_template', '')
                variables = config.get('variables', {})
                max_tokens = config.get('max_tokens', 500)
                temperature = config.get('temperature', 1.0)
                system_message = config.get('system_message')

                # 如果 prompt_template 是模板ID，从数据库获取模板内容
                if prompt_template:
                    # 检查是否是模板ID（在数据库中存在）
                    # 如果prompt_template包含换行符或长度超过100，当作直接提示词
                    if '\n' in prompt_template or len(prompt_template) > 100:
                        logger.info(f"使用直接提示词（非模板ID），长度: {len(prompt_template)}")
                    else:
                        template = await PromptTemplate.get_or_none(id=prompt_template)
                        if template:
                            logger.info(f"使用提示词模板: {template.name} (ID: {prompt_template})")
                            prompt_template = template.template_content
                            
                            # 如果有示例输出，添加到提示词后面
                            if template.example_output:
                                prompt_template = f"{prompt_template}\n\n示例输出：\n{template.example_output}"
                        else:
                            # 模板不存在，抛出异常
                            raise ValueError(f"提示词模板 {prompt_template} 不存在，请检查配置")
                else:
                    logger.warning(f"未配置 prompt_template")

                # 解析变量：处理 template 类型的变量
                resolved_variables = {}
                
                # 首先解析从 input_data 中提取的变量表达式（如 {topics[0].topic}）
                logger.info(f"开始解析变量，input_data类型: {type(input_data)}")
                if isinstance(input_data, dict):
                    logger.info(f"input_data键: {list(input_data.keys())}")
                    if 'topics' in input_data:
                        logger.info(f"topics类型: {type(input_data['topics'])}, 长度: {len(input_data['topics']) if isinstance(input_data['topics'], list) else 'N/A'}")
                
                variables_from_input = resolve_variables_from_input_data(variables, input_data)
                
                # 然后处理 template 类型的变量
                for key, value in variables.items():
                    if key in variables_from_input:
                        # 已经从 input_data 中解析出值
                        resolved_variables[key] = variables_from_input[key]
                    elif isinstance(value, dict) and value.get('type') == 'template':
                        # 从数据库获取模板内容
                        template_id = value.get('value')
                        template = await PromptTemplate.get_or_none(id=template_id)
                        if template:
                            resolved_variables[key] = template.template_content
                        else:
                            logger.warning(f"模板 {template_id} 不存在，使用空字符串")
                            resolved_variables[key] = ''
                    else:
                        # 普通值，直接使用
                        resolved_variables[key] = value

                # 提取 input_data 中的 content
                content = extract_content_from_data(input_data)

                # 检查是否有有效输入（content或variables）
                has_content = bool(content)
                has_variables = bool(resolved_variables)
                has_prompt = bool(prompt_template)

                # 如果既没有内容也没有变量，才返回错误
                if not has_content and not has_variables and not has_prompt:
                    logger.warning(f"Skill {skill_name}: input_data中没有找到可用内容, input_data类型: {type(input_data)}, 键: {input_data.keys() if isinstance(input_data, dict) else 'N/A'}")
                    return {
                        "title": "",
                        "content": "",
                        "tags": [],
                        "parsed_title": "",
                        "parsed_content": "",
                        "error": "没有找到输入内容"
                    }

                # 如果有variables但没有content，这是正常的（如厚黑学agent）
                if has_variables and not has_content:
                    logger.info(f"Skill {skill_name}: 使用variables生成内容，无前置内容")

                # 调用生成函数
                result = await generate_text(
                    llm_service=llm_service,
                    prompt_template=prompt_template,
                    content=content,
                    variables=resolved_variables,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_message=system_message,
                    provider=llm_provider
                )

                logger.info(f"Skill {skill_name} 返回: {list(result.keys()) if isinstance(result, dict) else type(result)}, "
                           f"标题: {result.get('title', 'N/A')[:30] if result.get('title') else 'N/A'}, "
                           f"内容长度: {len(result.get('parsed_content') or result.get('content') or '')}, "
                           f"原始文本长度: {len(result.get('original_text') or '')}, "
                           f"生成文本长度: {len(result.get('generated_text') or '')}, "
                           f"标签: {result.get('tags') or result.get('parsed_tags')}")

                # 合并输入数据和生成结果
                if isinstance(input_data, dict):
                    result = {**input_data, **result}

                return result

            if skill_name == 'generation.render':
                # 导入渲染模块
                import importlib

                # 构建完整的模块路径
                module_path = f"app.skills.skills.{skill_name.replace('.', '.')}.scripts"
                scripts_module = importlib.import_module(module_path)
                RenderEngine = scripts_module.RenderEngine

                # 准备参数 - 从 input_data 和 config 中提取
                title = config.get('title', '')
                content = config.get('content', '')
                tags = config.get('tags', [])
                platform = config.get('platform', 'xiaohongshu')
                template = config.get('template', 'minimal')
                max_length = config.get('max_length')
                split_long = config.get('split_long', True)
                # 正式草稿图片存到 drafts 目录
                output_dir = config.get('output_dir', 'data/images/drafts')

                # 从 input_data 提取内容（如果未在 config 中指定）
                if isinstance(input_data, dict):
                    # 优先使用配置中的值，如果没有则从 input_data 提取
                    # 注意：优先使用parsed_title，因为它可能比title更准确
                    if not title:
                        title = (input_data.get('parsed_title', '') or
                                input_data.get('title', '') or
                                input_data.get('generated_title', ''))
                    if not content:
                        content = (input_data.get('parsed_content', '') or
                                  input_data.get('content', '') or
                                  input_data.get('generated_text', '') or
                                  input_data.get('text', ''))
                    if not tags:
                        tags = (input_data.get('parsed_tags', []) or
                               input_data.get('tags', []) or
                               input_data.get('topics', []) or
                               [])

                # 确保 content 是字符串
                if not isinstance(content, str):
                    content = str(content) if content else ''

                logger.info(f"渲染参数: 标题={title[:30] if title else 'N/A'}, 内容长度={len(content)}, max_length={max_length}")

                # 调用渲染引擎
                engine = RenderEngine()
                result = await engine.render(
                    title=title,
                    content=content,
                    platform=platform,
                    template=template,
                    max_length=max_length,
                    split_long=split_long,
                    output_dir=output_dir
                )

                # 将标题和标签添加到结果中
                result['title'] = title
                result['content'] = content
                result['tags'] = tags if isinstance(tags, list) else []

                logger.info(f"渲染成功，生成 {result.get('total_pages')} 张图片，标题: {title}")

                # 合并输入数据和渲染结果
                if isinstance(input_data, dict):
                    result = {**input_data, **result}

                return result

            # 其他 LLM-dependent skill 可以在这里添加
            logger.warning(f"未知的 LLM Skill: {skill_name}")
            return input_data

        except ImportError as e:
            logger.error(f"无法导入 Skill 模块 {skill_name}: {str(e)}")
            return {
                'success': False,
                'error': f"无法导入 Skill 模块: {str(e)}"
            }
        except Exception as e:
            logger.error(f"执行 LLM Skill {skill_name} 失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"执行 LLM Skill 失败: {str(e)}"
            }

    async def _execute_publishing_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict
    ) -> Any:
        """
        执行发布相关 Skill

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置

        Returns:
            Skill执行结果
        """
        try:
            if skill_name == 'publishing.draft':
                # 导入保存草稿模块
                from app.skills.skills.publishing.draft.scripts.save_draft import save_draft

                # 提取数据
                if isinstance(input_data, dict):
                    # 获取标题（优先级：parsed_title > title > config）
                    # 注意：要优先使用parsed_title，因为它可能比title更准确
                    title = (input_data.get('parsed_title', '') or
                            input_data.get('title', '') or
                            config.get('title', 'AI生成内容'))

                    # 获取内容
                    generated_text = input_data.get('generated_text', '')
                    content = (input_data.get('parsed_content', '') or
                              input_data.get('content', '') or
                              generated_text)

                    # logger.info(f"保存草稿: 标题={title[:30] if title else 'N/A'}, "
                    #            f"内容长度={len(content)}, "
                    #            f"generated_text长度={len(generated_text)}, "
                    #            f"parsed_content长度={len(input_data.get('parsed_content', ''))}")

                    # 提取图片路径
                    rendered_images = input_data.get('rendered_images') or input_data.get('images') or []
                    images_str = ','.join(rendered_images) if rendered_images else None

                    # 提取标签
                    tags = input_data.get('tags', []) or input_data.get('parsed_tags', []) or []
                    # logger.info(f"保存草稿时提取的标签: {tags}, tags字段={input_data.get('tags')}, parsed_tags字段={input_data.get('parsed_tags')}")
                else:
                    title = config.get('title', 'AI生成内容')
                    content = str(input_data)
                    images_str = None
                    tags = []

                # 获取配置
                agent_id = config.get('agent_id', 'unknown')
                platform = config.get('platform', 'xiaohongshu')

                # 构建元数据（包含标签和审核结果）
                metadata = config.get('metadata', {}) or {}

                # 保存标签
                if tags:
                    metadata['tags'] = tags
                if input_data.get('total_pages'):
                    metadata['total_pages'] = input_data.get('total_pages')
                if input_data.get('template'):
                    metadata['template'] = input_data.get('template')

                # 保存审核结果
                if input_data.get('is_safe') is not None:
                    metadata['is_safe'] = input_data.get('is_safe')
                if input_data.get('risk_level'):
                    metadata['risk_level'] = input_data.get('risk_level')
                if input_data.get('detected_items'):
                    metadata['detected_items'] = input_data.get('detected_items')
                if input_data.get('overall_score') is not None:
                    metadata['overall_score'] = input_data.get('overall_score')
                if input_data.get('is_qualified') is not None:
                    metadata['is_qualified'] = input_data.get('is_qualified')
                if input_data.get('scores'):
                    metadata['quality_scores'] = input_data.get('scores')
                if input_data.get('method'):
                    metadata['review_method'] = input_data.get('method')

                # 调用保存草稿
                result = await save_draft(
                    agent_id=agent_id,
                    platform=platform,
                    content=content,
                    title=title,
                    images=images_str,
                    tags=tags,
                    metadata=json.dumps(metadata, ensure_ascii=False) if metadata else None
                )

                logger.info(f"草稿保存成功: {result.get('draft_id')}, 标题: {title}, 图片: {images_str}, 标签: {tags}")

                # 创建审核记录
                if result.get('draft_id'):
                    try:
                        from app.models import Review

                        # 检查是否有审核结果（Agent是否配置了审核skill）
                        has_review_result = (
                            input_data.get('is_safe') is not None or
                            input_data.get('overall_score') is not None or
                            input_data.get('risk_level') is not None
                        )

                        if has_review_result:
                            # 有审核结果，提取审核数据
                            is_safe = input_data.get('is_safe', True)
                            risk_level = input_data.get('risk_level', 'low')
                            detected_items = input_data.get('detected_items', {})
                            overall_score = input_data.get('overall_score', 0) or input_data.get('quality_score', 0)
                            is_qualified = input_data.get('is_qualified', True)

                            # 提取分数 - 支持两种格式
                            dimensions = input_data.get('dimensions', {})
                            scores = input_data.get('scores', {})
                            
                            if dimensions:
                                readability_score = dimensions.get('readability', {}).get('score', 0)
                                completeness_score = dimensions.get('completeness', {}).get('score', 0)
                                attractiveness_score = dimensions.get('attractiveness', {}).get('score', 0)
                            elif scores:
                                readability_score = scores.get('readability', 0)
                                completeness_score = scores.get('completeness', 0)
                                attractiveness_score = scores.get('attractiveness', 0)
                            else:
                                readability_score = 0
                                completeness_score = 0
                                attractiveness_score = 0

                            # 提取敏感词
                            sensitive_words = []
                            if detected_items:
                                for category, words in detected_items.items():
                                    if isinstance(words, list):
                                        sensitive_words.extend(words)

                            # 确定审核状态
                            if not is_safe:
                                review_status = 'rejected'
                            elif overall_score == 0 and not dimensions:
                                # 没有质量评分，需要人工审核
                                review_status = 'pending'
                                logger.warning(f"Agent {agent_id} 未配置质量审核skill，需人工审核")
                            elif not is_qualified:
                                review_status = 'pending'
                            else:
                                review_status = 'approved'

                            # 创建审核记录
                            await Review.create(
                                draft_id=result.get('draft_id'),
                                agent_id=agent_id,
                                status=review_status,
                                sensitive_word_count=len(sensitive_words),
                                sensitive_words=sensitive_words,
                                risk_level=risk_level,
                                quality_score=overall_score,
                                readability_score=readability_score,
                                completeness_score=completeness_score,
                                attractiveness_score=attractiveness_score,
                                reviewer='system',
                                reviewed_at=datetime.now() if review_status != 'pending' else None
                            )
                            logger.info(f"审核记录创建成功: draft_id={result.get('draft_id')}, status={review_status}, score={overall_score}")
                        else:
                            # 没有审核结果，创建待人工审核记录
                            await Review.create(
                                draft_id=result.get('draft_id'),
                                agent_id=agent_id,
                                status='pending',
                                sensitive_word_count=0,
                                sensitive_words=[],
                                risk_level='unknown',
                                quality_score=0,
                                readability_score=0,
                                completeness_score=0,
                                attractiveness_score=0,
                                reviewer=None,
                                review_notes='Agent未配置审核skill，需人工审核'
                            )
                            logger.warning(f"Agent {agent_id} 未配置审核skill，创建待人工审核记录: draft_id={result.get('draft_id')}")
                            
                            # 更新草稿状态为待审核
                            from app.models import Draft
                            draft = await Draft.get_or_none(id=result.get('draft_id'))
                            if draft:
                                draft.status = 'pending_review'
                                await draft.save()
                    except Exception as e:
                        logger.error(f"创建审核记录失败: {str(e)}", exc_info=True)

                # 合并输入数据和保存结果
                if isinstance(input_data, dict):
                    result = {**input_data, **result}

                return result

            if skill_name == 'publishing.publish':
                # 导入发布模块
                from app.skills.skills.publishing.publish.scripts.publish import publish_content

                # 获取skill路径
                skill_info = self.loader.metadata_cache.get(skill_name, {})
                skill_path = skill_info.get('path')
                script_path = skill_path / 'scripts'

                # 导入模块
                import sys
                sys.path.insert(0, str(script_path))
                from publish import publish_content

                # 提取数据 - 支持多种可能的字段名
                if isinstance(input_data, dict):
                    # 获取标题（优先级：config > input_data 多种可能字段）
                    title = (config.get('title') or
                            input_data.get('title', '') or
                            input_data.get('parsed_title', '') or
                            input_data.get('generated_title', ''))

                    # 获取内容
                    content = (config.get('content') or
                              input_data.get('content', '') or
                              input_data.get('parsed_content', '') or
                              input_data.get('generated_text', '') or
                              input_data.get('text', ''))

                    # 获取图片
                    images = (config.get('images') or
                             input_data.get('rendered_images') or
                             input_data.get('images', []))

                    # 获取标签/话题
                    topics = (config.get('topics') or
                             input_data.get('tags') or
                             input_data.get('parsed_tags') or
                             input_data.get('topics', []))
                    
                    # logger.info(f"发布时获取的标签: {topics}, 来源字段: tags={input_data.get('tags')}, parsed_tags={input_data.get('parsed_tags')}")
                else:
                    title = config.get('title', '')
                    content = str(input_data)
                    images = config.get('images', [])
                    topics = config.get('topics', [])

                # 获取配置
                platform = config.get('platform', 'xiaohongshu')
                account_id = config.get('account_id')
                cookie = config.get('cookie')
                location = config.get('location')
                headless = config.get('headless', True)

                # 提取 draft_id（如果存在）
                draft_id = input_data.get('draft_id')
                
                # 如果有 draft_id，从草稿获取标签
                if draft_id and not topics:
                    from app.models import Draft
                    draft = await Draft.get_or_none(id=draft_id)
                    if draft and draft.tags:
                        topics = draft.tags
                        logger.info(f"从草稿 {draft_id} 获取标签: {topics}")

                # 验证必要参数
                if not title:
                    return {'success': False, 'error': '缺少标题', 'code': 'missing_title'}
                if not content:
                    return {'success': False, 'error': '缺少内容', 'code': 'missing_content'}
                if not images:
                    return {'success': False, 'error': '缺少图片', 'code': 'missing_images'}

                # 检查审核状态（优先检查）
                if draft_id:
                    from app.models import Review
                    review = await Review.get_or_none(draft_id=draft_id)
                    if not review:
                        logger.warning(f"草稿 {draft_id} 没有审核记录，需先审核")
                        return {
                            'success': False,
                            'error': '内容未审核，请先在审核页面进行审核',
                            'code': 'review_required',
                            'draft_id': draft_id
                        }
                    if review.status == 'pending':
                        logger.warning(f"草稿 {draft_id} 待审核中")
                        return {
                            'success': False,
                            'error': '内容待审核中，请等待审核通过后再发布',
                            'code': 'review_pending',
                            'draft_id': draft_id
                        }
                    if review.status == 'rejected':
                        logger.warning(f"草稿 {draft_id} 已被拒绝")
                        return {
                            'success': False,
                            'error': '内容已被拒绝，无法发布',
                            'code': 'review_rejected',
                            'draft_id': draft_id
                        }
                    logger.info(f"草稿 {draft_id} 审核已通过，允许发布")

                logger.info(f"发布参数: account_id={account_id}, cookie存在={bool(cookie)}, platform={platform}")

                # 获取账户cookie
                if not cookie and account_id:
                    from app.models import Account
                    account = await Account.get_or_none(id=account_id)
                    if account:
                        cookie = account.cookie
                        if cookie:
                            logger.info(f"从账户 {account_id} 获取cookie成功")
                        else:
                            logger.warning(f"账户 {account_id} 存在但未配置cookie，请在账户管理中添加cookie")
                    else:
                        logger.warning(f"账户 {account_id} 不存在，请检查Agent绑定的账户ID")
                elif not account_id:
                    logger.warning("未配置 account_id，请在Agent配置中绑定账户")

                # 如果没有cookie，返回错误
                if not cookie:
                    return {
                        'success': False,
                        'error': '未配置发布账户或cookie，请在Agent配置中设置account_id，或在账户管理中配置cookie',
                        'code': 'no_account_cookie'
                    }
                else:
                    logger.warning("没有 draft_id，跳过审核检查（可能是直接发布模式）")

                # 调用发布函数
                result = await publish_content(
                    title=title,
                    content=content,
                    images=images,
                    platform=platform,
                    account_id=account_id,
                    cookie=cookie,
                    topics=topics if topics else None,
                    location=location,
                    headless=headless,
                    draft_id=draft_id  # 传递 draft_id 以便更新状态
                )

                if result.get('success'):
                    logger.info(f"发布成功: {title}, 标签: {topics}")
                else:
                    logger.error(f"发布失败: {result.get('error')}")

                return result

            logger.warning(f"未知的 Publishing Skill: {skill_name}")
            return input_data

        except Exception as e:
            logger.error(f"执行 Publishing Skill {skill_name} 失败: {str(e)}", exc_info=True)
            return input_data

    async def _execute_review_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict,
        llm_service=None,
        llm_provider: str = None
    ) -> Any:
        """
        执行审核相关 Skill

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置
            llm_service: LLM服务实例（用于AI审核模式）
            llm_provider: LLM提供商

        Returns:
            Skill执行结果
        """
        try:
            if skill_name == 'review.sensitive':
                # 导入敏感词检测模块
                from app.skills.skills.review.sensitive.scripts.check_sensitive import SensitiveWordChecker
                from app.models import ReviewSettings

                # 提取内容
                content = extract_content_from_data(input_data)

                logger.info(f"review.sensitive: 提取到的content长度={len(content)}")

                if not content:
                    return {'is_safe': True, 'risk_level': 'low', 'detected_items': {}}

                # 获取全局审核设置
                settings = await ReviewSettings.get_settings()
                
                # 如果全局设置禁用了敏感词检测，直接返回安全
                if not settings.sensitive_word_enabled:
                    logger.info("敏感词检测已禁用，跳过检测")
                    return {'is_safe': True, 'risk_level': 'low', 'detected_items': {}}

                # 使用全局设置，但 Agent 配置可以覆盖
                strictness = config.get('strictness', 'medium')
                categories = config.get('categories') or settings.sensitive_categories
                custom_words = config.get('custom_words') or settings.custom_words

                # 创建检测器
                checker = SensitiveWordChecker(strictness=strictness)

                # 执行检测
                result = checker.full_check(
                    content=content,
                    categories=categories.split(',') if isinstance(categories, str) else categories,
                    custom_words=custom_words
                )

                logger.info(f"敏感词检测完成，风险等级: {result.get('risk_level')}, 安全: {result.get('is_safe')}")

                # 合并输入数据和检测结果
                if isinstance(input_data, dict):
                    result = {**input_data, **result}

                return result

            if skill_name == 'review.quality':
                from app.models import ReviewSettings
                
                # 获取全局审核设置
                settings = await ReviewSettings.get_settings()
                
                # 如果全局设置禁用了质量评分，直接返回合格
                if not settings.quality_score_enabled:
                    logger.info("质量评分已禁用，跳过评分")
                    result = {'overall_score': 100, 'is_qualified': True, 'method': 'disabled'}
                    if isinstance(input_data, dict):
                        result = {**input_data, **result}
                    return result
                
                # 检查是否使用 AI 审核模式
                use_ai = config.get('use_ai', False)

                if use_ai and llm_service:
                    # AI 审核模式
                    from app.skills.skills.generation.text.scripts.generate import generate_text

                    # 提取内容和标题
                    content = extract_content_from_data(input_data)
                    title = extract_title_from_data(input_data)

                    # 构建 AI 审核的 prompt
                    review_prompt = f"""请对以下内容进行质量评分，评分范围 0-100 分。

评分维度：
1. 可读性（0-30分）：句子长度、段落结构、标点符号使用
2. 完整性（0-30分）：内容完整度、逻辑连贯性
3. 吸引力（0-40分）：标题吸引力、内容价值、适合平台发布

待评分内容：
标题：{title or '无'}
内容：{content or ''}

平台：{config.get('platform', 'general')}

请按以下JSON格式返回评分结果（不要添加其他文字）：
{{
  "overall_score": 总分(0-100),
  "is_qualified": true/false,
  "scores": {{
    "readability": 可读性得分,
    "completeness": 完整性得分,
    "attractiveness": 吸引力得分
  }},
  "suggestions": ["改进建议1", "改进建议2"]
}}
"""

                    # 调用 LLM 进行审核
                    ai_result = await generate_text(
                        llm_service=llm_service,
                        prompt_template=review_prompt,
                        content='',
                        variables={},
                        max_tokens=500,
                        temperature=0.3,  # 低温度保证评分稳定
                        provider=llm_provider
                    )

                    # 解析 AI 返回的评分
                    import re
                    ai_content = ai_result.get('parsed_content', '')
                    json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            result['method'] = 'ai'
                        except json.JSONDecodeError:
                            # AI 返回格式错误，使用默认评分
                            result = {'overall_score': 60, 'is_qualified': True, 'error': 'AI返回格式错误', 'method': 'ai'}
                    else:
                        result = {'overall_score': 60, 'is_qualified': True, 'error': 'AI未返回有效评分', 'method': 'ai'}

                    logger.info(f"AI质量评分完成，总分: {result.get('overall_score')}, 合格: {result.get('is_qualified')}")

                else:
                    # 本地规则审核模式
                    from app.skills.skills.review.quality.scripts.score_quality import ContentQualityScorer

                    # 调试：打印input_data结构
                    logger.info(f"review.quality 收到 input_data 类型: {type(input_data)}")
                    if isinstance(input_data, dict):
                        logger.info(f"review.quality 收到 input_data 键: {list(input_data.keys())[:10]}")

                    # 提取内容和标题
                    content = extract_content_from_data(input_data)
                    title = extract_title_from_data(input_data)

                    logger.info(f"review.quality: 提取到的content长度={len(content)}, title={'有' if title else '无'}")

                    if not content:
                        result = {'overall_score': 0, 'is_qualified': False, 'error': '内容为空', 'method': 'rule_based'}
                    else:
                        # 获取配置，使用全局设置作为默认值
                        platform = config.get('platform', 'xiaohongshu')
                        dimensions = config.get('dimensions', 'readability,completeness,attractiveness')
                        min_score = config.get('min_score') or settings.min_quality_score
                        weights = config.get('weights') or settings.weights

                        # 创建评分器
                        scorer = ContentQualityScorer(platform=platform)

                        # 执行评分
                        result = scorer.full_score(
                            content=content,
                            title=title if title else None,
                            dimensions=dimensions.split(',') if isinstance(dimensions, str) else dimensions,
                            min_score=min_score,
                            weights=weights
                        )

                        result['method'] = 'rule_based'

                        logger.info(f"规则质量评分完成，总分: {result.get('overall_score')}, 合格: {result.get('is_qualified')}")

                # 合并输入数据和评分结果
                if isinstance(input_data, dict):
                    result = {**input_data, **result}

                return result

            logger.warning(f"未知的 Review Skill: {skill_name}")
            return input_data

        except Exception as e:
            logger.error(f"执行 Review Skill {skill_name} 失败: {str(e)}", exc_info=True)
            return input_data

    async def _execute_conditional_skill(
        self,
        skill_name: str,
        input_data: Any,
        config: Dict
    ) -> Any:
        """
        执行条件判断 Skill

        Args:
            skill_name: Skill名称
            input_data: 输入数据
            config: Skill配置

        Returns:
            Skill执行结果
        """
        try:
            if skill_name == 'conditional.save':
                # 条件保存：根据前面的审核结果决定是否保存
                # 需要检查前序skill的结果

                # 获取条件
                conditions = config.get('conditions', {})
                min_quality_score = conditions.get('min_quality_score', 60)
                require_safe = conditions.get('require_safe', True)
                skip_on_failure = conditions.get('skip_on_failure', True)

                # 检查input_data中的审核结果
                should_save = True
                reasons = []

                # 检查质量评分
                if 'quality_score' in input_data or 'overall_score' in input_data:
                    score = input_data.get('quality_score') or input_data.get('overall_score', 0)
                    if score < min_quality_score:
                        should_save = False
                        reasons.append(f"质量评分不足: {score} < {min_quality_score}")

                # 检查敏感词检测
                if 'sensitive_check' in input_data or 'is_safe' in input_data:
                    is_safe = input_data.get('sensitive_check', {}).get('is_safe', True) if 'sensitive_check' in input_data else input_data.get('is_safe', True)
                    if require_safe and not is_safe:
                        should_save = False
                        reasons.append("内容存在敏感词或违规内容")

                # 检查是否有错误
                if 'error' in input_data and skip_on_failure:
                    should_save = False
                    reasons.append(f"前序步骤出错: {input_data.get('error')}")

                result = {
                    'should_save': should_save,
                    'reasons': reasons,
                    'skip': not should_save
                }

                if should_save:
                    logger.info(f"条件保存通过，内容符合保存条件")
                    # 返回原始数据，但附加条件检查结果
                    # 注意：不要直接修改input_data，创建新的结果
                    if isinstance(input_data, dict):
                        # 将条件检查结果添加到input_data中
                        return {**input_data, **result}
                    else:
                        return {'data': input_data, **result}
                else:
                    # 条件不满足，抛出异常中断后续skill执行
                    error_msg = f"条件保存未通过: {', '.join(reasons)}"
                    logger.warning(error_msg)
                    raise RuntimeError(error_msg)

            logger.warning(f"未知的 Conditional Skill: {skill_name}")
            return input_data

        except Exception as e:
            logger.error(f"执行 Conditional Skill {skill_name} 失败: {str(e)}", exc_info=True)
            return input_data

    def get_skill_description(self, skill_name: str) -> Optional[str]:
        """获取Skill描述"""
        metadata = self.loader.get_skill_metadata(skill_name)
        return metadata.get('description') if metadata else None

    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有Skill"""
        skills = []
        for skill_name in self.loader.list_skill_names():
            metadata = self.loader.get_skill_metadata(skill_name)
            skills.append({
                'name': skill_name,
                'description': metadata.get('description', '') if metadata else ''
            })
        return skills
