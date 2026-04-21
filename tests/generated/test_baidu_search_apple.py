# --- AITEST_META begin
# case_id: baidu_search_apple
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/example_baidu.md
# --- AITEST_META end

import re

from playwright.sync_api import Page, expect


def test_baidu_search_apple(page: Page) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("https://m.baidu.com/")
    page.wait_for_load_state("domcontentloaded")

    page.locator("#index-kw").fill("苹果", timeout=30_000)
    page.locator("#index-bn").click()
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title(re.compile(r"苹果|百度"), timeout=30_000)
    expect(page.get_by_text("苹果", exact=False).first).to_be_visible(timeout=30_000)
