import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Any, Set
from pathlib import Path


class WeiboHotSearch:
    """微博热搜获取器 - 逐屏滚动加载所有热搜"""
    
    def __init__(self, headless: bool = False, output_dir: str = './output'):
        """
        初始化
        
        Args:
            headless: 是否使用无头模式
            output_dir: 输出目录
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.hot_search_data = []
        self.seen_titles: Set[str] = set()  # 全局set，用于去重
        self.all_unique_hot_search = []  # 存储所有去重后的热搜
    
    def parse_hot_search(self, html_content: str) -> List[Dict[str, Any]]:
        """
        从HTML中解析热搜数据
        
        Args:
            html_content: HTML字符串
            
        Returns:
            热搜数据列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        hot_items = []
        
        # 查找所有热搜项
        items = soup.select('._wrap_s5b56_2')
        
        # 如果没有找到，尝试其他选择器
        if not items:
            items = soup.select('.vue-recycle-scroller__item-view')
        
        for item in items:
            try:
                # 获取排名
                rank_elem = item.select_one('._rank1_s5b56_21 ._ranknum_s5b56_39, ._ranktop_s5b56_6')
                rank = rank_elem.get_text(strip=True) if rank_elem else ''
                
                # 获取标题
                title_elem = item.select_one('._tit_s5b56_65 span, ._tit_s5b56_65')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                if not title:
                    # 尝试其他标题选择器
                    title_elem = item.select_one('a span, a')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                
                if not title:
                    continue
                
                # 获取热度值
                heat_elem = item.select_one('._num_s5b56_120, ._num_s5b56_120 span')
                heat = heat_elem.get_text(strip=True) if heat_elem else ''
                
                # 获取热搜标识
                tag_elem = item.select_one('.wbpro-icon-search-2')
                tag = tag_elem.get_text(strip=True) if tag_elem else ''
                
                # 获取链接
                link_elem = item.select_one('a._tit_s5b56_65, a')
                link = link_elem.get('href', '') if link_elem else ''
                if link and not link.startswith('http'):
                    link = 'https://s.weibo.com' + link
                
                # 判断是否为置顶
                is_top = bool(item.select_one('._ranktop_s5b56_6'))
                
                hot_items.append({
                    'rank': rank,
                    'title': title,
                    'heat': heat,
                    'tag': tag,
                    'link': link,
                    'is_top': is_top
                })
                
            except Exception as e:
                continue
        
        return hot_items
    
    def deduplicate_and_number(self, hot_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重并按照顺序标序号
        
        Args:
            hot_items: 原始热搜数据列表
            
        Returns:
            去重并编号后的热搜数据列表
        """
        unique_items = []
        
        for item in hot_items:
            title = item.get('title', '')
            
            # 如果标题不在seen_titles中，说明是新数据
            if title and title not in self.seen_titles:
                self.seen_titles.add(title)
                
                # 生成新的序号（从1开始）
                new_rank = len(self.all_unique_hot_search) + 1
                
                # 创建新item，保留原始数据但更新rank
                new_item = item.copy()
                new_item['original_rank'] = item.get('rank', '')  # 保存原始排名
                new_item['rank'] = str(new_rank)  # 设置新的连续序号
                
                self.all_unique_hot_search.append(new_item)
                unique_items.append(new_item)
        
        return unique_items
    
    async def scroll_to_load_all(self, page, max_scrolls: int = 20):
        """
        滚动加载所有热搜
        
        Args:
            page: Playwright页面对象
            max_scrolls: 最大滚动次数
        """
        print("5. 开始滚动加载更多热搜...")
        
        # 获取页面高度
        page_height = await page.evaluate('document.body.scrollHeight')
        viewport_height = await page.evaluate('window.innerHeight')
        
        print(f"   页面总高度: {page_height}, 视口高度: {viewport_height}")
        
        # 计算每次滚动的距离
        scroll_distance = viewport_height - 100
        
        previous_count = 0
        consecutive_no_change = 0
        
        for step in range(1, max_scrolls + 1):
            # 滚动到下一个位置
            scroll_position = step * scroll_distance
            await page.evaluate(f'window.scrollTo({{top: {scroll_position}, behavior: "smooth"}})')
            
            # 等待新内容加载
            await page.wait_for_timeout(2000)
            
            # 获取当前页面的HTML并解析
            current_html = await page.content()
            current_hot_search = self.parse_hot_search(current_html)
            
            # 去重并获取新增加的热搜
            before_count = len(self.all_unique_hot_search)
            self.deduplicate_and_number(current_hot_search)
            after_count = len(self.all_unique_hot_search)
            
            print(f"   第 {step} 次滚动，新增加: {after_count - before_count}，累计: {after_count}")
            
            # 如果不再有新的热搜，计数加1
            if (after_count - before_count) == 0:
                consecutive_no_change += 1
                if consecutive_no_change >= 3:
                    print("   已无新数据加载，停止滚动")
                    break
            else:
                consecutive_no_change = 0
            
            # 如果滚动超过页面高度，停止
            if scroll_position > page_height + 500:
                print("   已滚动到底部")
                break
        
        print(f"   滚动加载完成，共获取 {len(self.all_unique_hot_search)} 条不重复热搜")
    
    async def navigate_to_hot(self, page):
        """
        导航到热搜页面
        
        Args:
            page: Playwright页面对象
        """
        print("1. 访问微博首页...")
        await page.goto("https://weibo.com", timeout=60000)
        
        print("2. 等待页面加载...")
        await page.wait_for_timeout(5000)
        
        print("3. 查找并点击'热搜'标签...")
        
        # 尝试多种方式找到热搜链接
        selectors = [
            'a[href*="/hot/search"]',
            'a[href*="hot"][title*="热搜"]',
            'text="热搜"',
            'div[role="link"] span:text("热搜")',
            '._text_118ye_24:text("热搜")'
        ]
        
        found = False
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    await elements[0].click()
                    print(f"   已使用选择器 '{selector}' 点击热搜")
                    found = True
                    break
            except:
                continue
        
        if not found:
            print("   未找到热搜标签，直接访问热搜页面")
            await page.goto("https://weibo.com/hot/search", timeout=60000)
        
        print("4. 等待热搜页面初始加载...")
        await page.wait_for_selector('._wrap_s5b56_2', timeout=10000)
        await page.wait_for_timeout(3000)
        
        # 获取初始热搜
        initial_html = await page.content()
        initial_hot_search = self.parse_hot_search(initial_html)
        self.deduplicate_and_number(initial_hot_search)
        print(f"   初始加载 {len(initial_hot_search)} 条热搜，去重后 {len(self.all_unique_hot_search)} 条")
    
    async def fetch_hot_search(self) -> List[Dict[str, Any]]:
        """获取热搜数据"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # 导航到热搜页面
                await self.navigate_to_hot(page)
                
                # 滚动加载更多
                await self.scroll_to_load_all(page)
                
                # 设置最终数据
                self.hot_search_data = self.all_unique_hot_search
                
                print(f"\n成功获取 {len(self.hot_search_data)} 条不重复热搜")
                return self.hot_search_data
                
            except Exception as e:
                print(f"获取失败: {e}")
                # 如果出错但有已获取的数据，也返回
                if self.all_unique_hot_search:
                    self.hot_search_data = self.all_unique_hot_search
                    print(f"已获取部分数据: {len(self.hot_search_data)} 条")
                return self.hot_search_data
            finally:
                await browser.close()
    
    def print_hot_search(self):
        """打印热搜数据"""
        if not self.hot_search_data:
            print("没有热搜数据")
            return
        
        print("\n" + "="*80)
        print(f"微博热搜榜 (共{len(self.hot_search_data)}条，已去重并重新编号)".center(78))
        print("="*80)
        
        for item in self.hot_search_data[:20]:  # 只打印前20条
            rank = item.get('rank', '')
            title = item.get('title', '')
            heat = item.get('heat', '')
            tag = item.get('tag', '')
            is_top = item.get('is_top', False)
            original_rank = item.get('original_rank', '')
            
            if is_top:
                print(f"【置顶】 {title} [{tag}]")
            else:
                print(f"{rank:>4}. {title} [{tag}] (原排名: {original_rank})")
            
            if heat:
                print(f"      热度: {heat}")
        
        if len(self.hot_search_data) > 20:
            print(f"\n... 共{len(self.hot_search_data)}条热搜，仅显示前20条")
    
    def save_to_json(self, filename: str = None) -> str:
        """保存热搜数据为JSON"""
        if not self.hot_search_data:
            data = {
                'timestamp': datetime.now().isoformat(),
                'total': 0,
                'hot_search': [],
                'note': '未获取到热搜数据'
            }
        else:
            data = {
                'timestamp': datetime.now().isoformat(),
                'total': len(self.hot_search_data),
                'hot_search': self.hot_search_data
            }
        
        if not filename:
            filename = f"weibo_hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存至: {filepath}")
        return str(filepath)


async def main():
    """主函数"""
    print("开始获取微博热搜...")
    print("提示：首次使用可能需要扫码登录")
    
    fetcher = WeiboHotSearch(headless=False)
    await fetcher.fetch_hot_search()
    fetcher.print_hot_search()
    fetcher.save_to_json()


if __name__ == "__main__":
    asyncio.run(main())