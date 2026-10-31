# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Accounting Tool（本地 Flask 过磅记账工具）
**Last Updated:** 2026-10-31
**Category:** Analytics Dashboard / 数据密集型工具
**Style:** 现代简约 — 干净留白、圆角卡片、柔和阴影、扁平、专业但不沉重
**Design Dials:** Variance 4/10（Balanced / Modern） | Motion 7/10（Standard） | Density 5/10（Standard）

> 本文档反映**代码实际实施状态**。工具初版生成的蓝+琥珀配色、Fira 字体、Enterprise Gateway 营销模式均未采用，已按用户决策（绿色系、双主题、桌面+手机+长辈全场景、动效丰富不牺牲流畅）落地。

---

## Global Rules

### 1. 中性基础令牌（不随主题色变化）

每个明暗主题各有一套中性变量；`--accent*` 系列由 JS 动态覆盖（见下节）。

**浅色（`:root` / `[data-theme="light"]`）**

| Token | Value | 用途 |
|---|---|---|
| `--bg` | `#F8FAFC` | 页面冷白底色 |
| `--surface` | `#FFFFFF` | 卡片面 |
| `--surface2` | `#F1F5F9` | 表头/分段控件底/次级面 |
| `--surface3` | `#E2E8F0` | 悬浮/三级面 |
| `--border` | `#E2E8F0` | 描边 |
| `--text` | `#0F172A` | 主文字 |
| `--muted` | `#5B6B82` | 次要文字/标签 |
| `--danger` | `#DC2626` | 删除/危险 |
| `--danger-dim` | `rgba(220,38,38,0.08)` | 危险淡底 |
| `--success` | `#16A34A` | 成功语义 |
| `--info` | `#2563EB` | 额外账本列等信息色 |

**深色（`[data-theme="dark"]`）**

| Token | Value | 用途 |
|---|---|---|
| `--bg` | `#0A1019` | 深色页面底 |
| `--surface` | `#121B2B` | 卡片面 |
| `--surface2` | `#1B2638` | 次级面 |
| `--surface3` | `#243650` | 三级面 |
| `--border` | `#26394F` | 描边 |
| `--text` | `#F0F6F3` | 主文字 |
| `--muted` | `#93A5BE` | 次要文字 |
| `--danger` | `#F87171` | 危险 |
| `--danger-dim` | `rgba(248,113,113,0.10)` | 危险淡底 |
| `--success` | `#4ADE80` | 成功 |
| `--info` | `#38BDF8` | 信息 |

**设计原则：** 中性色保持干净不"发绿"；主题色（accent）只出现在按钮、图标、选中态、数字强调、链接、录入卡顶条等点缀位置，**不做大面积底色**（表头/标签用中性底，不用绿底绿字）。

### 2. 主题色预设（ACCENT_PRESETS，用户可一键切换）

8 个预设，每个含浅色/深色两套 accent 色。JS 通过 `document.documentElement.style.setProperty` 内联覆盖 CSS 变量。

| ID | 名称 | 浅色 accent / hover | 深色 accent / hover | on-accent（浅 / 深） |
|---|---|---|---|---|
| `forest`（默认） | 深墨绿 | `#166534` / `#15803D` | `#22C55E` / `#4ADE80` | `#FFFFFF` / `#062B16` |
| `emerald` | 翡翠绿 | `#059669` / `#047857` | `#34D399` / `#6EE7B7` | `#FFFFFF` / `#06281F` |
| `mint` | 薄荷绿 | `#10B981` / `#059669` | `#6EE7B7` / `#A7F3D0` | `#FFFFFF` / `#052E23` |
| `teal` | 青碧 | `#0D9488` / `#0F766E` | `#2DD4BF` / `#5EEAD4` | `#FFFFFF` / `#042F2E` |
| `sage` | 灰绿 | `#4D7C5F` / `#3D6650` | `#84A98C` / `#A3B99F` | `#FFFFFF` / `#0F1F16` |
| `lime` | 亮翠绿 | `#16A34A` / `#15803D` | `#4ADE80` / `#86EFAC` | `#FFFFFF` / `#052E16` |
| `blue` | 蓝 | `#2563EB` / `#1D4ED8` | `#60A5FA` / `#93C5FD` | `#FFFFFF` / `#081B2E` |
| `indigo` | 靛蓝 | `#4F46E5` / `#4338CA` | `#818CF8` / `#A5B4FC` | `#FFFFFF` / `#14143A` |

每个预设还包含：
- `dim`：accent 低透明度（约 10–14%），用于选中淡底、聚焦环、图表淡填充
- `ring`：accent 中透明度（约 35–38%），用于焦点环
- `pie`：6 色同色系数组，浅色/深色各一套，供饼图与图表色板使用

