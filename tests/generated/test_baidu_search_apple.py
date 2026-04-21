# --- AITEST_META begin
# case_id: baidu_search_apple
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/example_baidu.md
# --- AITEST_META end

import os
from playwright.sync_api import sync_playwright, Page, expect


def test_baidu_search_apple():
    with sync_playwright() as p:
        # 使用移动设备视口
        device = p.devices['iPhone 12']
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**device)
        page = context.new_page()

        try:
            # 步骤1: 打开移动端百度首页
            page.goto("https://m.baidu.com/")
            # 等待页面主要内容加载
            page.wait_for_load_state("networkidle")

            # 步骤2: 在搜索框输入「苹果」
            # 使用移动端搜索框选择器
            search_box = page.locator("#index-kw")
            search_box.fill("苹果")

            # 步骤3: 点击搜索按钮
            search_button = page.locator("#index-bn")
            search_button.click()

            # 等待搜索结果加载
            page.wait_for_load_state("networkidle")

            # 断言: 结果区域可见且包含与搜索相关的结果
            # 检查搜索结果容器可见
            results_container = page.locator("#results")
            expect(results_container).to_be_visible()

            # 检查页面包含多条搜索结果（通过检查结果项）
            result_items = page.locator(".c-container")
            expect(result_items.first).to_be_visible()
            # 验证至少存在多个结果项
            assert result_items.count() > 1, "搜索结果应包含多条结果"

            # 检查页面内容包含搜索关键词「苹果」
            page_content = page.content()
            assert "苹果" in page_content, "搜索结果应包含搜索关键词'苹果'"

        finally:
            context.close()
            browser.close()
