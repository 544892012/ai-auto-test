# AI 驱动 Web/H5 UI 自动化测试 — 设计规格

**日期**：2026-04-21  
**状态**：已评审通过（头脑风暴收敛）  
**范围**：本地 CLI MVP，后续可扩展插件/平台

---

## 1. 背景与目标

### 1.1 问题

传统 UI 自动化依赖人工编写每个用例（脚本或函数），维护成本高；页面改版后选择器失效，修复重复劳动多。

### 1.2 目标

1. **用例编写**：QA/开发以**半结构化中文 Markdown** 描述步骤与断言，降低门槛。  
2. **脚本生成**：由**公司内部大模型网关**将用例转为 **Playwright + pytest** 可执行代码，纳入版本管理与 CI。  
3. **执行**：CI/本地执行确定性脚本（执行阶段**不依赖** LLM，保证稳定与成本可控）。  
4. **自愈（Self-Healing）**：脚本因 UI 变更失败时，通过离线 **`heal`** 命令结合失败上下文与页面信息生成**补丁式修改**，经**人工审核**后再合入，避免静默污染仓库。

### 1.3 非目标（MVP 不做）

- 不做完整 Web 测试管理平台（用例管理、权限、报表大盘等）。  
- 不做原生 App（Appium）；仅 **Web + H5（浏览器内移动模拟）**。  
- 不在**生产/不可改配置**环境上承诺绕过验证码；MVP 假设**测试环境**可配置「跳过验证码」或「固定测试码」。  
- 不自愈流程中**自动 commit** 到主分支。

---

## 2. 用户场景

### 2.1 典型流程

1. 作者新建或编辑 `cases/baidu_search_apple.md`（半结构化用例）。  
2. 执行 `aitest gen cases/baidu_search_apple.md` → 生成或更新 `tests/generated/test_baidu_search_apple.py`。  
3. 人工 Code Review 生成脚本后合入。  
4. CI 或本地执行 `aitest run`（底层 `pytest`）。  
5. 某次 UI 改版导致失败 → 本地或 CI 产物中保留失败信息 → 执行 `aitest heal <case或失败目录>` → 输出 diff/patch → 人审后合入。

### 2.2 示例用例（半结构化 Markdown）

```markdown
---
id: baidu_search_apple
target: https://www.baidu.com
device: mobile  # 可选: desktop | mobile，映射 Playwright 设备描述
---

# 百度搜索苹果

## steps
1. 打开 target 首页
2. 在搜索框输入「苹果」
3. 点击「百度一下」或等价搜索按钮

## asserts
- 结果区域可见且包含文案「Apple」或「苹果」相关结果（按环境可放宽为「搜索结果列表非空」）
```

**说明**：front matter 用 YAML 承载结构化字段；正文用有序步骤与自然语言断言，便于人读与 LLM 解析。

---

