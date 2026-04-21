# --- AITEST_META begin
# case_id: form_httpbin_post
# source: /Users/wenchao.zeng/work/codes/ai-auto-test/cases/form_httpbin_post.md
# --- AITEST_META end

from playwright.sync_api import Page, expect


def test_form_httpbin_post(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto("https://httpbin.org/forms/post")
    page.wait_for_load_state("domcontentloaded")

    page.get_by_label("Customer name").fill("AITest")
    page.get_by_label("Telephone").fill("13800138000")
    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url("https://httpbin.org/post", timeout=30_000)
    expect(page.locator("body")).to_contain_text("AITest")
    expect(page.locator("body")).to_contain_text("13800138000")
