# --- AITEST_META begin
# case_id: form_httpbin_post
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/form_httpbin_post.md
# --- AITEST_META end

import os
import pytest
from playwright.sync_api import sync_playwright, Page, expect


def test_form_httpbin_post():
    with sync_playwright() as p:
        # 启动浏览器，使用 desktop 场景
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        try:
            # 步骤1: 打开 target 表单页
            page.goto("https://httpbin.org/forms/post")
            
            # 步骤2: 在 Customer name 输入框中输入 "AITest"
            # 使用 get_by_label 定位姓名输入框
            page.get_by_label("Customer name").fill("AITest")
            
            # 步骤3: 在 Telephone 输入框中输入 "13800138000"
            # 使用 get_by_label 定位电话输入框
            page.get_by_label("Telephone").fill("13800138000")
            
            # 步骤4: 点击 Submit 提交按钮
            # 使用 get_by_role 定位提交按钮
            page.get_by_role("button", name="Submit").click()
            
            # 断言: 提交后页面内容体现已进入处理结果页
            # 等待导航完成并检查页面包含表单字段回显
            expect(page).to_have_url("https://httpbin.org/post")
            # 检查响应页面包含提交的姓名和电话字段
            expect(page.locator("body")).to_contain_text("AITest")
            expect(page.locator("body")).to_contain_text("13800138000")
            
        finally:
            # 关闭浏览器上下文
            context.close()
            browser.close()
