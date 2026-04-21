# --- AITEST_META begin
# case_id: mobile_baidu_search_orange
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/mobile_baidu_search_orange.md
# --- AITEST_META end

import re

from playwright.sync_api import Page, expect


def test_mobile_baidu_search_orange(page: Page) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("https://m.baidu.com/")
    page.wait_for_load_state("domcontentloaded")

    page.locator("#index-kw").fill("橙子", timeout=30_000)
    page.locator("#index-bn").click()
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title(re.compile(r"橙子|百度"), timeout=30_000)
    body = page.locator("body")
    expect(body).to_contain_text(re.compile(r"橙子|百度"), timeout=30_000)
