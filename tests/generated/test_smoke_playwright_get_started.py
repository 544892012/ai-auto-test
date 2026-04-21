# --- AITEST_META begin
# case_id: smoke_playwright_get_started
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/smoke_playwright_get_started.md
# --- AITEST_META end

import re

from playwright.sync_api import Page, expect


def test_smoke_playwright_get_started(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("https://playwright.dev/python/docs/intro")
    page.wait_for_load_state("networkidle")

    # 文档站标题常见为「Installation | Playwright Python」，勿与固定短标题相等断言
    expect(page).to_have_title(re.compile(r"Playwright", re.IGNORECASE))

    main_heading = page.get_by_role("heading", name=re.compile(r"Installation|安装", re.IGNORECASE))
    expect(main_heading.first).to_be_visible(timeout=30_000)

    expect(page.get_by_text("Playwright", exact=False).first).to_be_visible()
