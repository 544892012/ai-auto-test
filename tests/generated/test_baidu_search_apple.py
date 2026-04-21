# --- AITEST_META begin
# case_id: baidu_search_apple
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/example_baidu.md
# --- AITEST_META end

import re
import os
from playwright.sync_api import Page, expect


def test_baidu_search_apple(page: Page):
    # 设置移动视口
    page.set_viewport_size({"width": 375, "height": 667})
    
    # 步骤1: 打开移动端百度首页
    page.goto("https://m.baidu.com/")
    
    # 步骤2: 在搜索框输入「苹果」
    # 使用移动端搜索框选择器
    search_input = page.locator("#index-kw")
    search_input.fill("苹果")
    
    # 步骤3: 点击搜索按钮
    # 使用移动端搜索按钮选择器
    search_button = page.locator("#index-bn")
    search_button.click()
    
    # 等待搜索结果加载
    page.wait_for_load_state("networkidle")
    
    # 断言: 结果区域可见且包含与搜索相关的结果
    # 检查搜索结果容器可见
    results_container = page.locator(".c-container")
    expect(results_container.first).to_be_visible()
    
    # 断言页面包含多条搜索结果
    results_count = page.locator(".c-container").count()
    assert results_count >= 3, f"搜索结果少于3条，实际找到{results_count}条"
    
    # 断言至少一个结果包含「苹果」关键词
    # 获取所有结果文本内容
    all_results_text = ""
    for i in range(min(5, results_count)):
        result_text = page.locator(".c-container").nth(i).text_content()
        all_results_text += result_text or ""
    
    # 检查是否包含搜索关键词
    assert "苹果" in all_results_text, "搜索结果中未找到'苹果'关键词"
