# 写作助手 / Writing Assistant

一个可迁移的本地桌面写作助手，支持多场景 AI 信件生成、材料自动转换与结构化输出。  
A portable local desktop writing assistant for multi-scenario AI letter generation, material conversion, and structured outputs.

## 项目定位 / What This Project Is

- 面向高频文书场景（如申诉信、退租信）的一体化 GUI 工具。  
  A unified GUI tool for high-frequency writing tasks (such as appeal letters and lease termination letters).
- 本地优先，不绑定个人机器路径，不内置敏感密钥。  
  Local-first design with no hardcoded machine paths and no embedded sensitive keys.
- 支持 OpenRouter，可切换模型，支持默认模型配置。  
  OpenRouter-based, model-switchable, with configurable default model.

## 核心功能 / Core Features

1. Offer Appeal 生成（最小输入模式）  
   Offer appeal letter generation (minimal-input mode).
2. Lease Direct 直写（直接生成）  
   Lease direct letter generation (from structured inputs).
3. Lease Template 改写（按模板重写）  
   Lease template rewrite (template-driven output).
4. 材料自动转换（`txt/md/docx/pdf/pptx` -> Markdown）  
   Automatic material conversion (`txt/md/docx/pdf/pptx` -> Markdown).
5. Markdown + DOCX 输出  
   Markdown and DOCX outputs.
6. 设置页统一管理：API Key、默认模型、超时、重试、字数区间、数据目录  
   Central settings page: API key, default model, timeout, retries, word range, data root.

## 目录结构 / Project Structure

```text
.
├── app/
│   ├── gui.py
│   ├── openrouter_client.py
│   ├── converter.py
│   ├── settings.py
│   └── pipelines/
├── build/
│   ├── build_mac.sh
│   └── build_win.ps1
├── docs/
├── .github/workflows/ci-build.yml
├── launch_app.py
└── requirements.txt
```

## 环境要求 / Requirements

- Python 3.11+（推荐）  
  Python 3.11+ (recommended)
- 可访问 OpenRouter 的网络环境  
  Network access to OpenRouter

## 本地启动 / Run Locally

### macOS / Linux

```bash
cd "<repo-root>"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python launch_app.py
```

### Windows (PowerShell)

```powershell
cd "<repo-root>"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python launch_app.py
```

## 首次配置 / First-Time Setup

在应用的 `Settings` 页填写并保存：  
Configure and save these fields in the `Settings` tab:

1. `OpenRouter API Key`（必填）  
   `OpenRouter API Key` (required)
2. `Default Model`（默认：`anthropic/claude-sonnet-4.6`）  
   `Default Model` (default: `anthropic/claude-sonnet-4.6`)
3. `Timeout (sec)`、`Retries`  
   `Timeout (sec)` and `Retries`
4. `Default Word Min/Max`（默认 750-900）  
   `Default Word Min/Max` (default 750-900)
5. `Data Root`（可选，建议单独目录便于迁移）  
   `Data Root` (optional, recommended for clean migration)

保存后重启应用，使默认路径在所有标签页完全刷新。  
Restart the app after saving to refresh default paths across all tabs.

## 使用说明 / How To Use

### 1) Offer Appeal（最少输入）

最低必填：  
Minimum required:

- `Target School`
- `Requested Revision`

建议补充（可选）：  
Recommended optional fields:

- `Professor URL`
- `Program URL`
- `Program`
- `Extra Instructions`
- 材料目录 `Materials Folder`（放成绩单/CV/补充说明等）  
  `Materials Folder` (transcript/CV/supporting docs)

点击 `Generate Offer Appeal` 生成结果。  
Click `Generate Offer Appeal` to generate.

### 2) Lease Direct（直接生成）

建议至少填写：  
Recommended minimum:

- `Tenant Name`
- `Issues`

其余字段用于提高定制程度（地址、退款诉求、健康背景、法域等）。  
Other fields improve specificity (address, refund demand, health context, jurisdiction, etc.).

### 3) Lease Template（模板改写）

必填：  
Required:

- `Tenant Name`
- `Issues`
- `Template DOCX`

系统会在模板基础上进行内容改写并导出。  
The app rewrites content based on your template and exports the result.

## 输出与数据目录 / Output and Data Directories

默认会创建并使用以下目录（可通过 `Data Root` 覆盖）：  
The app creates and uses the following folders by default (overridable via `Data Root`):

- `materials`
- `converted`
- `output`
- `templates`
- `contracts`

输出通常包括：  
Typical outputs include:

- `.md`（中间与最终文本）  
  `.md` (intermediate and final text)
- `.docx`（可交付版本）  
  `.docx` (deliverable version)

## 模型与提示词策略 / Model and Prompt Strategy

- 每个业务标签页都可单独填写模型 ID。  
  Each workflow tab supports its own model ID.
- 不填写时使用 `Settings` 中的默认模型。  
  If left empty, the default model in `Settings` is used.
- 建议保留“结构约束 + 字数约束 + 禁止编造”三类规则，提高稳定性。  
  Keep structure constraints, word-count bounds, and anti-fabrication rules for stable quality.

## 构建打包 / Packaging

### macOS DMG

```bash
./build/build_mac.sh
```

### Windows EXE

```powershell
.\build\build_win.ps1
```

更多细节见：  
For details, see:

- `docs/DEPLOYMENT.md`
- `docs/KEYS_AND_SETTINGS.md`
- `docs/TROUBLESHOOTING.md`

## GitHub Actions（自动安装环境与构建） / GitHub Actions (Auto Setup and Build)

工作流文件：`.github/workflows/ci-build.yml`  
Workflow file: `.github/workflows/ci-build.yml`

触发条件：  
Triggers:

1. `push` 到 `main`
2. `pull_request`
3. 手动触发 `workflow_dispatch`

流程内容：  
Pipeline steps:

1. 安装 Python 依赖  
   Install Python dependencies
2. 运行编译检查  
   Run compile checks
3. 构建 macOS/Windows 产物  
   Build macOS and Windows artifacts
4. 上传 artifacts 供下载  
   Upload downloadable artifacts

## 隐私与安全 / Privacy and Security

- API Key 不写死在代码中。  
  API keys are not hardcoded in source code.
- 配置保存在用户目录下的设置文件中。  
  Settings are stored in a per-user config file.
- 迁移到新设备时，仅需复制项目并重新填写 Key。  
  On a new device, copy project files and set the key again.

## 常见问题 / FAQ

1. **启动后报 API Key 缺失**  
   去 `Settings` 填写并保存 `OpenRouter API Key`。  
   Fill and save `OpenRouter API Key` in `Settings`.

2. **模型切换不生效**  
   检查当前标签页 `Model` 输入框是否被留空或写错模型 ID。  
   Check whether the current tab's `Model` field is empty or invalid.

3. **文档转换失败（PDF/DOCX）**  
   先确认依赖已完整安装，再查看 `docs/TROUBLESHOOTING.md`。  
   Confirm dependencies are installed, then check `docs/TROUBLESHOOTING.md`.