### 3. Typography

- **正文/标题字体：** `'Inter', -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif`
- **等宽/数字字体：** `'JetBrains Mono', 'SFMono-Regular', Consolas, monospace`（表格数字、金额、吨数）
- 字体全部**本地离线**（`static/fonts/`，114 个 woff2 + fonts.css），无外部请求
- 基础字号 14px，行高 1.5；数字用 `font-variant-numeric: tabular-nums` 对齐
- 工具推荐的 Fira Code / Fira Sans 未采用：Inter + JetBrains Mono 同气质且已离线，避免重新下载字体

### 4. 圆角 / 阴影 / 间距

**圆角**

| Token | Value |
|---|---|
| `--radius-sm` | `8px` |
| `--radius` | `12px` |
| `--radius-lg` | `16px`（卡片） |
| `--radius-pill` | `999px`（单价按钮、标签、色块） |

**阴影（双主题各自定义）**

| Level | 浅色 | 深色 |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(15,23,42,0.05)` | `0 1px 3px rgba(0,0,0,0.28)` |
| `--shadow-md` | `0 4px 18px rgba(15,23,42,0.07)` | `0 6px 22px rgba(0,0,0,0.34)` |
| `--shadow-lg` | `0 10px 36px rgba(15,23,42,0.13)` | `0 14px 44px rgba(0,0,0,0.46)` |

**间距基准（4px 网格）：** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48；卡片内边距 20–22px，卡片间距 16px。

---

## 主题色切换机制（核心架构）

```
用户点击 .accent-swatch
        ↓
applyAccent(id)
  ├─ currentAccentId = id；localStorage.setItem('accent', id)
  ├─ 取当前明暗主题对应的预设色（themeIsDark() ? preset.dark : preset.light）
  ├─ root.style.setProperty 覆盖 --accent / --accent-hover / --accent-dim / --on-accent / --ring
  ├─ 更新所有色块的 .active 选中态
  └─ 若存在图表实例 → loadReport() 重绘
```

- **持久化：** accent 选择存 `localStorage.accent`，刷新/重开保持；明暗主题存 `localStorage.theme`
- **明暗切换不丢色：** `setTheme()` 内部调用 `applyAccent(currentAccentId)`，按新主题重新取同一预设的对应色板
- **关键约束：** 主题色相关属性（background / color / border-color / box-shadow）**不参与 CSS transition**。CSS 变量整体切换时，颜色过渡会卡死（停在旧值），因此这些属性即时切换；只保留 `transform` 过渡（不依赖主题变量）驱动 hover 上浮/按压
- 初始化：脚本加载即 `renderAccentSwatches()` 渲染色块，随后 `setTheme(savedTheme)` 应用保存的主题与主题色

---

## Component Specs

### Buttons

```css
.btn {
  min-height: 40px; padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-weight: 600; white-space: nowrap;
  transition: transform var(--transition); /* 仅 transform，颜色即时 */
}
.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-hover));
  color: var(--on-accent);
  box-shadow: 0 1px 2px rgba(15,23,42,0.14), 0 3px 10px var(--accent-dim);
}
.btn-primary:hover { transform: translateY(-1px); }
.btn-primary:active { transform: translateY(1px); }
```

变体：`.btn-outline`（中性面+描边，hover 变 accent）、`.btn-danger`、`.btn-success`。
触控场景（窄屏）按钮 `min-height: 44px`。

### 分段标签控件（Tab Bar）

```css
.tab-bar { background: var(--surface2); border:1px solid var(--border);
           border-radius: var(--radius); padding: 4px; }
.tab.active { background: var(--accent-dim); color: var(--accent); }
```

小面积 accent-dim 底 + accent 字提供明确选中反馈（区别于大面积绿底）。

### KPI 卡（记录页汇总条）

```css
.records-summary { display:grid; grid-template-columns: repeat(4,1fr); gap:12px; }
.summary-item { display:flex; align-items:center; gap:12px;
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius-lg); padding:14px 16px; }
.summary-icon { width:40px; height:40px; border-radius:var(--radius);
  background:var(--accent-dim); color:var(--accent); }
