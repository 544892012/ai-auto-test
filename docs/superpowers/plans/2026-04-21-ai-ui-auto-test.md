# AI UI 自动化 CLI（gen / run / heal）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans，按任务逐步执行。步骤使用 `- [ ]` 勾选跟踪。

**Goal:** 交付可运行的本地 CLI：从半结构化中文 Markdown 用例生成 Playwright+pytest 脚本、执行测试、在失败后用 LLM 产出可人工审核的修复 diff。

**Architecture:** Python 包 `aitest` 提供 Typer CLI；`case_parser` 解析 YAML front matter 与 steps/asserts；`llm` 模块通过环境变量对接 **OpenAI 兼容** 的内网 Chat Completions HTTP API；`gen` 将结构化用例与系统约束写入 prompt，校验生成代码语法后落盘；`run` 委托 `pytest`；`heal` 读取失败信息与原脚本，请求 LLM 输出 unified diff。**MVP 不实现**真实内网专有 SDK，仅以 `LLM_BASE_URL` + Bearer 兼容层接入。

**Tech Stack:** Python 3.11+、`typer`、`pytest`、`playwright`、`httpx`、`pyyaml`、`python-dotenv`。

---

## 文件总览（将创建）

| 路径 | 职责 |
|------|------|
| `pyproject.toml` | 包元数据、依赖、`aitest` 脚本入口 |
| `.gitignore` | `__pycache__`、`.env`、`reports/`、`.pytest_cache/` |
| `.env.example` | LLM 与测试账号变量名占位 |
| `aitest.yaml` | 默认路径与 Playwright 设备名 |
| `cases/example_baidu.md` | 与 SPEC 一致的示例用例 |
| `src/aitest/__init__.py` | 版本号 |
| `src/aitest/cli.py` | Typer：`gen` / `run` / `heal` / `init` |
| `src/aitest/case_parser.py` | 解析 md → `CaseDocument` dataclass |
| `src/aitest/llm/client.py` | OpenAI 兼容 `chat/completions` |
| `src/aitest/llm/prompts.py` | `build_gen_prompt` / `build_heal_prompt` |
| `src/aitest/gen.py` | 调用 LLM、校验、写 `tests/generated/` |
| `src/aitest/heal.py` | 调用 LLM 产出 diff |
| `tests/conftest.py` | Playwright pytest 插件 fixture：`browser_context_args` |
| `tests/generated/.gitkeep` | 占位；生成文件可删后由 gen 创建 |

---

### Task 1: 工程骨架与可安装 CLI

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/aitest/__init__.py`
- Create: `src/aitest/cli.py`

- [ ] **Step 1: 添加 `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aitest"
version = "0.1.0"
description = "NL case to Playwright+pytest; gen, run, heal CLI"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "typer>=0.12",
  "httpx>=0.27",
  "pyyaml>=6",
  "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-playwright>=0.5"]

[project.scripts]
aitest = "aitest.cli:app"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: 实现占位 CLI**

`src/aitest/cli.py`：

```python
import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.command()
def init():
    """生成 aitest.yaml 与 .env.example（若不存在）。"""
    raise SystemExit("implement in Task 1 follow-up")

@app.command()
def gen(case: str):
    """根据 Markdown 用例生成 tests/generated 下的 pytest 文件。"""
    raise SystemExit("implement in Task 4")

@app.command()
def run(ctx: typer.Context):
    """运行 pytest；透传未知参数。"""
    raise SystemExit("implement in Task 5")

@app.command()
def heal(case_id: str | None = None, report: str | None = None):
    """根据失败上下文生成修复 diff。"""
    raise SystemExit("implement in Task 6")

def main():
    app()

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 可编辑安装并验证入口**

Run:

```bash
cd /Users/wenchao.zeng/work/codes/ai-auto-test
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
aitest --help
```

Expected: 显示 Typer 帮助，无 ImportError。

- [ ] **Step 4: Commit（若已 `git init`）**

```bash
git add pyproject.toml .gitignore src/aitest
git commit -m "chore: scaffold aitest package and CLI entry"
```

---

### Task 2: 用例解析器

**Files:**
- Create: `src/aitest/case_parser.py`
- Create: `cases/example_baidu.md`
- Create: `tests/test_case_parser.py`

- [ ] **Step 1: 写失败单测（解析 steps 条数）**

`tests/test_case_parser.py`：

```python
from pathlib import Path
from aitest.case_parser import parse_case_file

def test_parse_example_baidu():
    root = Path(__file__).resolve().parents[1]
    doc = parse_case_file(root / "cases" / "example_baidu.md")
    assert doc.id == "baidu_search_apple"
    assert "baidu.com" in doc.target
    assert len(doc.steps) >= 3
    assert len(doc.asserts) >= 1
