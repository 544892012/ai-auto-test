# ai-auto-test

将**半结构化中文 Markdown** 用例交给大模型，生成 **Playwright + pytest** 可执行脚本；支持本地 CLI **`gen`（生成）** / **`run`（执行）** / **`heal`（失败修复建议）**。设计规格见 `docs/superpowers/specs/2026-04-21-ai-ui-auto-test-design.md`，实现计划见 `docs/superpowers/plans/2026-04-21-ai-ui-auto-test.md`。

---

## 功能概览


| 命令                      | 作用                                                                                                                |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `aitest init`           | 创建 `cases/`、`tests/generated/`、`reports/`；若不存在则写入 `.env.example` 与最小 `aitest.yaml`                                |
| `aitest gen <用例.md>`    | 解析用例 → 调用 LLM → 语法与安全校验 → 写入 `tests/generated/test_<id>.py`                                                       |
| `aitest gen-all`        | 对 `cases/*.md` **逐个**执行 `gen`；默认失败不中断，可用 `--fail-fast` 遇错即停                                                                |
| `aitest run …`          | 透传参数执行 `pytest`；无额外参数时默认跑整个 `tests/`                                                                              |
| `aitest heal <case_id>` | 读取 `reports/last_failure.txt` 与 `tests/generated/test_<id>.py`，调用 LLM 输出 `reports/heal-<id>-<时间>.diff`（需人工审阅后再应用） |


**执行阶段不调用 LLM**（除 `gen` / `heal`），CI 跑的是确定性脚本，成本与稳定性可控。

### `cases/*.md` 和 `tests/generated/*.py` 是什么关系？

- **`cases/`**：给人看的用例说明（Markdown），**不会**被 pytest 直接执行。  
- **`tests/generated/`**：只有在你运行 **`aitest gen …`**（或 **`aitest gen-all`**）之后，才会根据 front matter 里的 **`id`** 生成对应的 **`test_<id>.py`**。  
- **`aitest run`**：等价于跑 **`pytest`**，**只执行已有的 `.py`**，**不会**根据 Markdown 自动生成新脚本。

因此：新建了 `cases/foo.md` 但目录里没有 `tests/generated/test_foo.py`，是因为**还没对该文件执行 `gen`**。批量生成示例：

```bash
aitest gen-all
```

---

## 环境要求

- **Python 3.11+**
- 可访问的 **OpenAI 兼容 Chat Completions** 接口（如 DeepSeek、内网网关等）
- 运行浏览器用例前需安装 Playwright 浏览器：`playwright install chromium`

---

## 安装

```bash
cd /path/to/ai-auto-test
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
playwright install chromium
aitest init
```

安装完成后应能执行：

```bash
aitest --help
```

---

## 大模型（LLM）配置

CLI 在 `gen` / `heal` / `run` 入口会 `load_dotenv()`，优先读取当前工作目录下的 `**.env**`（请把 `.env` 加入 `.gitignore`，**不要提交密钥**）。

### 环境变量说明


| 变量                 | 含义                   | 备注                                                                         |
| ------------------ | -------------------- | -------------------------------------------------------------------------- |
| `LLM_BASE_URL`     | Chat Completions 根地址 | 与 `OPENAI_API_BASE` **二选一**即可                                              |
| `OPENAI_API_BASE`  | 同上（兼容常见工具链命名）        | 示例：`https://api.deepseek.com`                                              |
| `LLM_API_KEY`      | Bearer Token         | 可与 `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` 混用，按优先级取值                         |
| `OPENAI_API_KEY`   | 同上                   |                                                                            |
| `DEEPSEEK_API_KEY` | 同上                   |                                                                            |
| `LLM_MODEL`        | 模型名                  | 与 `OPENAI_MODEL` 二选一；若未设置且 `base_url` 含 `deepseek`，则默认 `**deepseek-chat`** |
| `OPENAI_MODEL`     | 同上                   |                                                                            |


**请求形态**：向 `{LLM_BASE_URL}/v1/chat/completions` 发送 JSON，与 OpenAI 官方兼容（内网若路径不同，需在后续版本增加配置项或适配层）。

### DeepSeek 示例（`.env`）

```bash
OPENAI_API_BASE=https://api.deepseek.com
OPENAI_API_KEY=你的密钥
# 可不写模型名，将默认 deepseek-chat
```

等价写法：

```bash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=你的密钥
LLM_MODEL=deepseek-chat
```

### 登录相关（可选）

若生成脚本中需要登录，生成器会引导使用：

- `TEST_USERNAME`
- `TEST_PASSWORD`

请在 `.env` 中配置；**勿**把真实密码写进用例 Markdown 或生成的仓库明文。

---

## 用例编写（Markdown）

用例文件分为 **YAML Front Matter** + **正文**。

### 约定字段（Front Matter）


| 字段       | 必填  | 说明                                        |
| -------- | --- | ----------------------------------------- |
| `id`     | 是   | 用例唯一 id，对应生成文件 `test_<id>.py`             |
| `target` | 是   | 起始 URL（生成 prompt 会明确传给模型）                 |
| `device` | 否   | `desktop` / `mobile` 等，供 prompt 描述视口与站点类型 |


### 正文结构

- 一级标题 `#`：用例人类可读标题  
- `## steps`：步骤列表，推荐 `1.` / `2.` 编号  
- `## asserts`：断言描述，推荐 `-` 列表

仓库内 `**cases/*.md`** 均为示例，可按需复制改名：


