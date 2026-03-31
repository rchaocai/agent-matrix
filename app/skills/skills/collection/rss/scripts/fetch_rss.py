"""
RSS内容采集脚本
"""

import feedparser
import json
import sys
import argparse
from datetime import datetime


def fetch_rss(url: str, max_items: int = 10, min_length: int = 100):
    """
    从RSS源采集内容

    Args:
        url: RSS订阅源URL
        max_items: 最多采集文章数
        min_length: 最小内容长度

    Returns:
        JSON格式的文章列表
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"开始采集RSS: {url}")

    try:
        feed = feedparser.parse(url)

        # 检查是否解析成功
        if hasattr(feed, 'bozo') and feed.bozo:
            logger.warning(f"RSS解析警告: {feed.bozo}")

        if not feed.entries:
            logger.error(f"RSS源没有任何内容: {url}")
            return json.dumps({
                'error': f'RSS源没有任何内容: {url}',
                'items': [],
                'total': 0
            }, ensure_ascii=False, indent=2)

        logger.info(f"RSS源有 {len(feed.entries)} 个条目")

        items = []
        for entry in feed.entries[:max_items]:
            # 提取内容
            content = entry.get('summary', '') or entry.get('description', '')
            title = entry.get('title', '无标题')

            # 过滤过短内容
            if len(content) < min_length:
                logger.debug(f"跳过过短内容: {title} ({len(content)}字符)")
                continue

            items.append({
                'title': title,
                'content': content,
                'url': entry.get('link', ''),
                'published': entry.get('published', datetime.now().isoformat()),
                'source': url
            })

        if items:
            logger.info(f"成功采集 {len(items)} 篇文章")
        else:
            logger.warning(f"采集完成但没有符合条件的文章（最小长度: {min_length}）")

        return json.dumps({
            'items': items,
            'total': len(items)
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"RSS采集失败: {url}, 错误: {str(e)}")
        return json.dumps({
            'error': f'RSS采集失败: {str(e)}',
            'url': url,
            'items': [],
            'total': 0
        }, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    import sys
    import logging

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='RSS内容采集工具')
    parser.add_argument('--url', required=True, help='RSS订阅源URL')
    parser.add_argument('--max-items', type=int, default=10, help='最多采集文章数')
    parser.add_argument('--min-length', type=int, default=100, help='最小内容长度')
    args = parser.parse_args()

    result = fetch_rss(args.url, args.max_items, args.min_length)
    print(result)

    # 解析结果判断是否成功
    import json
    try:
        result_dict = json.loads(result)
        if 'error' in result_dict:
            # 有错误，返回非0退出码
            sys.exit(1)
        elif result_dict.get('total', 0) == 0:
            # 没有采集到内容，返回非0退出码
            sys.exit(1)
    except json.JSONDecodeError:
        pass
