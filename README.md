# 个股金融数据仓库与可视化大屏系统

> 基于 Python + Vue3 的全栈个股金融数据分析平台，集成多源数据采集、数仓分层建模、可视化大屏与 AI 智能问答。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.4-green)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [数据源说明](#数据源说明)
- [AI 智能问答](#ai-智能问答)
- [部署方式](#部署方式)
- [免责声明](#免责声明)

---

## 功能特性

| 模块 | 功能说明 |
|------|---------|
| **多源数据采集** | 支持 Baostock、AkShare（主）、Tushare（可选）多源 A 股数据采集，覆盖日线行情、财务报表、资金流向、行业分类 |
| **数仓分层建模** | 严格遵循 ODS → DWD → DWS → ADS 四层架构，数据可追溯、可复用 |
| **技术指标计算** | 集成 MA / MACD / RSI / KDJ / BOLL 等 150+ 种技术指标 |
| **可视化大屏** | Vue3 + ECharts 打造大屏级展示，含 K 线图、资金流向、技术雷达、财务健康度、行业对比等组件 |
| **AI 智能问答** | 自然语言提问 → Text-to-SQL → 数据查询 → 专业解读，支持多轮对话与投资分析 |
| **定时自动化** | APScheduler 定时采集、增量更新、失败重试，全流程无人值守 |
| **缓存与限流** | Redis 热点数据缓存，接口限流，对话历史管理 |

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
│   MySQL 数据仓库  │  分层建模 ODS / DWD / DWS / ADS          │
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
| 技术指标 | ta (TA-Lib替代) | 0.11+ | 技术指标计算 |
| AI框架 | LangChain | 0.3+ | 大模型应用编排 |
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
# 后端环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入数据库、Redis、大模型 API 等配置
```

关键配置项：

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

# 大模型 API（AI问答功能，推荐豆包大模型）
LLM_PROVIDER=doubao
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=doubao-pro-32k
```

### 3. 初始化数据库

```bash
# 创建数据库并执行建表脚本
mysql -u root -p < backend/init_db.sql
```

### 4. 启动后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt

# 启动 API 服务
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
│   │   ├── api/                      # API 路由
│   │   │   ├── stock.py              # 股票行情接口
│   │   │   ├── indicator.py          # 技术指标接口
│   │   │   ├── dashboard.py          # 大屏数据接口
│   │   │   └── ai_chat.py            # AI 问答接口
│   │   ├── models/                   # SQLAlchemy 模型（ODS/DWD/DWS/ADS）
│   │   ├── schemas/                  # Pydantic 数据模型
│   │   ├── services/                 # 业务逻辑层
│   │   └── utils/                    # 工具函数（数据库/缓存/日志）
│   ├── ai/                           # AI 智能问答模块
│   │   ├── llm_client.py             # 大模型客户端
│   │   ├── text_to_sql.py            # Text-to-SQL 生成
│   │   ├── intent_recognition.py     # 意图识别
│   │   ├── answer_generator.py       # 回答生成
│   │   ├── sql_safety.py             # SQL 安全校验
│   │   ├── prompt_templates.py       # Prompt 模板
│   │   └── knowledge_base/           # 知识库（RAG，可选）
│   ├── collector/                    # 数据采集模块
│   │   ├── baostock_collector.py     # Baostock 采集
│   │   ├── akshare_collector.py      # AkShare 采集
│   │   ├── tushare_collector.py      # Tushare 采集（可选）
│   │   ├── cleaner.py                # 数据清洗
│   │   ├── indicator_calculator.py   # 指标计算
│   │   └── scheduler.py              # 定时调度
│   ├── etl/                          # ETL 脚本
│   │   ├── ods_to_dwd.py             # ODS → DWD
│   │   ├── dwd_to_dws.py             # DWD → DWS
│   │   └── dws_to_ads.py             # DWS → ADS
│   ├── tests/                        # 测试
│   ├── requirements.txt              # Python 依赖
│   ├── .env.example                  # 环境变量模板
│   ├── init_db.sql                   # 数据库初始化脚本
│   └── Dockerfile                    # 后端 Dockerfile
│
├── frontend/                         # 前端项目
│   ├── src/
│   │   ├── main.js                   # 入口
│   │   ├── App.vue                   # 根组件
│   │   ├── views/
│   │   │   └── Dashboard.vue         # 大屏主页面
│   │   ├── components/               # 大屏组件
│   │   │   ├── StockOverview.vue     # 个股概览
│   │   │   ├── KLineChart.vue        # K线图
│   │   │   ├── CapitalFlow.vue       # 资金流向
│   │   │   ├── TechnicalRadar.vue    # 技术雷达
│   │   │   ├── FinancialHealth.vue   # 财务健康度
│   │   │   ├── IndustryCompare.vue   # 行业对比
│   │   │   ├── MarketAnalysis.vue    # 市场分析
│   │   │   └── AIChatAssistant.vue   # AI 问答对话
│   │   ├── api/                      # API 请求封装
│   │   ├── stores/                   # Pinia 状态管理
│   │   └── router/                   # 路由
│   ├── public/                       # 静态资源
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile                    # 前端 Dockerfile
│
├── database/                         # 数据库脚本
│   └── migration/                    # 迁移脚本
│
├── docker-compose.yml                # Docker Compose 编排
├── nginx.conf                        # Nginx 反向代理配置
├── .gitignore
└── README.md
```

---

## 数据源说明

本项目以 **免费、安全、合规** 为原则选择数据源：

- **Baostock**：完全免费、无需注册，提供 A 股日线/分钟线、财务报表、分红送配、行业分类等数据，稳定性高。
- **AkShare**：完全免费、开源，聚合东方财富、新浪、同花顺等公开渠道数据，覆盖范围广，补充性强。
- **Tushare**：可选补充，数据质量更高，但需要注册获取 token，高级数据需积分。

> 推荐以 Baostock + AkShare 为主，可满足个人项目 95% 以上需求。

---

## AI 智能问答

系统内置 AI 智能问答助手，支持：

- **自然语言行情查询**："贵州茅台今天涨了多少？"
- **Text-to-SQL**：自动将自然语言转为 SQL 查询数据仓库
- **技术指标解读**："比亚迪的MACD现在是什么状态？"
- **财务分析问答**："招商银行近三年ROE变化趋势如何？"
- **资金流向分析**："今天主力资金流入最多的股票有哪些？"
- **多轮对话**：支持上下文追问

**技术架构：**

```
用户提问 → 意图识别 → Text-to-SQL生成 → SQL安全校验
    → 执行查询 → 结果组装 → 大模型生成解读 → 返回回答
```

**安全机制：**
- 仅允许 SELECT 语句，关键字白名单校验
- 单次查询最多返回 100 行
- 单用户每分钟限流 10 次
- 所有分析回答自动附加免责声明

---

## 部署方式

### Docker Compose（推荐）

```bash
# 配置环境变量后，一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务启动后：
- 前端大屏：http://localhost
- 后端 API：http://localhost/api
- API 文档：http://localhost/api/docs

### 手动部署

分别启动 MySQL、Redis、后端（uvicorn）、前端（nginx 托管 dist），通过 nginx.conf 配置反向代理。

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
