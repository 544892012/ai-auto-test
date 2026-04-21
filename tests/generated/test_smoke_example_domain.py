# --- AITEST_META begin
# case_id: smoke_example_domain
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/smoke_example_domain.md
# --- AITEST_META end

from playwright.sync_api import Page, expect


def test_smoke_example_domain(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("https://example.com/")
    page.wait_for_load_state("domcontentloaded")

    main_heading = page.get_by_role("heading", level=1)
    expect(main_heading).to_be_visible()
    expect(main_heading).to_have_text("Example Domain")
    expect(page).to_have_title("Example Domain")

    # 文案随地区/版本可能变化，用 href 关联 IANA 更稳
    iana_link = page.locator('a[href*="iana.org"]')
    expect(iana_link.first).to_be_visible()
