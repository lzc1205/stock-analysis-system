# 个股金融数仓与投研大屏系统

> A 股个股金融数据仓库 + 可视化大屏 + NL2SQL 智能问数。
> 四层数仓建模（ODS / DWD / DWS / ADS），覆盖 18 张数仓表、30 个前端页面、5000+ 只 A 股；
> 内置 LangGraph 投研 Agent，自然语言问数经**关键字黑名单 + 表名白名单 + 自动 LIMIT** 三重校验后才落到 SQL，绝不放行写操作。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.4-green)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 目录

- [项目截图](#项目截图)
- [核心亮点](#核心亮点)
- [系统架构](#系统架构)
- [数仓建模](#数仓建模)
- [技术指标](#技术指标)
- [AI 智能问数](#ai-智能问数)
- [功能特性](#功能特性)
- [前端页面](#前端页面)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [数据源](#数据源)
- [部署方式](#部署方式)
- [已知限制](#已知限制)
- [免责声明](#免责声明)

---

## 项目截图

> 截图占位 —— 把图片放到 `docs/images/` 下，文件名按下方标注替换即可。
> 建议至少补 3 张：**投研大屏首页**、**AI 问数对话**、**K 线 + 技术指标**。

| 投研大屏 | AI 智能问数 |
|---|---|
| ![投研大屏](docs/images/dashboard.png) | ![AI 问数](docs/images/ai-chat.png) |
| K 线与技术指标 | 个股财务健康度 |
| ![K线](docs/images/kline.png) | ![财务健康度](docs/images/financial-health.png) |

---

## 核心亮点

这个项目不是「大屏 demo」，重点在两处：**数仓分层做得干净**，以及 **AI 问数不敢乱写**。

### 1. 四层数仓，每层职责明确

```
数据源 → 采集 → ODS（原始快照，不做任何清洗）
              ↓ 清洗 / 去重 / 归一
            DWD（明细标准表，一致口径）
              ↓ 聚合 / 宽表化
            DWS（主题汇总宽表，跨表 JOIN 已完成）
              ↓ 按应用场景组织
            ADS（应用层，直接供大屏与 Agent 查询）
```

**18 张表**按层分布：

| 层 | 表 | 说明 |
|---|---|---|
| **ODS**（7） | `ods_stock_basic` `ods_stock_daily` `ods_daily_basic` `ods_income` `ods_balancesheet` `ods_cashflow` `ods_moneyflow` | 原始快照层，只落不改，保留采集时间戳便于回溯 |
| **DWD**（3） | `dwd_stock_info` `dwd_stock_daily` `dwd_financial_indicator` | 明细标准层，统一字段命名与单位，去除源表冗余列 |
| **DWS**（3） | `dws_stock_daily_wide` `dws_stock_weekly` `dws_industry_daily` | 汇总宽表层，行情 + 指标 + 财务宽表化，跨表 JOIN 前置完成 |
| **ADS**（5） | `ads_stock_overview` `ads_kline_data` `ads_technical_radar` `ads_capital_flow` `ads_financial_health` | 应用层，直接对应大屏的可视化模块 |

关键设计：
- **联合唯一索引 + 日期分区** —— 关键表以 `ts_code + trade_date` 为联合唯一键，重复写入直接被数据库挡住，避免定时任务重跑造成数据翻倍。
- **增量更新** —— ETL 只处理增量区间，不是每天全量重算。
- **离线计算** —— 技术指标在 ETL 阶段算好落库，不在查询时实时算，大屏高频刷新不压数据库。

### 2. AI 问数：让模型不敢写错 SQL

自然语言问数最大的风险是模型生成 `UPDATE` / `DROP`，或者表名字段名瞎编导致查错数据。这个项目用**多层防线**堵住：

```
用户提问
  ↓ ① 意图识别（行情 / 指标 / 财务 / 资金流 / 泛问）
  ↓ ② LangGraph ReAct 循环 —— 按需调用四类工具（行情查询 / 指标计算 / Text-to-SQL / 研报检索）
  ↓ ③ SQL 安全校验（sql_safety.py）
  ↓ ④ 执行 → 结果组装 → 大模型生成解读 → 附免责声明
```

第 ③ 层（`backend/ai/sql_safety.py`）的具体做法：
- **必须以 `SELECT` 开头** —— 非 SELECT 直接拒绝
- **危险关键字黑名单** —— `DROP` `DELETE` `INSERT` `UPDATE` `ALTER` `TRUNCATE` `CREATE` `EXEC` `GRANT` `LOAD` `INTO OUTFILE` `MERGE` `CALL` 等 17 个一律拦截
- **分号拦截** —— 语句内出现 `;` 即拒绝，防止多语句注入
- **表名白名单** —— 只允许访问已注册的 16 张数仓表，`FROM` 后出现的表名必须命中白名单，模型编出来的表直接拒绝
- **自动 LIMIT** —— 未带 `LIMIT` 时自动补 `LIMIT 100`，防止 `SELECT *` 拖垮数据库
- **限流** —— 单用户每分钟调用次数受限

**口径类问题的兜底**：像「roe 怎么算」这种没有唯一数值答案的问题，不硬答，直接回落到研报 / 公告知识库（BGE-M3 + Milvus）并**绑定原文出处**；检索不到依据就自动拒答，绝不让模型自己编一个财务口径。

> **已知不足**：当前校验基于正则与关键字匹配，对精心构造的绕过手法（如 `WITH ... AS (DELETE ...)`、字符串拼接的动态 SQL）覆盖有限。生产化应改为 **AST 解析**（如 sqlglot）做语法树级判定，这是本项目下一步的改进项。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    可视化展示层 (Presentation)                │
│   Vue3 + ECharts + DataV 大屏    │    AI 问答对话组件        │
├─────────────────────────────────────────────────────────────┤
│                    应用服务层 (Service)                       │
│   数据查询 API  │  AI 智能问答服务  │  技术指标计算  │  缓存  │
├─────────────────────────────────────────────────────────────┤
│                    数据仓库层 (Storage)                       │
│   MySQL 数据仓库  │  分层建模 ODS / DWD / DWS / ADS（18 表） │
├─────────────────────────────────────────────────────────────┤
│                    数据采集层 (Collection)                    │
│  Baostock / AkShare（主）  Tushare（可选）  │  APScheduler  │
└─────────────────────────────────────────────────────────────┘
```

**数据流：**

```
数据源 → 采集脚本 → ODS层(原始数据) → 清洗 → DWD层(明细)
    → 聚合 → DWS层(汇总宽表) → ADS层(应用数据)
    → FastAPI → Vue3大屏 / AI问答服务
```

---

## 技术指标

指标在 ETL 阶段用 **TA-Lib** 离线计算并落库（无 TA-Lib 时自动回退纯 pandas 实现），落库字段共 **16 项**：

| 类别 | 字段 |
|---|---|
| 均线 | `ma5` `ma10` `ma20` `ma60` |
| MACD | `dif` `dea` `macd_bar` |
| RSI | `rsi6` `rsi12` `rsi24` |
| KDJ | `k` `d` `j` |

另有 **5 个综合评分维度**（`ads_technical_radar`）：趋势 `trend_score`、动量 `momentum_score`、波动 `volatility_score`、量能 `volume_score`、综合 `overall_score`，并输出交易信号 `signal`。

> 为什么不实时算：K 线图需要拉长周期历史序列做指标对齐，实时计算在每次翻页 / 切股票时都要重跑一遍 TA-Lib，是典型的大屏卡顿来源。离线算好入库后，接口只做一次索引查询。

---

## AI 智能问数

### 能力

- **自然语言行情查询** —— "贵州茅台今天涨了多少？"
- **Text-to-SQL** —— 自然语言转 SQL 查数仓，带关键字黑名单与表名白名单校验
- **技术指标解读** —— "比亚迪的 MACD 现在是什么状态？"
- **财务分析问答** —— "招商银行近三年 ROE 变化趋势如何？"
- **资金流向分析** —— "今天主力资金流入最多的股票有哪些？"
- **多轮对话** —— 支持上下文追问

### 技术架构

```
用户提问 → 意图识别 → LangGraph ReAct 循环
    ├─ 行情查询工具
    ├─ 指标计算工具
    ├─ Text-to-SQL 工具（→ 安全校验 → 执行 → LIMIT 约束）
    └─ 研报检索工具（BGE-M3 + Milvus，口径问题兜底）
    → 结果组装 → 大模型生成解读 → 附免责声明
```

### 安全机制一览

| 机制 | 实现 |
|---|---|
| 语句类型限制 | 必须以 `SELECT` 开头 |
| 表名白名单 | 仅允许白名单内的 16 张数仓表 |
| 行数上限 | 未带 LIMIT 时自动补 LIMIT 100 |
| 限流 | 单用户每分钟 10 次 |
| 口径问题兜底 | 回落研报/公告知识库并绑定原文出处 |
| 无依据拒答 | 检索不到依据时自动拒答，不臆造 |
| 免责声明 | 所有 AI 分析回答自动附加 |

---

## 功能特性

| 模块 | 功能说明 |
|------|---------|
| **多源数据采集** | Baostock + AkShare 双源互补，覆盖日线行情、三大财务报表、资金流向、行业分类；APScheduler 定时调度 + 失败重试 |
| **数仓分层建模** | ODS → DWD → DWS → ADS 四层，18 张表，联合唯一索引 + 日期分区防重复写入 |
| **技术指标** | TA-Lib 离线计算 16 项指标 + 5 维技术雷达评分 |
| **可视化大屏** | Vue3 + ECharts，含 K 线、资金流向、技术雷达、财务健康度、行业对比等组件 |
| **AI 智能问数** | LangGraph 编排投研 Agent，ReAct 按需调用四类工具，SQL 经关键字黑名单 + 表名白名单校验 |
| **选股筛选** | 基本面筛选与技术形态筛选两套筛子 |
| **策略回测** | 自定义策略与分组管理 |
| **缓存与限流** | Redis 热点数据缓存、接口限流、对话历史管理 |
| **数据源可配** | 数据源与接口偏好可在前端页面上配置 |

---

## 前端页面

30 个实际页面，按功能域分组：

| 分组 | 页面 |
|---|---|
| **个股分析** | K 线分析、技术指标、资金流向、财务分析、多股对比 |
| **市场行情** | 指数趋势、涨跌分布、行业板块、市场情绪 |
| **资金面** | 主力资金、北向资金、龙虎榜、两融交易 |
| **选股筛选** | 基本面筛选、技术形态筛选、风险预警 |
| **策略工具** | 自定义策略、自定义分组、策略回测、股票池管理、自选股 |
| **数据与配置** | 数据源、指标参数、界面偏好、账户管理 |
| **资讯与报告** | 财报、个股新闻快讯、行业研报、AI 诊断 |

---

## 技术栈

### 后端

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.10+ | 核心开发语言 |
| Web框架 | FastAPI | 0.115+ | RESTful API，自动生成文档 |
| ORM | SQLAlchemy | 2.0+ | 数据库模型与查询 |
| 数据库 | MySQL | 8.0+ | 数据仓库存储 |
| 缓存 | Redis | 7.0+ | 热点缓存、限流、对话历史 |
| 数据处理 | pandas / numpy | 2.2+ / 1.26+ | 数据清洗与计算 |
| 技术指标 | TA-Lib | 0.6+ | 指标计算（缺失时回退纯 Python） |
| AI框架 | LangGraph / LangChain | 0.3+ | 多智能体编排与工具调用 |
| 向量检索 | Milvus + BGE-M3 | — | 研报/公告知识库 |
| 定时调度 | APScheduler | 3.10+ | 定时任务 |
| 日志 | loguru | 0.7+ | 结构化日志 |

### 前端

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue.js | 3.4+ | 前端框架 |
| 构建工具 | Vite | 5.4+ | 开发与构建 |
| 状态管理 | Pinia | 2.2+ | 全局状态 |
| 图表库 | ECharts | 5.5+ | K线、雷达、柱状图等 |
| 大屏组件 | @kjgl77/datav-vue3 | 1.0+ | 大屏边框与装饰 |
| HTTP客户端 | axios | 1.7+ | API请求 |

### 数据源

| 数据源 | 费用 | 注册 | 定位 |
|--------|------|------|------|
| **Baostock** | 完全免费 | 无需注册 | 主数据源，A股行情财务 |
| **AkShare** | 完全免费 | 无需注册 | 主数据源，多源金融数据聚合 |
| Tushare | 基础免费 | 需注册 | 可选补充，数据质量更高 |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 7.0+
- Docker / Docker Compose（推荐部署方式）

### 1. 克隆项目

```bash
git clone https://github.com/lzc1205/stock-analysis-system.git
cd stock-analysis-system
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入数据库、Redis、大模型 API 等配置
```

```env
# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=stock_warehouse

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 大模型 API（AI 问答功能）
LLM_PROVIDER=doubao
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=doubao-pro-32k
```

> ⚠️ `.env` 含真实凭据，**已被 `.gitignore` 排除，勿提交**。仓库只提供 `.env.example`。

### 3. 初始化数据库

```bash
mysql -u root -p < backend/init_db.sql
```

### 4. 启动后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档：http://localhost:8000/docs

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

### 6. 启动数据采集

```bash
cd backend
python start_data_collection.py
```

---

## 项目结构

```
stock-analysis-system/
├── backend/                          # 后端项目
│   ├── app/                          # FastAPI 应用
│   │   ├── main.py                   # 入口文件
│   │   ├── config.py                 # 配置管理
│   │   ├── api/                      # API 路由（stock / indicator / dashboard / ai_chat）
│   │   ├── models/                   # SQLAlchemy 模型（ODS/DWD/DWS/ADS 共 18 表）
│   │   ├── schemas/                  # Pydantic 数据模型
│   │   ├── services/                 # 业务逻辑层
│   │   └── utils/                    # 工具函数（数据库/缓存/日志）
│   ├── ai/                           # AI 智能问答模块
│   │   ├── llm_client.py             # 大模型客户端
│   │   ├── text_to_sql.py            # Text-to-SQL 生成
│   │   ├── intent_recognition.py     # 意图识别
│   │   ├── answer_generator.py       # 回答生成
│   │   ├── sql_safety.py             # SQL 安全校验（黑名单 + 白名单 + LIMIT）
│   │   ├── prompt_templates.py       # Prompt 模板
│   │   └── knowledge_base/           # 研报/公告知识库（BGE-M3 + Milvus）
│   ├── collector/                    # 数据采集模块
│   │   ├── baostock_collector.py     # Baostock 采集
│   │   ├── akshare_collector.py      # AkShare 采集
│   │   ├── tushare_collector.py      # Tushare 采集（可选）
│   │   ├── cleaner.py                # 数据清洗
│   │   ├── indicator_calculator.py   # 指标计算（TA-Lib + 纯 Python 回退）
│   │   └── scheduler.py              # 定时调度
│   ├── etl/                          # ETL 脚本（ODS→DWD→DWS→ADS）
│   ├── tests/                        # 测试
│   ├── requirements.txt
│   ├── .env.example                  # 环境变量模板
│   ├── init_db.sql                   # 数据库初始化脚本
│   └── Dockerfile
│
├── frontend/                         # 前端项目
│   ├── src/
│   │   ├── main.js / App.vue
│   │   ├── views/                    # 30 个页面
│   │   ├── components/               # 大屏组件（K线/资金流/技术雷达/财务健康度等）
│   │   ├── api/ stores/ router/
│   ├── public/
│   ├── package.json / vite.config.js / Dockerfile
│
├── database/                         # 数据库脚本
├── docs/                             # 文档与截图
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## 数据源说明

本项目以 **免费、安全、合规** 为原则选择数据源：

- **Baostock** —— 完全免费、无需注册，提供 A 股日线/分钟线、财务报表、分红送配、行业分类等数据，稳定性高。
- **AkShare** —— 完全免费、开源，聚合东方财富、新浪、同花顺等公开渠道数据，覆盖范围广，补充性强。
- **Tushare** —— 可选补充，数据质量更高，但需要注册获取 token，高级数据需积分。

> 推荐以 Baostock + AkShare 为主，可满足个人项目 95% 以上需求。

---

## 部署方式

### Docker Compose（推荐）

```bash
docker compose up -d
docker compose ps
docker compose logs -f
```

服务启动后：
- 前端大屏：http://localhost
- 后端 API：http://localhost/api
- API 文档：http://localhost/api/docs

### 手动部署

分别启动 MySQL、Redis、后端（uvicorn）、前端（nginx 托管 dist），通过 `nginx.conf` 配置反向代理。

---

## 已知限制

写清楚边界，避免误解：

- **数据源为第三方免费接口**，稳定性与字段口径随上游变化，商用前需自行评估。
- **未接入实时行情**，当前为日线级别的 T+1 数据，不适用于盘中交易决策。
- **AI 问数依赖大模型服务**，需自备 API Key；模型不可用时其余功能不受影响。
- **策略回测为简化实现**，未考虑滑点、手续费与冲击成本，回测收益不代表实盘表现。
- **Milvus 知识库为可选组件**，不启动时口径类问题会直接走拒答分支。

---

## 免责声明

本项目仅供学习研究和个人数据分析使用，不构成任何投资建议。

- 项目所使用的数据均来自公开免费渠道，数据的准确性、完整性和及时性以数据源官方为准。
- AI 智能问答生成的所有内容均由大模型自动生成，仅供参考，**不构成投资建议**。
- 股市有风险，投资需谨慎。使用者应自行判断并承担投资决策的全部风险与后果。
- 本项目作者不对因使用本系统而导致的任何直接或间接损失承担责任。

---

## License

[MIT](LICENSE)
