"""
主题分析Skill - 使用LLM分析数据并推荐主题
"""
import asyncio
import json
from typing import List, Dict, Optional
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.llm_service import create_llm_service_from_env

logger = logging.getLogger(__name__)


class TopicAnalysisSkill:
    """主题分析技能"""
    
    def __init__(self):
        self.llm_service = create_llm_service_from_env()
    
    async def execute(self, config: Dict) -> Dict:
        """
        执行主题分析
        
        Args:
            config: 配置参数
                - input_data: 输入数据（来自采集技能）
                - llm_provider: LLM提供商
                - model: 模型名称（可选）
                - count: 推荐主题数量
                - target_audience: 目标受众
                - platform: 目标平台
        
        Returns:
            {
                'topics': [
                    {
                        'topic': '主题标题',
                        'score': 0.95,
                        'reason': '推荐理由',
                        'keywords': ['关键词'],
                        'suggested_angle': '建议角度',
                        'expected_engagement': '高/中/低'
                    }
                ],
                'analysis_summary': '分析总结'
            }
        """
        input_data = config.get('input_data', [])
        llm_provider = config.get('llm_provider', 'openrouter')
        model = config.get('model')
        count = config.get('count', 3)
        target_audience = config.get('target_audience', '大众')
        platform = config.get('platform', 'xiaohongshu')
        
        logger.info(f"开始主题分析: provider={llm_provider}, count={count}, audience={target_audience}")
        
        # 准备数据摘要
        data_summary = self._prepare_data_summary(input_data)
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(
            data_summary=data_summary,
            count=count,
            target_audience=target_audience,
            platform=platform
        )
        
        # 调用LLM分析
        result = await self.llm_service.generate_text(
            prompt=prompt,
            provider=llm_provider,
            max_tokens=2000,
            temperature=0.7,
            system_message=self._get_system_message()
        )
        
        if 'error' in result:
            logger.error(f"LLM分析失败: {result['error']}")
            return {
                'success': False,
                'error': result['error'],
                'topics': [],
                'analysis_summary': f"分析失败: {result['error']}"
            }
        
        # 解析LLM返回的结果
        topics = self._parse_llm_response(result['generated_text'])
        
        logger.info(f"分析完成，推荐 {len(topics)} 个主题")
        
        return {
            'success': True,
            'topics': topics[:count],
            'analysis_summary': f"基于{len(input_data)}条数据分析，推荐{len(topics[:count])}个高潜力主题",
            'llm_info': {
                'provider': result.get('provider'),
                'model': result.get('model'),
                'tokens_used': result.get('tokens_used')
            }
        }
    
    def _prepare_data_summary(self, input_data: List) -> str:
        """准备数据摘要"""
        if not input_data:
            return "无数据"
        
        summary_parts = []
        
        # 处理不同格式的输入数据
        if isinstance(input_data, dict):
            # 如果是字典，可能是RSS或其他采集结果
            if 'topics' in input_data:
                # 来自topic_discovery的数据
                for i, topic in enumerate(input_data['topics'][:10], 1):
                    title = topic.get('topic', '未知标题')
                    source = topic.get('source', '未知来源')
                    summary_parts.append(f"{i}. {title} (来源: {source})")
            elif 'items' in input_data:
                # 来自RSS的数据
                for i, item in enumerate(input_data['items'][:10], 1):
                    title = item.get('title', '未知标题')
                    summary_parts.append(f"{i}. {title}")
        elif isinstance(input_data, list):
            # 如果是列表
            for i, item in enumerate(input_data[:10], 1):
                if isinstance(item, dict):
                    title = item.get('title', item.get('topic', '未知标题'))
                    summary_parts.append(f"{i}. {title}")
                else:
                    summary_parts.append(f"{i}. {str(item)}")
        
        return "\n".join(summary_parts)
    
    def _build_analysis_prompt(
        self,
        data_summary: str,
        count: int,
        target_audience: str,
        platform: str
    ) -> str:
        """构建分析提示词"""
        platform_names = {
            'xiaohongshu': '小红书',
            'weixin': '微信公众号',
            'zhihu': '知乎',
            'weibo': '微博'
        }
        platform_name = platform_names.get(platform, platform)
        
        prompt = f"""请分析以下数据，智能推荐{count}个最适合的创作主题。

## 数据来源
{data_summary}

## 发布平台
{platform_name}

## 分析要求
1. 从数据中识别出最具潜力的主题
2. 分析数据的热点趋势和用户兴趣
3. 结合{platform_name}平台特性（偏好实用、有趣、易传播的内容）
4. 根据数据特点，推断目标受众
5. 为每个主题提供创作建议

## 输出格式
请严格按照以下JSON格式输出：

```json
{{
  "topics": [
    {{
      "topic": "主题标题（吸引人的标题）",
      "score": 0.95,
      "reason": "推荐理由（50字以内）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "suggested_angle": "建议的创作角度",
      "expected_engagement": "高/中/低",
      "target_audience": "推断的目标受众"
    }}
  ],
  "analysis_summary": "分析总结"
}}
```

注意：
- 主题标题要吸引人，可以使用数字、疑问句等技巧
- 评分范围0-1，综合考虑热度、时效性、可操作性
- 关键词要准确，3-5个
- 建议角度要具体，有可操作性
- 根据数据特点和{platform_name}平台特性，推断目标受众
- 只输出JSON，不要有其他内容
"""
        
        return prompt
    
    def _get_system_message(self) -> str:
        """获取系统消息"""
        return """你是一个专业的内容策划师，擅长从海量数据中发现有价值的内容主题。
你的分析基于：
1. 数据趋势和热度
2. 目标受众需求
3. 平台特性
4. 内容创作价值

请确保输出严格的JSON格式，便于程序解析。"""
    
    def _parse_llm_response(self, response_text: str) -> List[Dict]:
        """解析LLM返回的结果"""
        try:
            # 尝试提取JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            logger.info(f"LLM返回内容长度: {len(response_text)}")
            logger.info(f"JSON起始位置: {json_start}, 结束位置: {json_end}")
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                logger.info(f"提取的JSON内容: {json_str[:200]}...")
                result = json.loads(json_str)
                return result.get('topics', [])
            else:
                logger.warning("未找到JSON格式的响应")
                logger.warning(f"LLM返回内容: {response_text[:500]}...")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"LLM返回内容: {response_text[:1000]}...")
            return []