```

Run: `pytest tests/test_case_parser.py -v`  
Expected: **FAIL**（`parse_case_file` 未定义）

- [ ] **Step 2: 实现 `parse_case_file`**

`src/aitest/case_parser.py` 使用 `yaml.safe_load` 解析 front matter（`---` 包裹），正文用正则或行扫描提取 `## steps` 与 `## asserts` 下内容，有序列表行去掉前缀 `数字.` 存入 `steps` / `asserts` 字符串列表。

- [ ] **Step 3: 再次运行 pytest**

Expected: **PASS**

---

### Task 3: LLM HTTP 客户端（OpenAI 兼容）

**Files:**
- Create: `src/aitest/llm/client.py`
- Create: `tests/test_llm_client.py`（使用 `httpx.MockTransport`）

- [ ] **Step 1: 单测 mock 返回 choices[0].message.content**

- [ ] **Step 2: 实现 `chat_completion(messages, model, temperature=0.2) -> str`**

POST `{base_url}/v1/chat/completions`，Header `Authorization: Bearer {api_key}`。

- [ ] **Step 3: pytest 全绿**

---

### Task 4: `gen` 命令与提示词

**Files:**
- Create: `src/aitest/llm/prompts.py`
- Create: `src/aitest/gen.py`
- Modify: `src/aitest/cli.py`（`gen` 调用 `run_gen`）

- [ ] **Step 1: `build_gen_prompt(case_doc)`**  
  约束：仅 `pytest`、`playwright.sync_api`；函数名 `test_{id}`；文件顶 `AITEST_META` 注释块包含 `case_id`、源路径；使用 `os.environ` 读取 `TEST_USERNAME`/`TEST_PASSWORD` 若用例含登录关键词（可选）；**禁止** `subprocess`、`eval`、`exec`、网络请求除被测 URL。

- [ ] **Step 2: `run_gen(case_path)`**  
  调 `chat_completion`，对返回去 markdown fence，用 `ast.parse` 校验语法，写入 `tests/generated/test_{slug}.py`。

- [ ] **Step 3: 手工联调**（需有效 `.env`）

Run: `aitest gen cases/example_baidu.md`  
Expected: 生成非空 `tests/generated/test_baidu_search_apple.py`。

---

### Task 5: Playwright + `run`

**Files:**
- Create: `tests/conftest.py`
- Modify: `pyproject.toml`（确保 `pytest-playwright` 在 dev）
- Modify: `src/aitest/cli.py`（`run` 使用 `subprocess` 调 `pytest` — **允许**：CLI 工具本身调用子进程运行测试；**生成脚本内**仍禁止 `subprocess`）

`tests/conftest.py` 最小内容：

```python
import pytest

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, pytestconfig):
    return {**browser_context_args, "locale": "zh-CN"}
```

Run:

```bash
playwright install chromium
aitest run tests/generated/test_baidu_search_apple.py -v
```

Expected: 由生成脚本质量决定；若失败则进入 Task 6 或迭代 prompt。

---

### Task 6: `heal` 与失败产物

**Files:**
- Modify: `tests/conftest.py`（`pytest_runtest_makereport` 钩子：失败时写 `reports/last_failure.txt`：nodeid、长repr、可选 `page.content()` 截断前 N 字符）
- Create: `src/aitest/heal.py`
- Modify: `src/aitest/cli.py`

`build_heal_prompt` 输入：原 py 全文 + `reports/last_failure.txt`。要求 LLM **仅**输出 unified diff，无其它文字。`heal` 将 stdout 写入 `reports/heal-{case_id}.diff`。

---

### Task 7: `init` 与默认配置

**Files:**
- Create: `aitest.yaml`（若 init 才写，可模板化）
- Create: `.env.example`
- Modify: `src/aitest/cli.py` 的 `init`

---

## Self-Review（计划 vs SPEC）

| SPEC 章节 | 对应任务 |
|-----------|----------|
| CLI gen/run/heal | Task 1,4,5,6 |
| 半结构化 md | Task 2 + `cases/example_baidu.md` |
| 内网 LLM | Task 3（兼容层；专有 SDK 为开放项） |
| 自愈人审 | Task 6 产出 `.diff` |
| 登录/验证码假设 | Task 4 prompt 约束 + `.env` |
| H5 | `aitest.yaml` 中 `mobile_device` + conftest 传参（可在 Task 5 扩展 `browser_context_args` 注入 `**playwright.devices["iPhone 13"]`） |

**缺口（后续迭代）：** 内网非 OpenAI 兼容协议适配；多模态截图 heal；`storage_state` 登录。

---

## 执行交接

**Plan 已保存至** `docs/superpowers/plans/2026-04-21-ai-ui-auto-test.md`。

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每个 Task 新开子代理，任务间 review。需使用 **subagent-driven-development** 技能。  
2. **Inline Execution** — 本会话内按任务执行，使用 **executing-plans** 技能。

请选择 **1** 或 **2**；若未指定，默认在当前会话内连续实现 Task 1–3 骨架直至 `aitest --help` 与解析器测试通过。
