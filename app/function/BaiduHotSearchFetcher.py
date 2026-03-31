import asyncio
from playwright.async_api import async_playwright
import json
import re
from typing import List, Dict, Optional
import csv
from datetime import datetime


class BaiduHotSearchFetcher:
    def __init__(self, headless: bool = True):
        """
        初始化百度热搜爬虫
        
        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self):
        """初始化浏览器"""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def fetch_page(self, url: str, wait_time: int = 3000) -> Optional[str]:
        """
        获取页面内容
        
        Args:
            url: 页面URL
            wait_time: 等待时间（毫秒）
        """
        try:
            print(f"正在访问: {url}")
            await self.page.goto(url, wait_until='networkidle')
            
            # 等待页面加载完成
            await self.page.wait_for_timeout(wait_time)
            
            # 获取页面内容
            content = await self.page.content()
            return content
        except Exception as e:
            print(f"页面访问失败: {e}")
            return None
    
    async def extract_json_data(self) -> Optional[Dict]:
        """从页面中提取JSON数据"""
        try:
            # 方法1: 从script标签中提取
            json_data = await self.page.evaluate('''
                () => {
                    // 查找包含热搜数据的script标签
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            if (data && data.data && data.data.cards) {
                                return data;
                            }
                        } catch (e) {}
                    }
                    
                    // 查找window.__INITIAL_STATE__
                    if (window.__INITIAL_STATE__) {
                        return window.__INITIAL_STATE__;
                    }
                    
                    return null;
                }
            ''')
            
            if json_data:
                return json_data
            
            # 方法2: 从HTML注释中提取
            html_content = await self.page.content()
            match = re.search(r'<!--s-data:(.*?)-->', html_content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
        except Exception as e:
            print(f"提取JSON数据失败: {e}")
        
        return None
    
    async def extract_hot_list(self) -> List[Dict]:
        """从页面中提取热搜列表"""
        try:
            hot_list = await self.page.evaluate('''
                () => {
                    const items = [];
                    
                    // 查找所有热搜条目
                    const elements = document.querySelectorAll('[class*="category-wrap"]');
                    
                    elements.forEach((el, index) => {
                        try {
                            // 提取标题
                            const titleEl = el.querySelector('[class*="title"]');
                            const title = titleEl ? titleEl.textContent.trim() : '';
                            
                            // 提取描述
                            const descEl = el.querySelector('[class*="hot-desc"]');
                            const desc = descEl ? descEl.textContent.trim() : '';
                            
                            // 提取热搜指数
                            const scoreEl = el.querySelector('[class*="hot-index"]');
                            const score = scoreEl ? scoreEl.textContent.trim() : '';
                            
                            // 提取热度标签
                            const tagEl = el.querySelector('[class*="hot-tag"]');
                            const tag = tagEl ? tagEl.textContent.trim() : '';
                            
                            // 提取排名
                            const rankEl = el.querySelector('[class*="index"]');
                            let rank = rankEl ? rankEl.textContent.trim() : (index + 1).toString();
                            
                            // 提取图片
                            const imgEl = el.querySelector('img');
                            const img = imgEl ? imgEl.src : '';
                            
                            // 提取链接
                            const linkEl = el.querySelector('a[href*="wd="]');
                            const url = linkEl ? linkEl.href : '';
                            
                            // 提取热搜词（从URL中）
                            let word = title;
                            if (url) {
                                const match = url.match(/wd=([^&]+)/);
                                if (match) {
                                    word = decodeURIComponent(match[1]);
                                }
                            }
                            
                            items.push({
                                rank: rank,
                                word: word,
                                title: title,
                                desc: desc,
                                hot_score: score,
                                hot_tag: tag,
                                url: url,
                                img: img,
                                index: index + 1
                            });
                        } catch (e) {
                            console.error('解析条目失败:', e);
                        }
                    });
                    
                    return items;
                }
            ''')
            
            return hot_list
            
        except Exception as e:
            print(f"提取热搜列表失败: {e}")
            return []
    
    async def get_hot_search(self, url: str = "https://top.baidu.com/board?tab=realtime") -> List[Dict]:
        """
        获取热搜数据
        
        Args:
            url: 百度热搜页面URL
            
        Returns:
            热搜数据列表
        """
        await self.setup()
        
        try:
            # 获取页面内容
            await self.fetch_page(url)
            
            # 先尝试从JSON数据中提取
            json_data = await self.extract_json_data()
            hot_list = []
            
            if json_data and 'data' in json_data:
                # 从JSON中解析
                data = json_data['data']
                if 'cards' in data:
                    for card in data['cards']:
                        if card.get('component') == 'hotList' and 'content' in card:
                            for i, item in enumerate(card['content']):
                                hot_item = {
                                    'rank': i + 1,
                                    'word': item.get('word', ''),
                                    'query': item.get('query', ''),
                                    'desc': item.get('desc', ''),
                                    'hot_score': item.get('hotScore', ''),
                                    'hot_change': item.get('hotChange', ''),
                                    'hot_tag': self._get_hot_tag_name(item.get('hotTag', '0')),
                                    'url': item.get('url', ''),
                                    'img': item.get('img', ''),
                                    'is_top': item.get('isTop', False),
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                hot_list.append(hot_item)
            
            # 如果JSON提取失败，从DOM中提取
            if not hot_list:
                print("JSON数据提取失败，尝试从DOM提取...")
                hot_list = await self.extract_hot_list()
            
            return hot_list
            
        finally:
            await self.close()
    
    def _get_hot_tag_name(self, tag_code: str) -> str:
        """转换热度标签代码"""
        tag_map = {
            '0': '',
            '1': '新',
            '2': '热',
            '3': '热',
            '4': '沸'
        }
        return tag_map.get(tag_code, '')
    
    def save_to_json(self, hot_list: List[Dict], filename: str = None):
        """保存为JSON文件"""
        if not filename:
            filename = f"baidu_hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hot_list, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    
    def save_to_csv(self, hot_list: List[Dict], filename: str = None):
        """保存为CSV文件"""
        if not hot_list:
            return
        
        if not filename:
            filename = f"baidu_hot_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['rank', 'word', 'query', 'desc', 'hot_score', 'hot_tag', 'url', 'img', 'is_top', 'update_time']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in hot_list:
                row = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"数据已保存到 {filename}")
    
    def print_hot_list(self, hot_list: List[Dict], limit: int = 20):
        """打印热搜列表"""
        if not hot_list:
            print("未获取到热搜数据")
            return
        
        print(f"\n{'='*100}")
        print(f"{'排名':^6} {'热搜词':^40} {'热搜指数':^12} {'标签':^6} {'简介':^30}")
        print(f"{'='*100}")
        
        for item in hot_list[:limit]:
            rank = item.get('rank', '')
            word = item.get('word', '')
            if len(word) > 36:
                word = word[:36] + '..'
            
            hot_score = item.get('hot_score', '')
            hot_tag = f"[{item.get('hot_tag', '')}]" if item.get('hot_tag') else ''
            desc = item.get('desc', '')[:28] + '..' if len(item.get('desc', '')) > 28 else item.get('desc', '')
            
            print(f"{rank:^6} {word:^40} {hot_score:^12} {hot_tag:^6} {desc:^30}")


# 异步函数版本
async def get_baidu_hot_search_async(url: str = "https://top.baidu.com/board?tab=realtime", 
                                      headless: bool = True) -> List[Dict]:
    """
    异步获取百度热搜数据
    
    Args:
        url: 百度热搜页面URL
        headless: 是否使用无头模式
        
    Returns:
        热搜数据列表
    """
    scraper = BaiduHotSearchPlaywright(headless=headless)
    return await scraper.get_hot_search(url)


# 同步调用版本
def get_baidu_hot_search(url: str = "https://top.baidu.com/board?tab=realtime", 
                          headless: bool = True) -> List[Dict]:
    """
    同步获取百度热搜数据（封装异步调用）
    
    Args:
        url: 百度热搜页面URL
        headless: 是否使用无头模式
        
    Returns:
        热搜数据列表
    """
    async def _fetch():
        scraper = BaiduHotSearchPlaywright(headless=headless)
        return await scraper.get_hot_search(url)
    
    return asyncio.run(_fetch())


async def main_async():
    """异步主函数"""
    # 创建爬虫实例
    scraper = BaiduHotSearchPlaywright(headless=True)
    
    try:
        # 获取热搜数据
        hot_list = await scraper.get_hot_search()
        
        if hot_list:
            # 打印热搜列表
            scraper.print_hot_list(hot_list)
            
            # 保存数据
            scraper.save_to_json(hot_list)
            scraper.save_to_csv(hot_list)
            
            print(f"\n共获取 {len(hot_list)} 条热搜数据")
            
            # 数据分析示例
            print("\n=== 数据分析 ===")
            
            # 按热搜指数排序
            sorted_by_score = sorted(hot_list, 
                                    key=lambda x: int(x.get('hot_score', 0)) if x.get('hot_score', '').isdigit() else 0, 
                                    reverse=True)
            print(f"最高热搜指数: {sorted_by_score[0]['word']} - {sorted_by_score[0]['hot_score']}")
            
            # 统计热度标签
            tag_count = {}
            for item in hot_list:
                tag = item.get('hot_tag', '')
                if tag:
                    tag_count[tag] = tag_count.get(tag, 0) + 1
            
            if tag_count:
                print("热度标签分布:")
                for tag, count in tag_count.items():
                    print(f"  {tag}: {count}条")
            
            return hot_list
        else:
            print("未获取到热搜数据")
            return []
            
    finally:
        await scraper.close()


def main():
    """同步主函数"""
    hot_list = get_baidu_hot_search()
    
    if hot_list:
        print(f"成功获取 {len(hot_list)} 条热搜数据")
        
        # 示例：打印前10条热搜
        print("\n前10条热搜：")
        for item in hot_list[:10]:
            print(f"{item['rank']}. {item['word']} - {item['hot_score']}")
    else:
        print("获取失败")


if __name__ == "__main__":
    # 运行异步版本
    # asyncio.run(main_async())
    
    # 或运行同步版本
    main()