from __future__ import annotations

from aitest.case_parser import CaseDocument


def build_gen_prompt(doc: CaseDocument) -> str:
    steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(doc.steps))
    asserts = "\n".join(f"- {a}" for a in doc.asserts)
    return f"""你是一个测试代码生成器。根据以下用例，输出**一个完整**的 Python 源文件内容（不要 markdown 代码围栏，不要解释）。

硬性要求：
1. 使用 pytest 作为测试框架；使用 `from playwright.sync_api import Page, expect`；测试函数签名为 `def test_{doc.id}(page: Page):`（pytest-playwright 注入的 `page`）。
2. 测试函数名必须为：test_{doc.id}
3. 文件顶部必须包含如下注释块（原样包含 case_id 与 source）：
# --- AITEST_META begin
# case_id: {doc.id}
# source: {doc.source_path}
# --- AITEST_META end
4. 被测起始 URL 使用：{doc.target}
5. 设备场景：{doc.device}（若为 mobile，请使用移动视口；若 target 为 www.baidu.com 且 headless 下 PC 搜索框不可见，可改用 https://m.baidu.com/ 并选用可见的 `#index-kw` / `#index-bn` 等移动端主站选择器）。
6. **禁止**使用：subprocess、os.system、Python 内置的 `eval()` / `exec()` / `compile()`（**允许** `re.compile()`）、socket、urllib.request、requests、httpx（被测页面导航除外请只用 page.goto）。
7. **禁止**在生成的代码中硬编码真实密码；若需要登录，从 os.environ 读取 TEST_USERNAME / TEST_PASSWORD。
8. 使用稳定的定位方式：优先 get_by_role、get_by_placeholder、get_by_label、get_by_text；避免脆弱的长 xpath。
9. 页面标题断言不要用与短字符串完全相等（文档站常为「章节 | 站点名」），请用正则 `expect(page).to_have_title(re.compile(...))`。
10. 外链说明类断言优先用 `href` 包含关键域名（如 `a[href*="iana.org"]`），少用依赖英文省略号的 link name。
11. 搜索类结果页**不要**断言固定条数（如 `to_have_count(3)`），只断言可见性与关键词。
12. 每个关键步骤可加简短注释。

用例标题：{doc.title}

步骤：
{steps}

断言要求：
{asserts}

只输出 Python 源码，从第一个 import 或注释开始直到文件末尾。"""


def build_heal_prompt(
    *,
    case_id: str,
    generated_py: str,
    failure_log: str,
) -> str:
    return f"""你是一个 Playwright+pytest 测试修复助手。下面是一份失败的测试代码与 pytest 失败摘要。
请输出**仅** unified diff（git diff 格式），使其能修复失败。不要 markdown，不要解释文字。

case_id: {case_id}

--- 当前 tests/generated 文件内容 ---
{generated_py}

--- 失败摘要 ---
{failure_log}

要求：
1. diff 以 --- a/ 与 +++ b/ 开头，路径使用 tests/generated/test_{case_id}.py（与单文件一致）。
2. 仍遵守：生成代码中不得出现 subprocess、eval、exec。
3. 若失败是选择器问题，优先改为 get_by_role / get_by_text 等。
只输出 diff 正文。"""
