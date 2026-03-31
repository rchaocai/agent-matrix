import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Any, Set
from pathlib import Path


class ToutiaoHotSearch:
    """今日头条热搜获取器 - 模拟点击换一换获取完整数据"""
    
    def __init__(self, headless: bool = True, output_dir: str = './output'):
        """
        初始化
        
        Args:
            headless: 是否使用无头模式
            output_dir: 输出目录
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.all_hot_search = []
        self.seen_titles: Set[str] = set()  # 用于去重
    
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
        
        # 定位热搜区域
        hot_container = soup.select_one('.home-hotboard .ttp-hot-board')
        if not hot_container:
            return hot_items
        
        hot_list = hot_container.select_one('ol')
        if not hot_list:
            return hot_items
        
        items = hot_list.select('li')
        
        for item in items:
            try:
                link_elem = item.select_one('a.article-item')
                if not link_elem:
                    continue
                
                # 标题
                title_elem = link_elem.select_one('.news-title')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # 如果标题为空或已存在，跳过
                if not title or title in self.seen_titles:
                    continue
                
                # 链接
                link = link_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = 'https://www.toutiao.com' + link
                
                # 排名
                rank_elem = link_elem.select_one('.news-index')
                rank = rank_elem.get_text(strip=True) if rank_elem else ''
                
                # 标识（热/新/荐等）
                icon_elem = link_elem.select_one('.news-icon')
                icon = icon_elem.get_text(strip=True) if icon_elem else ''
                
                # 是否置顶
                is_stick = bool(item.select_one('.icon-stick'))
                
                hot_item = {
                    'rank': rank,
                    'title': title,
                    'link': link,
                    'tag': icon,
                    'is_top': is_stick
                }
                
                hot_items.append(hot_item)
                self.seen_titles.add(title)  # 记录已见过的标题
                
            except Exception as e:
                print(f"解析出错: {e}")
                continue
        
        return hot_items
    
    async def click_refresh_and_collect(self, page, refresh_times: int = 4) -> List[Dict[str, Any]]:
        """
        多次点击换一换按钮，收集所有热搜数据
        
        Args:
            page: Playwright页面对象
            refresh_times: 点击换一换的次数
            
        Returns:
            所有收集到的热搜数据
        """
        all_items = []
        
        for i in range(refresh_times + 1):  # +1 因为第一次是初始加载
            print(f"\n--- 第 {i+1} 次获取热搜 ---")
            
            # 获取当前页面的热搜
            html_content = await page.content()
            current_items = self.parse_hot_search(html_content)
            
            print(f"本次获取到 {len(current_items)} 条新热搜")
            all_items.extend(current_items)
            
            # 如果不是最后一次，点击换一换
            if i < refresh_times:
                try:
                    # 查找并点击换一换按钮
                    refresh_button = await page.query_selector('.refresh')
                    if refresh_button:
                        await refresh_button.click()
                        print("点击'换一换'按钮")
                        # 等待新内容加载
                        await page.wait_for_timeout(2000)
                    else:
                        print("未找到换一换按钮")
                        break
                except Exception as e:
                    print(f"点击换一换失败: {e}")
                    break
        
        return all_items
    
    async def fetch_all_hot_search(self, refresh_times: int = 4) -> List[Dict[str, Any]]:
        """获取所有热搜数据（通过多次点击换一换）"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            print("正在访问 https://www.toutiao.com ...")
            
            try:
                await page.goto("https://www.toutiao.com", timeout=30000)
                await page.wait_for_selector('.home-hotboard', timeout=10000)
                await page.wait_for_timeout(2000)
                
                # 多次点击换一换，收集所有数据
                self.all_hot_search = await self.click_refresh_and_collect(page, refresh_times)
                
                print(f"\n总共获取到 {len(self.all_hot_search)} 条热搜（去重后）")
                return self.all_hot_search
                
            except Exception as e:
                print(f"获取失败: {e}")
                return []
            finally:
                await browser.close()
    
    def print_hot_search(self):
        """打印所有热搜数据"""
        if not self.all_hot_search:
            print("没有热搜数据")
            return
        
        print("\n" + "="*70)
        print("今日头条热搜榜（完整版）".center(68))
        print("="*70)
        
        # 按是否置顶和排名排序
        top_items = [item for item in self.all_hot_search if item.get('is_top')]
        normal_items = [item for item in self.all_hot_search if not item.get('is_top')]
        
        if top_items:
            print("\n【置顶热搜】")
            for item in top_items:
                print(f"   {item['title']}")
                print(f"   链接: {item['link']}\n")
        
        if normal_items:
            print("\n【普通热搜】")
            for item in normal_items:
                tag = f"[{item['tag']}]" if item.get('tag') else ""
                print(f"{item['rank']:>4}. {item['title']} {tag}")
                print(f"     链接: {item['link']}\n")
    
    def save_to_json(self, filename: str = "toutiao_hotsearch_full.json") -> str:
        """保存所有热搜数据为JSON"""
        if not self.all_hot_search:
            raise ValueError("没有数据可保存")
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total': len(self.all_hot_search),
            'hot_search': self.all_hot_search
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存至: {filepath}")
        return str(filepath)


async def main():
    """主函数"""
    fetcher = ToutiaoHotSearch(headless=False)  # 设为False可以看到点击过程，调试用
    
    print("开始获取今日头条热搜（将点击'换一换'4次）...")
    await fetcher.fetch_all_hot_search(refresh_times=4)
    
    fetcher.print_hot_search()
    fetcher.save_to_json()


if __name__ == "__main__":
    asyncio.run(main())