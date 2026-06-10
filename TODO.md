# 八爪议事厅 · TODO（v2.18 + 角色成长系统 Phase 0-5）

> 最后核验：2026-06-10 | 核验方式：源目录 v2.18 代码 + 角色成长系统 Phase 0-5 全部编码落地（8 commits, 6 phases）
> 基线版本：**v2.18 + 角色成长系统 v1.0**（🎩 六帽滤镜 / 📊 评分卡 / 🔥 8 种模式 / 🧩 37 角色 / 📚 20 案例 / 🌱 角色成长 — 全部已落地，详见 `CHANGELOG.md`）
> 
> 本文档聚焦**剩余的待办项**和**长期演进方向**。

---

## ✅ Phase 0-5 · 角色成长系统（全部编码落地）

角色成长系统完整规格 → 编码完成，提交历史见下：

```
33424f0  Phase 5: 角色生涯事件 + 角色集市导出
64921bb  Phase 4: spawn 深度注入 + 选择性遗忘
a6256f4  Phase 3: 完整档渲染器 growth_renderer.py
b36e9af  Phase 2: auto_tags 规则库 + 议题相关度排序
c6f320f  Phase 1: 立场履历轻量档 MVP
f4310fc  Phase 0: 角色成长系统 API + 数据迁移 + 备份
```

### Phase 0 · 数据模型 + API 解耦 + 系统工程
| 项 | 状态 | 文件 |
|----|------|------|
| `growth_api.py` 新建（7 个接口函数） | ✅ | `scripts/growth_api.py` |
| `archive_discussion.py` 集成 growth_api | ✅ | `scripts/archive_discussion.py` |
| `scripts/migrate_growth_data.py` | ✅ | `scripts/migrate_growth_data.py` |
| `scripts/backup_growth_data.py` | ✅ | `scripts/backup_growth_data.py` |
| config.md 配置项（stance_history/relationship_network 系列） | ✅ | `config.md` |
| 关系线采集（auto/always/never 三模式） | ✅ | `growth_api.py` |

### Phase 1 · 立场履历轻量档 🚀 MVP
| 项 | 状态 | 文件 |
|----|------|------|
| `get_spawn_inject()` 权重排序+round跳过 | ✅ | `growth_api.py` |
| 紧凑图标式履历 `议题(立场)` | ✅ | `growth_api.get_compact_history()` |
| 📈 快速展开入口（行内迷你成长卡片） | 🔲 P2 未实现 | — |

### Phase 2 · auto_tags + 议题相关度
| 项 | 状态 | 文件 |
|----|------|------|
| `update_auto_tags()` 自动打标签（8 规则） | ✅ | `growth_api.py` |
| `references/auto-tag-rules.md` 规则库 | ✅ | `references/auto-tag-rules.md` |
| `get_spawn_inject()` 议题相关度排序 | ✅ | `growth_api.py` |

### Phase 3 · 完整档渲染器 + 关系网络
| 项 | 状态 | 文件 |
|----|------|------|
| 成长树 + 心路总结自动生成 | ✅ | `growth_renderer.py` |
| 关系网络文字展示 | ✅ | `growth_renderer.py` |
| 临时开关"这轮不要关系" | ✅ | `growth_api.set_session_override()` |
| 数据统计模块 | ✅ | `growth_renderer._compute_stats()` |
| 标签墙（自动+手动+置信度） | ✅ | `growth_renderer.py` |
| 条件触发引导 | ✅ | `growth_renderer.render_guidance()` |
| spawn inject 关系信息注入 | ✅ | `growth_api.get_spawn_inject()` |

### Phase 4 · spawn 深度注入 + 选择性遗忘
| 项 | 状态 | 文件 |
|----|------|------|
| `get_spawn_inject()` deep mode（top 3 + 一致性检测） | ✅ | `growth_api.py` |
| `stance_history_skip_sessions` 跳过列表 | ✅ | `growth_api.py` + `config.md` |

### Phase 5 · 角色生涯事件 + 角色集市
| 项 | 状态 | 文件 |
|----|------|------|
| `career_events` 自动检测（最高分/最低分/首次立场变化/里程碑） | ✅ | `growth_api.py` |
| 生涯事件模块渲染 | ✅ | `growth_renderer.py` |
| `scripts/export_role.py` 角色集市导出 | ✅ | `scripts/export_role.py` |
| 角色集市导入 | ✅ | `export_role.import_role()` |