| 文件                                | 场景                        |
| --------------------------------- | ------------------------- |
| `example_baidu.md`                | 百度搜索（已配合 `gen` 调试过 m 站路径） |
| `smoke_example_domain.md`         | 极简外站冒烟（example.com）       |
| `smoke_playwright_get_started.md` | 文档站加载与关键字可见性              |
| `form_httpbin_post.md`            | 简单表单填写与提交（httpbin）        |
| `mobile_baidu_search_orange.md`   | 移动百度检索另一条关键词              |


解析契约单测：`pytest tests/test_all_case_files_parse.py`（不调用 LLM）。

---

## 常用工作流

### 1. 生成脚本（单个用例）

```bash
aitest gen cases/example_baidu.md
# 或指定输出目录
aitest gen cases/example_baidu.md --out tests/generated
```

成功时打印：`written: tests/generated/test_<id>.py`

生成代码会经过 **AST 解析**与**危险 import 拦截**（如 `subprocess`、`httpx` 等），不通过则不会落盘。

### 1b. 批量生成：为 **所有** `cases/*.md` 生成 `tests/generated/test_<id>.py`

适用于：新增/修改了多条 Markdown 用例，希望一次性产出（或刷新）全部可执行脚本，再进入 Code Review 与 CI。

```bash
# 默认扫描仓库根目录下 cases/ 内全部 .md，按文件顺序逐个调用 LLM
aitest gen-all

# 指定用例目录（例如多套件分目录时）
aitest gen-all --cases /path/to/cases

# 指定生成输出目录（默认仍为 tests/generated）
aitest gen-all --out tests/generated

# 遇第一条失败立即停止（默认会继续跑完并汇总）
aitest gen-all --fail-fast
```

**注意（生产/成本）**：

- `gen-all` 会对 **每个** `.md` 各调用 **一次** 大模型接口：用例多时会显著增加 **耗时与费用**，建议在非高峰或带 **限速/重试** 的流水线中执行。  
- **默认容错**：任一条失败会 **打印错误并继续** 处理后续用例，最后汇总 `ok/failed` 并以 **退出码 1** 表示存在失败；若希望遇错即停，请加 **`--fail-fast`**。  
- LLM HTTP 层对超时、连接错误、429/5xx 等会做 **有限次重试**（见 `aitest/llm/client.py`）。  
- 推荐流程：**本地或独立 Job 跑 `gen-all` → 人审 diff → 合入 → CI 只 `aitest run`**，避免在主干每次提交都自动 `gen-all` 刷脚本。

**与 CI 的分工建议**：

| 阶段 | 命令 | 说明 |
|------|------|------|
| 编写用例 | 编辑 `cases/*.md` | 人写或产品/QA 写 |
| 生成脚本 | `aitest gen` / `aitest gen-all` | 需要 LLM；产出 `tests/generated/*.py` |
| 回归执行 | `aitest run` / `pytest` | **不调用** LLM，可高频跑 |

### 2. 执行测试

```bash
# 跑单个生成文件
aitest run tests/generated/test_baidu_search_apple.py -v

# 跑全部 tests（无参数时 aitest run 的默认行为）
aitest run

# 透传 pytest 参数示例
aitest run tests/generated -k baidu --tb=short -q
```

### 3. 失败自愈（离线 diff）

失败时，`tests/conftest.py` 中的钩子会向 `**reports/last_failure.txt**` 写入节点 id、堆栈摘要以及（若存在 `page` fixture）**页面 HTML 截断**，供 `heal` 使用。

```bash
# 先有一次失败（例如 pytest 失败）
aitest heal baidu_search_apple
```

输出示例：`diff written: reports/heal-baidu_search_apple-<时间戳>.diff`

请**人工审查** diff 后，再使用 `git apply` 或 IDE 应用补丁，**不要**盲信模型直接合入主干。

---

## 目录结构（摘要）

```
ai-auto-test/
├── aitest.yaml           # 可选全局配置（init 可生成最小版）
├── cases/                # Markdown 用例
├── tests/
│   ├── conftest.py       # Playwright 与失败报告钩子
│   └── generated/        # LLM 生成 pytest 文件（建议入库便于评审）
├── reports/              # last_failure、heal diff（默认 gitignore）
├── src/aitest/           # CLI 与核心逻辑
└── docs/superpowers/     # SPEC 与计划
```

---

## 已知限制与排错

1. **外站页面改版**：生成脚本可能一次不通，属正常现象；用 `heal` 或人工改选择器后再跑。
2. **百度示例**：`www.baidu.com` 在 **headless** 下常见搜索框不可见；移动场景可改用 `**https://m.baidu.com/`** 与可见控件（如 `#index-kw` / `#index-bn`）。`gen` 的 prompt 已包含该提示，但若仍失败，请人工改用例 `target` 或改生成结果。
3. **验证码**：MVP 假设测试环境可关闭或固定验证码；生产环境请另设计 `storage_state` 等方案（见 SPEC「开放项」）。
4. **网络与合规**：E2E 依赖外网与目标站点策略；内网系统请配置可达的 `target` 与代理（若需要可在后续版本加 `playwright` proxy 配置）。  
5. **生成脚本常见不稳点**：`example.com` 上 IANA 说明链接的**可见文案**可能变化，优先用 `a[href*="iana.org"]` 等 **href** 断言；文档站标题多为 `章节 | 站点名`，`to_have_title` 请用 **正则**（`re.compile(r"Playwright")`）而非与短字符串**完全相等**。

---

## 开发自测（本仓库）

```bash
source .venv/bin/activate
pytest -q
```

仅校验解析器与 LLM 客户端 mock，**不**默认调用外网 LLM。

---

## 安全提醒

- **永远不要**将含真实密钥的 `.env` 提交到仓库或粘贴到聊天/工单。  
- 若密钥曾出现在日志或共享屏幕中，建议在提供方控制台**轮换（rotate）**。

