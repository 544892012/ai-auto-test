# --- AITEST_META begin
# case_id: mobile_baidu_search_orange
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/mobile_baidu_search_orange.md
# --- AITEST_META end

import os
import pytest
from playwright.sync_api import sync_playwright, Page, expect


def test_mobile_baidu_search_orange():
    with sync_playwright() as p:
        # 启动移动端浏览器上下文
        browser = p.chromium.launch(headless=True)
        # 设置移动设备视口
        context = browser.new_context(viewport={"width": 375, "height": 667})
        page = context.new_page()

        try:
            # 1. 打开 m 站首页
            page.goto("https://m.baidu.com/")
            # 等待页面主要内容加载
            page.wait_for_load_state("networkidle")

            # 2. 在搜索框输入「橙子」
            # 使用移动端搜索框选择器
            search_input = page.locator("#index-kw")
            search_input.fill("橙子")

            # 3. 点击搜索按钮发起检索
            search_button = page.locator("#index-bn")
            search_button.click()

            # 等待结果页加载
            page.wait_for_load_state("networkidle")

            # 断言：结果页标题或正文可见且与「橙子」或「百度」相关
            # 检查页面标题包含"橙子"或"百度"
            title = page.title()
            assert "橙子" in title or "百度" in title, f"页面标题'{title}'未包含'橙子'或'百度'"

            # 检查页面正文可见且包含相关文本
            # 查找结果页主要内容区域
            content = page.locator("body")
            expect(content).to_be_visible()
            # 检查页面是否包含搜索关键词或百度标识
            page_text = content.inner_text()
            assert "橙子" in page_text or "百度" in page_text, "结果页未找到'橙子'或'百度'相关内容"

        finally:
            # 关闭浏览器
            context.close()
            browser.close()