---

## 📋 优先级总览（剩余待办）

| 优先级 | 内容 | 工作量 | 说明 |
|--------|------|--------|------|
| **P2** | 📈 快速展开入口（行内迷你成长卡片） | ~1h | Phase 1 遗留，需要前端可点击展开 |
| **P2** | 🔗 力导向关系网络图 | ~3h | 当前为文字版，升级为前端可视化 |

### #28 · 角色关系网络
> 状态：✅ **已编码落地** — 融合为 Phase 0 + Phase 3
> 提交：`f4310fc` / `a6256f4`

数据采集（Phase 0），展示渲染 + 临时开关 + spawn inject（Phase 3）。

### #33 · 跨讨论角色记忆
> 状态：✅ **已编码落地** — 融合为 Phase 1-5
> 提交：`c6f320f` / `b36e9af` / `a6256f4` / `64921bb` / `33424f0`

立场履历（Phase 1）、议题相关度（Phase 2）、完整展示（Phase 3）、选择性遗忘（Phase 4）、生涯事件（Phase 5）。

---

## ⚠️ 已知格式问题（非阻塞，记录备查）

### 1. 共识进度条仍是 5 格
- **现状**：讨论板共识进度条 `░░▒▒▒ (40%)` 仍是 5 格
- **#23 原方案**：改成 10% 一档 10 格
- **实际**：#23 升级为 #29（观点迁移图），已实现细粒度展示
- **影响**：低，观点迁移图已覆盖需求

### 2. 对峙型总结的"可执行下一步"无分级
- **现状**：六维框架总结有"高/中/低优先级"分级
- **问题**：对峙型总结格式只有"回答这 X 个问题再决定"，无分级
- **影响**：低，格式不统一但不影响功能

---

## 📝 废弃/升级说明

| 原编号 | 处理方式 | 说明 |
|--------|----------|------|
| #18 | 由 #36 覆盖 | 差异化字数上限统一解决 |
| #19 | 升级为 #26 | 增量混合展示 |
| #20 | 升级为 #27 | 对峙型总结格式 |
| #23 | 升级为 #29 | 观点迁移图 |
| #24 | 合并入 #36 | config.md 偏好键一并处理 |
| #25 | 降优先级 | 案例数 <10，手动可查 |
| #A-#G | ✅ **v2.18 已全部落地** | 四轮测试全量验证通过 |
| #40-#48 | ✅ **v2.18 已全部落地** | 帽子优化 7 项全通过 |
| #28、#33 | ✅ **已编码落地** | 分别融合为 Phase 0+3 和 Phase 1-5 |
| 角色成长系统 | ✅ **Phase 0-5 全部编码完成** | 6 commits, 10 files, ~2000 行代码 |

---

## 🗺️ 进化全景图

```
当前（源目录 v2.18 + 角色成长系统 Phase 0-5）
  ├── 🎩 六帽滤镜 ✅
  ├── 📊 评分卡 ✅
  ├── 🔥 8 种讨论模式 ✅
  ├── 🧩 37 个角色模板 ✅
  ├── 📚 20 个讨论案例 ✅
  ├── 🏗️ Phase 0: 数据模型 + API + 备份 ✅
  ├── 🚀 Phase 1: 立场履历轻量档 MVP ✅
  ├── 🏷️ Phase 2: auto_tags + 议题相关度 ✅
  ├── 🌳 Phase 3: 完整档渲染器（成长树+关系+统计）✅
  ├── 🧠 Phase 4: 深度注入 + 选择性遗忘 ✅
  └── 🎉 Phase 5: 生涯事件 + 角色集市 ✅

剩余待办
  ├── 📈 快速展开入口（行内迷你成长卡片）P2
  └── 🔗 力导向关系网络图 P2

长期演进
  ├── 🏪 角色集市生态（高等级角色共享）
  ├── 🎮 游戏化成长（经验值/成就/等级系统）
  └── ✏️ 角色自定义（改名/调立场/加软肋）
```

---

*整理于：2026-06-10*
*参考：源目录 v2.18 / 角色成长系统 Phase 0-5 代码 / git log*