"""
内容分割器 - 智能分割长文为多张卡片
"""

from typing import List, Tuple
import re


class ContentSplitter:
    """内容分割器 - 智能分割长文"""

    def __init__(self):
        pass

    def split_by_paragraph(
        self,
        content: str,
        max_length: int,
        preserve_endings: bool = True,
    ) -> List[str]:
        """
        按段落分割内容

        策略：
        1. 保持段落完整性
        2. 标题独立成段
        3. 控制每张卡片字数

        Args:
            content: 原始内容
            max_length: 单张最大字数
            preserve_endings: 是否保留段落标记

        Returns:
            分割后的页面列表
        """
        if not content:
            return []

        # 如果内容总长度不超过限制，直接返回
        if len(content) <= max_length:
            return [content]

        # 按段落分割（保持语义完整性）
        paragraphs = self._split_into_paragraphs(content)

        pages = []
        current_page = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)

            # 如果单个段落就超过限制，需要强制分割
            if para_length > max_length:
                # 先保存当前页面
                if current_page:
                    pages.append("\n\n".join(current_page))
                    current_page = []
                    current_length = 0

                # 强制分割超长段落
                sub_paras = self._force_split_paragraph(para, max_length)
                for i, sub_para in enumerate(sub_paras):
                    if current_length + len(sub_para) > max_length:
                        if current_page:
                            pages.append("\n\n".join(current_page))
                        current_page = [sub_para]
                        current_length = len(sub_para)
                    else:
                        current_page.append(sub_para)
                        current_length += len(sub_para) + 2

            elif current_length + para_length + 2 > max_length:
                # 当前页面已满，保存并开始新页面
                if current_page:
                    pages.append("\n\n".join(current_page))
                current_page = [para]
                current_length = para_length
            else:
                # 添加到当前页面
                current_page.append(para)
                current_length += para_length + 2  # +2 for "\n\n"

        # 保存最后一页
        if current_page:
            pages.append("\n\n".join(current_page))

        return pages

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        将内容分割为段落

        Args:
            content: 原始内容

        Returns:
            段落列表
        """
        # 按双换行符分割段落
        paragraphs = content.split("\n\n")

        # 清理每个段落的首尾空格
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _force_split_paragraph(self, paragraph: str, max_length: int) -> List[str]:
        """
        强制分割超长段落

        策略：按句子分割，保持句子完整性

        Args:
            paragraph: 超长段落
            max_length: 最大长度

        Returns:
            分割后的段落列表
        """
        # 按句子分割（中文和英文句号、问号、感叹号）
        sentences = re.split(r"([。！？.!?])", paragraph)

        # 重新组合句子和标点
        sentence_list = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if sentence.strip():
                sentence_list.append(sentence.strip())

        # 处理剩余部分
        if len(sentences) % 2 == 1:
            remaining = sentences[-1].strip()
            if remaining:
                sentence_list.append(remaining)

        # 按句子组装页面
        pages = []
        current_page = ""
        current_length = 0

        for sentence in sentence_list:
            sentence_length = len(sentence)

            if current_length + sentence_length > max_length:
                if current_page:
                    pages.append(current_page)

                # 如果单个句子还是太长，按字符强制分割
                if sentence_length > max_length:
                    char_chunks = [sentence[i:i + max_length] for i in range(0, len(sentence), max_length)]
                    pages.extend(char_chunks[:-1])
                    current_page = char_chunks[-1]
                    current_length = len(current_page)
                else:
                    current_page = sentence
                    current_length = sentence_length
            else:
                current_page += sentence
                current_length += sentence_length

        if current_page:
            pages.append(current_page)

        return pages

    def split_with_continuation(
        self,
        content: str,
        max_length: int,
        title: str = "",
    ) -> List[Tuple[str, str]]:
        """
        分割内容并添加续接标记

        Args:
            content: 原始内容
            max_length: 最大长度
            title: 标题

        Returns:
            [(内容, 标题), ...] 列表
        """
        pages = self.split_by_paragraph(content, max_length)

        result = []
        total_pages = len(pages)

        for i, page in enumerate(pages):
            # 第一页显示原标题
            if i == 0:
                page_title = title
            # 后续页面添加"（续）"标记
            else:
                page_title = f"{title}（{i}/{total_pages - 1}）" if total_pages > 2 else f"{title}（续）"

            result.append((page, page_title))

        return result