## 3. 架构概览

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ cases/*.md      │────▶│ aitest gen       │────▶│ tests/generated/*.py │
└─────────────────┘     │  (调用 LLM)      │     └──────────┬────────────┘
                        └──────────────────┘                │
                                                              ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ .env (gitignore)│     │ aitest run       │────▶│ pytest + Playwright │
└─────────────────┘     └──────────────────┘     └──────────┬────────────┘
                                                          │ 失败时
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────────┐
│ reports/        │◀───│ aitest heal      │◀────│ 失败日志 + DOM 摘要  │
└─────────────────┘     │  (调用 LLM)      │     │ (+ 可选截图)          │
                        └──────────────────┘     └─────────────────────┘
```

### 3.1 组件职责

| 组件 | 职责 |
|------|------|
| **CLI (`aitest`)** | 子命令：`gen` / `run` / `heal` / `init`（可选，生成默认配置） |
| **Case 解析器** | 解析 front matter + `## steps` / `## asserts` 区块 |
| **LLM Provider** | 抽象接口：对内网网关适配（OpenAI 兼容或自定义 HTTP/SDK） |
| **代码生成器** | 组装 prompt，约束输出为合法 Python + pytest + Playwright |
| **执行器** | 封装 `pytest`，透传参数；统一 `conftest.py`（浏览器、trace、截图） |
| **Heal 引擎** | 摄入：原脚本、堆栈、步骤名、DOM 可访问性树或简化 HTML 摘要、可选截图；输出：unified diff |

### 3.2 LLM 与多模态（MVP）

- **MVP**：以 **文本** 为主（用例 md + DOM 文本摘要 + 错误栈）。  
- **可选增强**：Heal 时附加**截图**需网关支持**多模态**；若当前内网模型仅文本，则截图字段保留接口、默认关闭。

---

## 4. CLI 设计

### 4.1 命令约定

| 命令 | 说明 |
|------|------|
| `aitest gen <path-to-case.md>` | 根据用例生成/覆盖更新对应 `tests/generated/` 下文件（策略见 4.2） |
| `aitest run [pytest-args...]` | 运行测试；默认 `pytest tests/` 或项目配置的路径 |
| `aitest heal [--case <id>] [--from-report <dir>]` | 基于最近一次失败或指定报告目录生成修复建议（patch/diff） |
| `aitest init` | （可选）生成 `aitest.yaml` 示例与 `.env.example` |

### 4.2 生成文件命名与幂等

- 建议映射：`cases/<name>.md` → `tests/generated/test_<slug>.py`，`slug` 来自 front matter `id` 或文件名。  
- 生成文件顶部包含**机器可读注释块**（如 `# --- AITEST_META begin ... end ---`），记录 `case_id`、源 md 路径、生成时间、模型版本，便于 heal 与审计。

---

## 5. 配置与密钥

### 5.1 `aitest.yaml`（建议字段）

```yaml
llm:
  provider: internal_gateway  # 实现映射到具体 SDK/HTTP
  base_url: ${LLM_BASE_URL}   # 或由 env 覆盖
  model: ${LLM_MODEL}
playwright:
  browser: chromium
  mobile_device: "iPhone 13"   # H5 场景
  trace: "on-first-retry"
pytest:
  args: ["-v", "--tb=short"]
paths:
  cases: cases
  generated: tests/generated
auth:
  mode: env_credentials       # 从环境变量读账号密码
  # test_env 假设可跳过或固定验证码，见 6 节
```

### 5.2 `.env`（不入库）

- `LLM_BASE_URL` / `LLM_API_KEY`（若网关需要）/ `LLM_MODEL`  
- `TEST_USERNAME` / `TEST_PASSWORD`（如用例需要）  
- 使用 `python-dotenv` 或 shell 注入；**仓库仅保留 `.env.example`**（无真实值）。

---

## 6. 登录与验证码（MVP 假设）

1. **账密**：从环境变量读取，生成脚本中使用 `os.environ["TEST_USERNAME"]` 等，避免写死。  
2. **验证码**：依赖**测试环境**能力——跳过人机校验或固定测试码（产品已确认）。  
3. **与准生产/生产的边界**：若未来不能改验证码，需增加 **`storage_state` 路径**（人工登录一次导出状态文件，CI 解密注入）；本 SPEC 列为**后续迭代**，不在 MVP 必选内。

---

## 7. Self-Healing（`heal`）流程

### 7.1 触发

- 人工在失败发生后运行 `aitest heal`。  
- **不**在默认 `run` 流程中静默修改源码。

### 7.2 输入

- 失败用例的 pytest 输出（含节点 id、失败行）。  
- 对应 `tests/generated/*.py` 当前版本。  
- **DOM 摘要**：Playwright 在失败钩子中抓取 `page.accessibility.snapshot()` 或截断的 `inner_text` / 关键 selector 列表（需控制 token 长度）。  
- 可选：失败截图路径（多模态可用时传入）。

### 7.3 输出

- stdout 或 `patches/<case_id>-<timestamp>.diff`  
- **人工**将 diff 应用到仓库并 PR。

### 7.4 安全与质量

- Heal 提示词中禁止泄露 `.env` 中的密钥；仅传「需要 env 变量名」不写值。  
- 对 LLM 输出做 **AST/语法校验**，不通过则重试或报错，不写入半成品。

---

## 8. 测试与 CI

- 本地：`aitest run`。  
- CI：安装依赖、`playwright install`、注入 secrets、执行 `pytest`。  
- 产物：JUnit XML、失败截图、trace zip（按 `playwright` 配置可选）。

---

## 9. 建议目录结构

```
ai-auto-test/
├── aitest.yaml
├── .env.example
├── pyproject.toml              # 或 requirements.txt
├── cases/
│   └── example_baidu.md
├── tests/
│   ├── conftest.py             # fixture：浏览器、base_url、失败截图
│   └── generated/              # LLM 生成，可整体 gitignore 或纳入评审后入库（团队策略二选一，默认建议入库以便 diff）
├── src/aitest/                 # CLI 包实现
│   ├── __main__.py
│   ├── cli.py
│   ├── case_parser.py
│   ├── llm/
│   │   ├── base.py
│   │   └── internal_gateway.py
│   ├── gen.py
│   └── heal.py
├── docs/superpowers/specs/
│   └── 2026-04-21-ai-ui-auto-test-design.md
└── reports/                    # gitignore，本地/CI 产物
```

**说明**：`tests/generated` 是否入库由团队决定；推荐**入库**以便 PR 可见生成代码与 heal diff。

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| LLM 生成代码不安全或调用危险 API | 静态扫描 + 仅允许 Playwright/pytest 白名单 import；禁止 `subprocess`/`os.system` 等（可 lint） |
| DOM 摘要过长导致超 token | 分层摘要：仅失败步骤附近 DOM + 默认深度限制 |
| 内网 LLM 无多模态 | Heal 第一阶段仅用文本；截图列为可选 |
| 选择器脆弱 | 生成时 prompt 要求优先 `get_by_role`/`get_by_text`/`data-testid` |

---

## 11. 开放项（实现前需对齐）

1. **公司内部 LLM 网关**的具体协议（OpenAI Chat Completions 兼容 vs 自定义）、鉴权方式、是否支持图片输入。  
2. **`tests/generated` 是否入库**的最终策略。  
3. **H5 设备矩阵**：默认一台设备名是否足够，或多 profile。

---

## 12. 下一步（实现阶段）

经本 SPEC 确认后，使用 **writing-plans** 技能输出分阶段实现计划（建议：先 `gen`+最小用例+单次 `run`，再 `heal` 最小闭环，最后 CI 与 heal 报告增强）。

---

## 修订历史

| 日期 | 说明 |
|------|------|
| 2026-04-21 | 初版：头脑风暴结论落地 |