async def main():
    """测试函数"""
    # 模拟输入数据
    mock_input_data = {
        "topics": [
            {
                "topic": "科技爱好者周刊（第 386 期）：当外卖员接入 AI",
                "source": "阮一峰的网络日志",
                "keywords": ["AI", "外卖", "效率"]
            },
            {
                "topic": "字节全家桶 Seed 2.0 + TRAE 玩转 Skill",
                "source": "阮一峰的网络日志",
                "keywords": ["字节", "AI", "工具"]
            },
            {
                "topic": "职场新人必知的5个潜规则",
                "source": "36氪",
                "keywords": ["职场", "新人", "规则"]
            }
        ]
    }
    
    skill = TopicAnalysisSkill()
    
    # 测试配置
    config = {
        'input_data': mock_input_data,
        'llm_provider': 'openrouter',
        'model': 'meta-llama/llama-3-8b-instruct:free',
        'count': 3,
        'target_audience': '职场新人',
        'platform': 'xiaohongshu'
    }
    
    result = await skill.execute(config)
    
    print("\n" + "="*60)
    print("🎯 主题分析结果")
    print("="*60)
    
    for i, topic in enumerate(result['topics'], 1):
        print(f"\n{i}. {topic['topic']}")
        print(f"   评分: {topic['score']}")
        print(f"   理由: {topic['reason']}")
        print(f"   关键词: {', '.join(topic['keywords'])}")
        print(f"   建议角度: {topic['suggested_angle']}")
        print(f"   预期互动: {topic['expected_engagement']}")
    
    print(f"\n{result['analysis_summary']}")
    
    if 'llm_info' in result:
        print(f"\nLLM信息:")
        print(f"  提供商: {result['llm_info']['provider']}")
        print(f"  模型: {result['llm_info']['model']}")
        print(f"  Token使用: {result['llm_info']['tokens_used']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
