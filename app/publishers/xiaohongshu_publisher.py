"""
小红书自动发布器
使用Playwright实现自动化登录和发布
适配新版页面结构
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


class XiaohongshuPublisher:
    """小红书自动发布器 - 适配新版页面"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.base_url = "https://creator.xiaohongshu.com"
        self.playwright = None
        self._closed = False

    async def initialize(self, cookie_str: Optional[str] = None, headless: bool = True):
        """
        初始化浏览器

        Args:
            cookie_str: Cookie字符串（用于保持登录状态）
            headless: 是否使用无头模式
        """
        self.playwright = await async_playwright().start()

        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--start-maximized',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--disable-default-apps',
                '--mute-audio',
                '--no-zygote',
                '--disable-accelerated-2d-canvas',
                '--disable-gl-drawing-for-tests'
            ]
        )

        # 创建上下文（不使用任何持久化存储）
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            offline=False
        )

        # 清除所有现有cookie和存储
        await self.context.clear_cookies()
        logger.info("✓ 已清除context中的所有cookie")

        # 创建页面
        self.page = await self.context.new_page()

        # 设置默认超时 - 增加到120秒以支持多图上传
        self.page.set_default_timeout(120000)

        # 如果有cookie，加载cookie
        if cookie_str:
            await self._load_cookies(cookie_str)

        logger.info("✓ 浏览器初始化完成")

    async def _load_cookies(self, cookie_str: str):
        """加载Cookie"""
        try:
            # 先清除所有现有的cookie
            existing_cookies = await self.context.cookies()
            if existing_cookies:
                logger.info(f"清除 {len(existing_cookies)} 个现有cookie")
                await self.context.clear_cookies()

            # 先访问域名
            await self.page.goto(f"{self.base_url}/", timeout=10000)
            await asyncio.sleep(1)

            # 解析cookie字符串
            cookies = []
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookie_obj = {
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.xiaohongshu.com',
                        'path': '/',
                        'secure': True,
                        'httpOnly': False
                    }
                    cookies.append(cookie_obj)

            # 添加cookies
            await self.context.add_cookies(cookies)
            logger.info(f"✓ 成功加载 {len(cookies)} 个cookie")
            
            # 验证关键cookie
            loaded_cookies = await self.context.cookies()
            a1_cookie = None
            for cookie in loaded_cookies:
                if cookie['name'] == 'a1':
                    a1_cookie = cookie['value']
                    break
            
            if a1_cookie:
                logger.info(f"✓ 加载的a1 cookie: {a1_cookie[:20]}...")
            else:
                logger.warning("⚠ 未找到a1 cookie")

        except Exception as e:
            logger.error(f"✗ 加载cookie失败: {e}")

    async def check_login_status(self) -> bool:
        """
        检查登录状态 - 修复版本，不会导致页面关闭
        """
        try:
            logger.info("检查登录状态...")

            # 直接访问发布页，不先访问首页
            response = await self.page.goto(
                f"{self.base_url}/publish/publish", 
                timeout=30000,
                wait_until='domcontentloaded'
            )
            
            if not response:
                logger.error("页面无响应")
                return False
                
            await asyncio.sleep(3)

            # 验证当前cookie（在清除存储前）
            try:
                current_cookies = await self.context.cookies()
                a1_cookie = None
                for cookie in current_cookies:
                    if cookie['name'] == 'a1':
                        a1_cookie = cookie['value']
                        break
                
                if a1_cookie:
                    logger.info(f"✓ 访问页面后的a1 cookie: {a1_cookie[:20]}...")
                else:
                    logger.warning("⚠ 访问页面后未找到a1 cookie")
            except Exception as e:
                logger.warning(f"验证cookie时出错: {e}")

            # 清除所有存储（localStorage、sessionStorage）
            try:
                await self.page.evaluate("""
                    () => {
                        localStorage.clear();
                        sessionStorage.clear();
                    }
                """)
                logger.info("✓ 已清除localStorage和sessionStorage")
            except Exception as e:
                logger.warning(f"清除存储时出错（可忽略）: {e}")

            # 检查是否跳转到登录页
            current_url = self.page.url
            logger.info(f"当前URL: {current_url}")
            
            if 'login' in current_url.lower():
                logger.warning("未登录：跳转到登录页")
                return False

            # 检查是否有发布页的特征元素
            try:
                # 等待一下让页面加载
                await self.page.wait_for_selector('button:has-text("上传图片")', timeout=10000)
                logger.info("✓ 已登录：检测到上传图片按钮")
                
                # 验证当前登录的用户
                try:
                    # 获取当前页面的cookie
                    current_cookies = await self.context.cookies()
                    a1_cookie = None
                    for cookie in current_cookies:
                        if cookie['name'] == 'a1':
                            a1_cookie = cookie['value']
                            break
                    
                    if a1_cookie:
                        logger.info(f"✓ 当前登录用户的a1 cookie: {a1_cookie[:20]}...")
                    else:
                        logger.warning("⚠ 未找到a1 cookie")
                except Exception as e:
                    logger.warning(f"验证用户时出错: {e}")
                
                return True
            except:
                # 如果没有找到上传图片按钮，可能是其他页面，但只要有publish关键词且不是login就算成功
                if 'publish' in current_url and 'login' not in current_url.lower():
                    logger.info("✓ 已登录：在发布页面")
                    return True
                else:
                    logger.warning("未登录：未检测到发布页面元素")
                    return False

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    async def login_by_qrcode(self, wait_time: int = 120) -> tuple:
        """二维码登录"""
        try:
            logger.info("开始二维码登录流程...")

            # 访问登录页
            login_url = f"{self.base_url}/login"
            await self.page.goto(login_url, timeout=60000)
            await asyncio.sleep(3)

            logger.info(f"请使用小红书APP扫码登录，最多等待: {wait_time}秒")

            # 等待登录成功
            for i in range(wait_time):
                await asyncio.sleep(1)

                try:
                    current_url = self.page.url
                    if 'login' not in current_url.lower():
                        logger.info("检测到登录成功")

                        await asyncio.sleep(2)

                        # 保存cookie
                        cookies = await self.context.cookies()
                        if not cookies:
                            return False, None

                        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                        logger.info(f"✓ 登录成功，获取到 {len(cookies)} 个cookie")
                        return True, cookie_str

                except Exception as e:
                    continue

                if i % 10 == 0 and i > 0:
                    logger.info(f"等待扫码中... {i}/{wait_time}秒")

            logger.warning("登录超时")
            return False, None

        except Exception as e:
            logger.error(f"二维码登录异常: {e}")
            return False, None
        

    async def publish(
        self,
        title: str,
        content: str,
        images: List[str],
        topics: Optional[List[str]] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发布笔记 - 主方法（修复顺序：先确保图片完全上传再填写内容）
        """
        try:
            # 检查页面是否已关闭
            if self._closed or not self.page:
                return {
                    'success': False,
                    'error': '浏览器已关闭',
                    'code': 'browser_closed'
                }

            # 直接导航到图片上传页面
            logger.info("检查登录状态并导航到图片上传页面...")
            response = await self.page.goto(
                f"{self.base_url}/publish/publish?from=menu&target=image", 
                timeout=60000,
                wait_until='domcontentloaded'
            )
            
            if not response:
                return {
                    'success': False,
                    'error': '页面加载失败',
                    'code': 'page_load_failed'
                }
                
            # 检查是否跳转到登录页
            current_url = self.page.url
            logger.info(f"当前URL: {current_url}")
            
            if 'login' in current_url.lower():
                return {
                    'success': False,
                    'error': '未登录，请先登录',
                    'code': 'not_login'
                }

            # 等待页面关键元素出现
            logger.info("等待页面关键元素加载...")
            try:
                await self.page.wait_for_selector('button:has-text("上传图片")', timeout=15000)
                logger.info("✓ 页面关键元素已加载")
            except Exception as e:
                logger.warning(f"等待上传图片按钮超时，但继续流程: {e}")
            
            await asyncio.sleep(2)
            await self.save_screenshot("1_initial_page.png")

            # 1. 确认已在图片上传模式
            await self._verify_image_upload_mode()

            # 2. 上传图片
            logger.info("=" * 50)
            logger.info("开始上传图片流程")
            upload_result = await self._upload_images(images)
            if not upload_result['success']:
                return upload_result
            logger.info("=" * 50)

            # 关键修改：等待图片完全上传和处理完成，直到标题输入框出现
            logger.info("等待图片上传完成并出现标题输入框...")
            
            # 等待图片预览出现
            max_wait = 30  # 最多等待30秒
            start_time = asyncio.get_event_loop().time()
            
            preview_found = False
            while asyncio.get_event_loop().time() - start_time < max_wait:
                try:
                    # 检查图片预览
                    previews = await self.page.query_selector_all('img[class*="preview"], .image-item img')
                    if len(previews) >= len(images):
                        logger.info(f"✓ 检测到 {len(previews)} 张图片预览")
                        preview_found = True
                        break
                except:
                    pass
                await asyncio.sleep(1)
            
            if not preview_found:
                logger.warning("等待图片预览超时，但继续流程")
            
            # 额外等待，确保标题输入框完全加载
            await asyncio.sleep(3)
            
            await self.save_screenshot("2_after_upload.png")

            # 3. 现在图片已上传完成，填写标题和内容
            logger.info("=" * 50)
            logger.info("开始填写内容（图片已上传完成）")
            await self._fill_content(title, content, topics)
            logger.info("=" * 50)

            # 4. 添加话题（如果topics不为空，但已经在_fill_content中附加到正文中了）
            # 这里保留原逻辑，如果需要单独添加话题可以取消下面的注释
            # if topics:
            #     logger.info("=" * 50)
            #     logger.info("开始添加话题")
            #     await self._add_topics(topics)
            #     logger.info("=" * 50)

            # 5. 添加位置
            if location:
                logger.info("=" * 50)
                logger.info("开始添加位置")
                await self._add_location(location)
                logger.info("=" * 50)

            # 6. 发布
            await asyncio.sleep(2)
            await self.save_screenshot("3_before_publish.png")

            logger.info("=" * 50)
            logger.info("开始发布")
            result = await self._submit_post()
            logger.info("=" * 50)

            return result

        except Exception as e:
            logger.error(f"发布失败: {e}", exc_info=True)
            try:
                await self.save_screenshot("error_state.png")
            except:
                pass
            return {
                'success': False,
                'error': str(e),
                'code': 'publish_error'
            }

    async def check_login_status(self) -> bool:
        """
        检查登录状态 - 简化版本，现在主要被publish方法直接使用
        """
        try:
            logger.info("检查登录状态...")
            
            # 直接访问图片上传页面
            response = await self.page.goto(
                f"{self.base_url}/publish/publish?from=menu&target=image", 
                timeout=30000,
                wait_until='domcontentloaded'
            )
            
            if not response:
                logger.error("页面无响应")
                return False
                
            await asyncio.sleep(2)

            # 检查是否跳转到登录页
            current_url = self.page.url
            logger.info(f"当前URL: {current_url}")
            
            if 'login' in current_url.lower():
                logger.warning("未登录：跳转到登录页")
                return False

            # 检查是否有发布页的特征元素
            try:
                await self.page.wait_for_selector('button:has-text("上传图片")', timeout=5000)
                logger.info("✓ 已登录：检测到上传图片按钮")
                return True
            except:
                if 'publish' in current_url and 'login' not in current_url.lower():
                    logger.info("✓ 已登录：在发布页面")
                    return True
                else:
                    logger.warning("未登录：未检测到发布页面元素")
                    return False

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    async def _verify_image_upload_mode(self):
        """
        确认当前处于图片上传模式（替换原来的_ensure_upload_mode）
        """
        try:
            logger.info("确认当前是否为图片上传模式...")
            # 等待一下，让页面充分加载
            await asyncio.sleep(2)
            
            # 查找“上传图片”按钮（排除“上传视频”）
            buttons = await self.page.query_selector_all('button')
            found_image_upload = False
            video_buttons = []
            
            for btn in buttons:
                try:
                    text = await btn.text_content() or ''
                    if "上传图片" in text and "视频" not in text:
                        found_image_upload = True
                        logger.info("✓ 确认已处于图片上传模式（找到上传图片按钮）")
                        break
                    elif "上传视频" in text:
                        video_buttons.append(text)
                except:
                    continue
            
            if not found_image_upload:
                # 如果没找到上传图片按钮，但找到了上传视频按钮，说明还是在视频模式
                if video_buttons:
                    logger.warning(f"⚠️ 检测到上传视频按钮: {video_buttons}，但URL已指定target=image，可能页面加载异常")
                    await self.save_screenshot("debug_wrong_mode.png")
                else:
                    logger.info("未找到上传图片按钮，但URL已指定target=image，继续流程...")
                
        except Exception as e:
            logger.error(f"确认图片上传模式时出错: {e}")

        """确保在图文上传模式"""
        try:
            # 检查是否已有上传图片按钮
            upload_btn = await self.page.query_selector('button:has-text("上传图片")')
            
            if not upload_btn:
                logger.info("未找到上传图片按钮，尝试点击上传图文")
                
                # 点击"上传图文"按钮
                selectors = [
                    'button:has-text("上传图文")',
                    'div:has-text("上传图文")',
                    '.ant-menu-item:has-text("上传图文")',
                    '//*[contains(text(), "上传图文")]'
                ]
                
                for selector in selectors:
                    try:
                        if selector.startswith('//'):
                            element = await self.page.wait_for_selector(f'xpath={selector}', timeout=3000)
                        else:
                            element = await self.page.wait_for_selector(selector, timeout=3000)
                        
                        if element and await element.is_visible():
                            await element.click()
                            logger.info(f"✓ 点击了上传图文")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
            
            # 再次确认
            upload_btn = await self.page.query_selector('button:has-text("上传图片")')
            if upload_btn:
                logger.info("✓ 已进入图文上传模式")
            else:
                logger.warning("可能未进入图文上传模式")

        except Exception as e:
            logger.error(f"确保上传模式失败: {e}")


    async def _upload_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        上传图片 - 确保上传完成
        """
        try:
            logger.info(f"需要上传 {len(image_paths)} 张图片")

            # 1. 查找"上传图片"按钮
            upload_button = None
            text_selectors = [
                'button:has-text("上传图片")',
                '//button[contains(text(), "上传图片")]',
            ]
            
            for selector in text_selectors:
                try:
                    if selector.startswith('//'):
                        elements = await self.page.query_selector_all(f'xpath={selector}')
                    else:
                        elements = await self.page.query_selector_all(selector)
                    
                    for element in elements:
                        if await element.is_visible():
                            text = await element.text_content()
                            if text and "上传图片" in text and "视频" not in text:
                                upload_button = element
                                logger.info(f"✓ 找到上传图片按钮: '{text}'")
                                break
                    if upload_button:
                        break
                except:
                    continue
            
            if not upload_button:
                return {
                    'success': False,
                    'error': '未找到上传图片按钮',
                    'code': 'button_not_found'
                }

            # 2. 点击上传按钮
            logger.info("点击上传图片按钮...")
            await upload_button.click()
            await asyncio.sleep(3)

            # 3. 查找文件输入框
            file_input = await self.page.query_selector('input[type="file"]:visible')
            
            if not file_input:
                await asyncio.sleep(2)
                file_inputs = await self.page.query_selector_all('input[type="file"]')
                if file_inputs:
                    file_input = file_inputs[0]
                    logger.info(f"找到 {len(file_inputs)} 个文件输入框")

            if not file_input:
                return {
                    'success': False,
                    'error': '未找到文件上传输入框',
                    'code': 'file_input_not_found'
                }

            # 4. 上传所有图片 - 一次性设置所有文件
            valid_images = [img for img in image_paths if Path(img).exists()]

            if len(valid_images) == 0:
                return {
                    'success': False,
                    'error': '没有有效的图片文件',
                    'code': 'no_valid_images'
                }

            logger.info(f"一次性上传 {len(valid_images)} 张图片")

            try:
                # 一次性设置所有图片文件
                await file_input.set_input_files(valid_images)
                logger.info(f"✓ 已选择 {len(valid_images)} 个文件")

                # 等待上传和预览 - 根据图片数量调整等待时间
                base_wait = 5
                extra_wait = len(valid_images) * 2  # 每张图片额外等待2秒
                await asyncio.sleep(base_wait + extra_wait)

                # 检查上传进度 - 等待所有图片的预览显示
                preview_count = 0
                max_wait_rounds = 20 + len(valid_images) * 5  # 根据图片数量增加等待轮次
                for wait_round in range(max_wait_rounds):
                    try:
                        all_previews = []
                        for selector in ['img[class*="preview"]', '.image-item img', '.upload-list img', '.pic-preview img']:
                            previews = await self.page.query_selector_all(selector)
                            all_previews.extend(previews)

                        unique_previews = list(set(all_previews))
                        preview_count = len(unique_previews)

                        logger.info(f"第{wait_round+1}次检查: 已显示 {preview_count} 张图片预览")

                        if preview_count >= len(valid_images):
                            logger.info(f"✓ 所有 {preview_count} 张图片上传完成")
                            break

                    except Exception as e:
                        logger.debug(f"检查预览时出错: {e}")

                    await asyncio.sleep(1)

                logger.info(f"✓ 图片上传完成，显示 {preview_count} 张预览")

            except Exception as e:
                logger.error(f"上传图片失败: {e}")
                return {
                    'success': False,
                    'error': f'上传图片失败: {str(e)}',
                    'code': 'upload_failed'
                }

            # 等待所有图片处理完成
            await asyncio.sleep(3)
            
            # 验证上传结果
            try:
                all_previews = []
                for selector in ['img[class*="preview"]', '.image-item img', '.upload-list img']:
                    previews = await self.page.query_selector_all(selector)
                    all_previews.extend(previews)
                
                unique_previews = list(set(all_previews))
                logger.info(f"✓ 当前页面显示 {len(unique_previews)} 张图片预览")
                
                # 关键：返回预览数量，让publish方法知道上传状态
                return {
                    'success': True,
                    'preview_count': len(unique_previews)
                }
                
            except Exception as e:
                logger.warning(f"验证上传结果时出错: {e}")
                return {'success': True}

        except Exception as e:
            logger.error(f"上传图片失败: {e}", exc_info=True)
            await self.save_screenshot("upload_error.png")
            return {
                'success': False,
                'error': f'图片上传失败: {str(e)}',
                'code': 'upload_error'
            }

 
    async def _fill_content(self, title: str, content: str, topics: Optional[List[str]] = None):
        """填写标题和内容 - 修复clear方法错误"""
        try:
            logger.info("等待标题和内容输入框出现...")
            await asyncio.sleep(3)

            # 1. 填写标题
            logger.info("开始查找标题输入框...")

            # 方法1: 通过精确的placeholder查找
            title_input = None
            try:
                title_input = await self.page.wait_for_selector(
                    'input[placeholder="填写标题会有更多赞哦"]',
                    timeout=5000
                )
                if title_input and await title_input.is_visible():
                    logger.info("✓ 通过placeholder找到标题框")
            except:
                logger.debug("通过placeholder查找失败")

            # 填写标题 - 修复clear方法
            if title_input:
                try:
                    # 点击输入框
                    await title_input.click()
                    await asyncio.sleep(0.5)

                    # 方法1: 使用fill直接覆盖（不需要先clear）
                    await title_input.fill(title)
                    logger.info(f"✓ 标题已填写: '{title[:30]}...'")

                    # 验证是否填写成功
                    filled_value = await title_input.input_value()
                    logger.info(f"   验证: 输入框值 '{filled_value[:30]}...'")
                except Exception as e:
                    logger.error(f"填写标题时出错: {e}")
                    # 备用方法：使用press_sequentially
                    try:
                        await title_input.click()
                        await asyncio.sleep(0.5)
                        # 全选后删除
                        await title_input.press("Control+A")
                        await asyncio.sleep(0.2)
                        await title_input.press("Backspace")
                        await asyncio.sleep(0.2)
                        # 输入新内容
                        await title_input.type(title, delay=50)
                        logger.info(f"✓ 使用备用方法填写标题成功")
                    except:
                        pass
            else:
                logger.error("❌ 找不到标题输入框")

            # 2. 填写正文
            logger.info("开始查找正文输入框...")
            content_selectors = [
                'div.tiptap.ProseMirror[contenteditable="true"]',
                'div.ProseMirror[contenteditable="true"]',
                'div[contenteditable="true"]',
                '.ProseMirror',
            ]

            content_div = None
            for selector in content_selectors:
                try:
                    content_div = await self.page.wait_for_selector(selector, timeout=3000)
                    if content_div and await content_div.is_visible():
                        logger.info(f"✓ 通过选择器 '{selector}' 找到正文框")
                        break
                except:
                    continue

            # 如果有标签，将标签附加到正文后面
            final_content = content
            if topics:
                tags_line = '\n\n' + ' '.join([f'#{tag}' for tag in topics])
                final_content = content + tags_line
                logger.info(f"标签将附加到正文: {tags_line}")
                logger.info(f"完整正文长度: {len(final_content)}, 标签数: {len(topics)}")
            else:
                logger.warning("没有标签需要附加到正文")

            if content_div:
                try:
                    await content_div.click()
                    await asyncio.sleep(0.5)

                    # 对于contenteditable的div，需要清空内容
                    await content_div.evaluate('el => el.innerHTML = ""')
                    await asyncio.sleep(0.5)

                    # 先输入正文内容
                    await content_div.type(content, delay=50)
                    await asyncio.sleep(0.5)
                    
                    # 如果有标签，逐个输入标签
                    if topics:
                        logger.info(f"开始逐个输入标签，共{len(topics)}个")
                        
                        # 先输入两个换行
                        await content_div.type('\n\n', delay=50)
                        await asyncio.sleep(0.5)
                        
                        # 逐个输入标签
                        for i, tag in enumerate(topics):
                            # 输入#和标签名
                            await content_div.type(f'#{tag}', delay=50)
                            await asyncio.sleep(1)
                            
                            # 等待并检查是否有标签选项弹出
                            try:
                                # 检查是否有标签选项弹出
                                tag_options = await self.page.query_selector('.topic-suggestions, .tag-suggestions, [class*="suggestion"], [class*="dropdown"]')
                                if tag_options and await tag_options.is_visible():
                                    logger.info(f"检测到标签选项弹出，选择第一个选项")
                                    
                                    # 尝试点击第一个选项
                                    try:
                                        first_option = await self.page.query_selector('.topic-suggestions > div:first-child, .tag-suggestions > div:first-child, [class*="suggestion"] > div:first-child, [class*="dropdown"] > div:first-child')
                                        if first_option and await first_option.is_visible():
                                            await first_option.click()
                                            await asyncio.sleep(0.5)
                                            logger.info(f"✓ 已选择标签选项")
                                        else:
                                            # 如果找不到第一个选项，按ESC关闭
                                            logger.info(f"未找到第一个选项，按ESC关闭")
                                            await self.page.keyboard.press('Escape')
                                            await asyncio.sleep(0.5)
                                    except:
                                        # 如果点击失败，按ESC关闭
                                        logger.info(f"点击选项失败，按ESC关闭")
                                        await self.page.keyboard.press('Escape')
                                        await asyncio.sleep(0.5)
                            except Exception as e:
                                logger.warning(f"处理标签选项时出错: {e}")
                            
                            # 如果不是最后一个标签，输入空格
                            if i < len(topics) - 1:
                                logger.info(f"输入空格分隔符")
                                await content_div.type(' ', delay=30)
                                await asyncio.sleep(0.5)
                            else:
                                # 最后一个标签，模拟一个空标签来触发选中
                                logger.info(f"最后一个标签，模拟空标签来触发选中")
                                await content_div.type(' #', delay=30)
                                await asyncio.sleep(0.5)
                                
                                # 等待并检查是否有标签选项弹出
                                try:
                                    tag_options = await self.page.query_selector('.topic-suggestions, .tag-suggestions, [class*="suggestion"], [class*="dropdown"]')
                                    if tag_options and await tag_options.is_visible():
                                        logger.info(f"检测到空标签选项弹出，按ESC关闭")
                                        await self.page.keyboard.press('Escape')
                                        await asyncio.sleep(0.5)
                                except:
                                    pass
                                
                                # 删除模拟的空标签
                                await self.page.keyboard.press('Backspace')
                                await self.page.keyboard.press('Backspace')
                                await asyncio.sleep(0.5)
                                logger.info(f"✓ 已删除模拟的空标签")
                        
                        logger.info(f"✓ 所有标签已输入")
                    
                    logger.info(f"✓ 正文已填写: {final_content[:50]}...")
                except Exception as e:
                    logger.error(f"填写正文时出错: {e}")
            else:
                logger.warning("未找到正文输入框")

        except Exception as e:
            logger.error(f"填写内容失败: {e}", exc_info=True)


    async def _add_topics(self, topics: List[str]):
        """添加话题 - 根据你看到的实际结构"""
        try:
            # 从日志看到，正文里已经有一个 "#佛学"，说明话题可能直接在正文输入
            # 所以这个方法可能不需要了，或者需要调整
            logger.info("话题可能直接在正文中输入，跳过单独添加话题步骤")
            
            # 单独添加话题
            for topic in topics:
                # 查找话题输入框
                topic_selectors = [
                    'input[placeholder*="话题"]',
                    'input[placeholder*="#"]',
                    '.topic-input'
                ]
                
                for selector in topic_selectors:
                    try:
                        topic_input = await self.page.wait_for_selector(selector, timeout=3000)
                        if topic_input and await topic_input.is_visible():
                            await topic_input.fill(f"#{topic}")
                            await asyncio.sleep(1)
                            await topic_input.press('Enter')
                            logger.info(f"✓ 添加话题: {topic}")
                            await asyncio.sleep(1)
                            break
                    except:
                        continue

        except Exception as e:
            logger.error(f"添加话题失败: {e}")

    async def _add_location(self, location: str):
        """添加位置"""
        try:
            # 查找位置按钮
            location_selectors = [
                'button:has-text("位置")',
                '.location-button',
                '[class*="location"]'
            ]
            
            for selector in location_selectors:
                try:
                    location_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if location_btn and await location_btn.is_visible():
                        await location_btn.click()
                        await asyncio.sleep(1)
                        
                        # 输入位置
                        search_input = await self.page.wait_for_selector(
                            'input[placeholder*="搜索"]', 
                            timeout=5000
                        )
                        if search_input:
                            await search_input.fill(location)
                            await asyncio.sleep(1)
                            
                            # 选择第一个结果
                            first_result = await self.page.wait_for_selector(
                                '.location-item, .ant-select-item', 
                                timeout=3000
                            )
                            if first_result:
                                await first_result.click()
                                logger.info(f"✓ 添加位置: {location}")
                        break
                except:
                    continue

        except Exception as e:
            logger.error(f"添加位置失败: {e}")

    async def _submit_post(self) -> Dict[str, Any]:
        """提交发布"""
        try:
            # 查找发布按钮
            publish_selectors = [
                'button:has-text("发布")',
                'button:has-text("立即发布")',
                '.publish-btn',
                'button[class*="publish"]',
                '.ant-btn-primary:has-text("发布")',
            ]

            publish_btn = None
            for selector in publish_selectors:
                try:
                    publish_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if publish_btn and await publish_btn.is_visible():
                        # 检查是否可用
                        is_disabled = await publish_btn.get_attribute('disabled')
                        is_disabled_class = await publish_btn.get_attribute('class')
                        if not is_disabled and 'disabled' not in (is_disabled_class or ''):
                            logger.info(f"✓ 找到可用的发布按钮: {selector}")
                            break
                except:
                    continue

            if not publish_btn:
                return {
                    'success': False,
                    'error': '未找到可用的发布按钮',
                    'code': 'button_not_found'
                }

            # 记录发布前的URL
            before_url = self.page.url

            # 点击发布
            logger.info("点击发布按钮...")
            await publish_btn.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            
            # 点击发布按钮
            logger.info("执行点击操作...")
            try:
                await publish_btn.click(timeout=10000)  # 点击操作设置10秒超时
                logger.info("✓ 点击操作完成")
            except Exception as e:
                logger.warning(f"点击操作超时或失败: {e}")
                # 尝试使用JavaScript点击
                logger.info("尝试使用JavaScript点击...")
                await self.page.evaluate('(btn) => btn.click()', publish_btn)
                logger.info("✓ JavaScript点击完成")
            
            # 等待可能的确认对话框
            logger.info("等待页面响应...")
            await asyncio.sleep(3)
            
            # 检查是否有确认对话框
            confirm_selectors = [
                'button:has-text("确认")',
                'button:has-text("确定")',
                'button:has-text("立即发布")',
                '.ant-modal-confirm-btns button:has-text("确定")',
                '.ant-btn-primary:has-text("确认")',
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = await self.page.query_selector(selector)
                    if confirm_btn and await confirm_btn.is_visible():
                        logger.info(f"✓ 检测到确认对话框，点击确认按钮: {selector}")
                        await confirm_btn.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            # 等待发布结果 - 增加等待时间和检测逻辑
            logger.info("等待发布结果...")
            max_wait = 60  # 增加到60秒以支持多图处理
            for i in range(max_wait):
                await asyncio.sleep(1)
                
                # 每5秒打印一次状态
                if (i + 1) % 5 == 0:
                    current_url = self.page.url
                    logger.info(f"等待发布结果... {i+1}/{max_wait}秒, 当前URL: {current_url}")
                else:
                    logger.debug(f"等待发布结果... {i+1}/{max_wait}秒")

                # 1. 检查成功消息（多种可能的选择器）
                success_indicators = [
                    '.ant-message-success',
                    '.ant-notification-notice-success',
                    'div:has-text("发布成功")',
                    'div:has-text("笔记已发布")',
                    'span:has-text("发布成功")',
                    '[class*="success"]',
                ]

                for indicator in success_indicators:
                    try:
                        element = await self.page.query_selector(indicator)
                        if element:
                            text = await element.text_content()
                            if text and ('成功' in text or 'success' in text.lower()):
                                logger.info(f"✓ 检测到发布成功: {text}")

                                # 获取笔记链接
                                note_url = None
                                try:
                                    # 尝试多个选择器获取链接
                                    link_selectors = [
                                        'a:has-text("查看笔记")',
                                        'a:has-text("查看")',
                                        '.ant-notification-notice a',
                                        '[class*="success"] a',
                                    ]
                                    for link_sel in link_selectors:
                                        view_link = await self.page.query_selector(link_sel)
                                        if view_link:
                                            note_url = await view_link.get_attribute('href')
                                            if note_url:
                                                break
                                except:
                                    pass

                                return {
                                    'success': True,
                                    'message': '发布成功',
                                    'url': note_url or self.page.url,
                                    'detection_method': 'success_message'
                                }
                    except:
                        continue

                # 2. 检查是否跳转到笔记详情页
                current_url = self.page.url
                if current_url != before_url:
                    if '/note/' in current_url or '/post/' in current_url or 'publish' not in current_url:
                        logger.info(f"✓ 检测到页面跳转，发布成功: {current_url}")
                        return {
                            'success': True,
                            'message': '发布成功',
                            'url': current_url,
                            'detection_method': 'url_change'
                        }

                # 3. 检查是否还在发布页且URL变化（可能跳转到管理页）
                if current_url != before_url and 'creator' in current_url:
                    logger.info(f"✓ 检测到页面跳转到创作者中心: {current_url}")
                    return {
                        'success': True,
                        'message': '发布成功',
                        'url': current_url,
                        'detection_method': 'creator_page'
                    }

            # 4. 检查错误消息
            error_indicators = [
                '.ant-message-error',
                '.ant-notification-notice-error',
                'div:has-text("发布失败")',
                'div:has-text("失败")',
                '[class*="error"]',
            ]

            for indicator in error_indicators:
                try:
                    error = await self.page.query_selector(indicator)
                    if error:
                        text = await error.text_content()
                        if text:
                            logger.error(f"检测到发布错误: {text}")
                            return {
                                'success': False,
                                'error': f'发布失败: {text}',
                                'code': 'publish_failed'
                            }
                except:
                    continue

            # 5. 最终检查：如果按钮状态变为disabled或文本改变
            try:
                btn_text = await publish_btn.text_content()
                btn_disabled = await publish_btn.get_attribute('disabled')
                if btn_disabled or '发布中' in btn_text or 'loading' in btn_text.lower():
                    # 可能正在处理中，但无法确定结果
                    await self.save_screenshot("publish_processing.png")
                    return {
                        'success': False,
                        'error': '发布处理中，无法确认结果',
                        'code': 'processing',
                        'url': self.page.url
                    }
            except:
                pass

            # 状态未知 - 保存截图供人工检查
            await self.save_screenshot("publish_result_unknown.png")
            logger.warning("无法确定发布结果，已保存截图")
            return {
                'success': False,
                'error': '发布状态未知，请人工检查截图确认',
                'code': 'unknown',
                'screenshot': 'publish_result_unknown.png'
            }

        except Exception as e:
            logger.error(f"提交发布失败: {e}", exc_info=True)
            try:
                await self.save_screenshot("publish_error.png")
            except:
                pass
            return {
                'success': False,
                'error': f'提交失败: {str(e)}',
                'code': 'submit_error'
            }

    async def _debug_buttons(self):
        """调试按钮 - 打印所有按钮信息"""
        try:
            logger.info("=" * 50)
            logger.info("调试所有按钮:")
            
            buttons = await self.page.query_selector_all('button')
            logger.info(f"找到 {len(buttons)} 个按钮:")
            
            for i, btn in enumerate(buttons):
                try:
                    text = await btn.text_content() or ''
                    classes = await btn.get_attribute('class') or ''
                    html = await btn.evaluate('el => el.outerHTML')
                    visible = await btn.is_visible()
                    
                    logger.info(f"按钮 {i+1}:")
                    logger.info(f"  text: '{text}'")
                    logger.info(f"  class: '{classes[:50]}'")
                    logger.info(f"  visible: {visible}")
                    logger.info(f"  html: {html[:100]}...")
                    
                    if "上传图片" in text or "upload" in classes.lower():
                        logger.info(f"  ⭐ 这是目标按钮！")
                    
                except Exception as e:
                    logger.error(f"分析按钮 {i+1} 失败: {e}")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"调试按钮失败: {e}")

    async def save_screenshot(self, path: str):
        """保存截图"""
        if self.page and not self.page.is_closed():
            try:
                await self.page.screenshot(path=path, full_page=True)
                logger.info(f"📸 截图已保存: {path}")
            except Exception as e:
                logger.error(f"保存截图失败: {e}")

    async def debug_page(self):
        """完整的页面调试"""
        try:
            if self.page.is_closed():
                logger.error("页面已关闭，无法调试")
                return
                
            logger.info("\n" + "="*60)
            logger.info("🔍 开始完整页面调试")
            logger.info("="*60)
            
            # 当前URL
            url = self.page.url
            logger.info(f"📌 URL: {url}")
            
            # 页面标题
            title = await self.page.title()
            logger.info(f"📌 标题: {title}")
            
            # 调试所有按钮
            await self._debug_buttons()
            
            # 查找所有输入框
            inputs = await self.page.query_selector_all('input, textarea, [contenteditable="true"]')
            logger.info(f"\n📝 找到 {len(inputs)} 个输入框:")
            for i, inp in enumerate(inputs[:10]):
                try:
                    tag = await inp.evaluate('el => el.tagName')
                    placeholder = await inp.get_attribute('placeholder') or ''
                    classes = await inp.get_attribute('class') or ''
                    logger.info(f"  [{i+1}] {tag} placeholder='{placeholder}' class='{classes[:30]}'")
                except:
                    pass
            
            # 保存完整HTML
            html = await self.page.content()
            with open('page_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info("\n💾 已保存: page_debug.html")
            
            # 保存截图
            await self.save_screenshot("debug_page.png")
            
            logger.info("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"调试失败: {e}")

    async def close(self):
        """关闭浏览器"""
        try:
            self._closed = True
            logger.info("开始关闭浏览器...")
            
            if self.page and not self.page.is_closed():
                await self.page.close()
                logger.info("✓ 页面已关闭")
            
            if self.context:
                # 清除所有cookie
                await self.context.clear_cookies()
                logger.info("✓ 已清除所有cookie")
                
                await self.context.close()
                logger.info("✓ Context已关闭")
            
            if self.browser:
                await self.browser.close()
                logger.info("✓ 浏览器已关闭")
            
            if self.playwright:
                await self.playwright.stop()
                logger.info("✓ Playwright已停止")
            
            logger.info("✓ 浏览器已完全关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")


# 便捷函数
async def publish_to_xiaohongshu(
    title: str,
    content: str,
    images: List[str],
    cookie: Optional[str] = None,
    headless: bool = False,
    topics: Optional[List[str]] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：发布到小红书
    """
    publisher = XiaohongshuPublisher()
    
    try:
        # 初始化
        await publisher.initialize(cookie_str=cookie, headless=headless)
        
        # 发布
        result = await publisher.publish(
            title=title,
            content=content,
            images=images,
            topics=topics,
            location=location
        )
        
        return result
        
    finally:
        await publisher.close()