```

4 张独立卡，各带一个 accent 图标圆（日历/秤/货车/现金）+ 大数字；hover 上浮。

### Cards

```css
.card {
  background: var(--surface); border:1px solid var(--border);
  border-radius: var(--radius-lg); padding:20px 22px;
  margin-bottom:16px; box-shadow:var(--shadow-sm);
  transition: transform var(--transition);
}
```

- `.card-entry`（录入卡）：`position:relative; overflow:hidden`，`::before` 顶部 3px 渐变条（accent→hover）
- `.card.table-wrap`：内边距 0、溢出隐藏，内嵌表格可横向滚动

### Inputs

```css
input, select {
  padding:9px 12px; border:1px solid var(--border);
  border-radius:var(--radius-sm); background:var(--surface); color:var(--text);
}
input:focus, select:focus {
  border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-dim);
}
```

下拉框自定义箭头 SVG；`focus-visible` 全局环形焦点（`--ring`）。

### Table

- 表头：`var(--surface2)` 中性底 + `var(--muted)` 字，sticky 置顶
- 行：斑马纹（偶数行 `surface2`）、hover 行 `accent-dim` 底
- 数字列等宽字体右对齐；合计行 `accent-dim` 底 + accent 顶边
- 窄屏：表格容器横向滚动，不挤压

### Modals

```css
.modal-overlay { background:rgba(0,0,0,0.5); backdrop-filter: blur(4px); }
.modal { background:var(--surface); border-radius:var(--radius-lg);
         box-shadow:var(--shadow-lg); }
```

弹入动画 `modalIn`；窄屏（600px）底部弹出式、全宽。

### 主题色色块（.accent-swatch）

```css
.accent-swatch { width:40px; height:40px; border-radius:50%;
  border:2px solid transparent; }
.accent-swatch.active { border-color:var(--surface);
  box-shadow:0 0 0 2px var(--text); }
.accent-swatch.active::after { /* 白色对勾 */ }
```

---

## Charts

- 折线/柱状主色取当前 `--accent`；淡填充用 `accent + 透明度`
- 饼图（doughnut，cutout 62%）：色板取当前预设的 `pie` 数组（同色系 6 色），中心显示总额
- 切换主题色或明暗主题：存在图表实例即 `loadReport()` 重绘，色板全部跟随
- 涨跌语义色（环比图）：涨绿/跌红为固定语义，不随 accent 改变
- 图表文字/默认字体跟随 `--muted` 与离线字体

---

## Motion

- **可动属性：** 仅 `transform`（hover 上浮、按压、缩放）参与过渡，时长 0.18s ease
- **颜色/阴影/边框：** 即时切换（CSS 变量切换会卡死过渡，见架构约束）
- 入场：卡片 `fade-in`、弹窗 `modalIn`
- 数字滚动：`animateNumber`（rAF + easeOutCubic），并带 `setTimeout(duration+100)` 兜底，防止 rAF 被暂停时数字不显示
- **`prefers-reduced-motion: reduce`：** 动画/过渡时长降到 0.01ms，渲染静态最终状态

---

## Responsive Breakpoints

| 断点 | 行为 |
|---|---|
| 768px | 标签全宽等分；KPI 卡 2 列；工具栏纵向堆叠 |
| 600px | 表单 `form-group` 全宽；按钮 44px 触控；弹窗底部弹出全宽；KPI 图标/数字缩小 |
| 375px | 按钮文字/间距进一步收紧；表格横向滚动；无水平滚动条 |

长辈/移动端要点：正文≥14px、触控目标 44px、间距 8px 起、选中态可见、焦点环明显。

---

## Anti-Patterns（Do NOT Use）

- ❌ Emoji 当图标 — 统一内联 SVG（Heroicons 线性风格）
- ❌ 绿底 + 绿字大面积铺表头/标签 — 中性底 + 绿色点缀
- ❌ 让背景/文字/边框/阴影参与主题色 transition — 会卡死，只动 transform
- ❌ 扁平与拟物混用、低饱和灰底上的低对比文字（对比度保持 4.5:1）
- ❌ 移除焦点环、图标按钮无可读标签（a11y）
- ❌ 移动端出现横向页面滚动、触控目标小于 44px
- ❌ 依赖外部 CDN 字体/脚本 — 全部本地离线

---

## Pre-Delivery Checklist

- [ ] 无 emoji 图标，SVG 来自统一图标集
- [ ] 可点击元素 `cursor:pointer`，`focus-visible` 焦点环可见
- [ ] 主题色 8 预设切换正常，明暗主题各自适配且选择持久化
- [ ] 颜色/阴影属性无 transition（仅 transform），主题切换无卡死
- [ ] 图表随主题色/明暗主题重绘，饼图色板为当前预设
- [ ] 浅色/深色文字对比度 ≥ 4.5:1
- [ ] `prefers-reduced-motion` 已尊重；数字动画有兜底
- [ ] 响应式 375 / 600 / 768 断点生效，移动端无横向滚动、触控 44px
- [ ] 字体/脚本/图表全部本地离线，无外部请求
