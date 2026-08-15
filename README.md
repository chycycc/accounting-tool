# 记账账本

一个基于 Flask 的本地 Web 记账工具，专为过磅称重场景设计。

## 功能特性

### 📝 记录管理
- **单条录入**：逐条添加每日过磅数据
- **批量录入**：一次填入整月数据，自动计算
- **批量删除**：勾选多条记录一键删除
- **智能解析**：支持多种输入格式
  - `750×5+422` → 展开为 750,750,750,750,750,422
  - `183包` → 自动换算为 kg（40包 = 1吨）
  - `670 800 670 670` → 空格分隔

### 📊 报表统计
- **月度汇总**：天数、总kg、总吨、总金额
- **年度报表**：各月汇总 + 全年合计
- **趋势图表**：折线图（金额趋势）+ 柱状图（金额对比）
- **按单价拆分**：不同价位的统计数据

### 📥 导出功能
- 导出月份明细 Excel
- 导出年度报表 Excel
- 自动带公式，用 Excel 打开即计算

### ⚙️ 设置管理
- 单价档位管理（增删）
- 支持多单价并存（150/180/300 元/吨等）

### 🎨 界面特色
- 深色/浅色主题切换
- 工业风设计（JetBrains Mono 等宽数字）
- 移动端自适应
- 本地存储，数据不怕丢

## 快速开始

### 1. 安装依赖

```bash
pip install flask openpyxl
```

### 2. 启动服务

```bash
cd accounting-tool
python app.py
```

### 3. 打开浏览器

访问 http://localhost:5000

## 项目结构

```
accounting-tool/
├── app.py              # Flask 后端
├── data.json           # 数据存储（自动生成）
├── requirements.txt    # Python 依赖
├── static/
│   └── style.css       # 样式文件
└── templates/
    └── index.html      # 前端页面
```

## 数据格式

数据存储在 `data.json` 中：

```json
{
  "prices": [150, 180, 300],
  "records": {
    "2026-07": [
      {
        "id": "abc123",
        "date": "7.1",
        "raw": "670+800+670+670",
        "kg": 2810,
        "price": 150
      }
    ]
  }
}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| GET | `/api/prices` | 获取单价列表 |
| POST | `/api/prices` | 添加单价 |
| DELETE | `/api/prices/<id>` | 删除单价 |
| GET | `/api/months` | 获取所有月份 |
| GET | `/api/records?month=2026-07` | 获取某月记录 |
| POST | `/api/records` | 添加记录 |
| DELETE | `/api/records/<id>` | 删除记录 |
| GET | `/api/report?year=2026` | 获取年度报表 |
| GET | `/api/export?month=2026-07` | 导出月份 Excel |
| GET | `/api/export_report?year=2026` | 导出年度 Excel |

## 技术栈

- **后端**：Python Flask
- **前端**：HTML + CSS + JavaScript
- **图表**：Chart.js
- **字体**：Inter + JetBrains Mono
- **存储**：本地 JSON 文件

## 注意事项

- 数据保存在本地 `data.json`，请勿手动删除
- 首次运行会自动创建数据文件
- 服务运行期间可随时在浏览器操作
- 支持手机访问（自适应布局）
