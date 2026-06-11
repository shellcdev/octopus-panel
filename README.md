> 📌 版本：v3.0 | 更新：2026-06-10 | 维护者：石叔

# 八爪议事厅 · 导航中枢

> 新人/运维上手入口。按优先级阅读，不要跳级。

---

## 🔴 必读（第一次使用前）

| 顺序 | 文件 | 读什么 | 耗时 |
|---|---|---|---|
| 1 | `SKILL.md` | 总览、硬性/柔性规则、四种讨论模式、交互指令 | 5分钟 |
| 2 | `references/jargon.md` | 术语通俗释义（风格约束锁/软肋/标签/成长系统） | 2分钟 |

---

## 🟡 建议读（生成/参与讨论时）

| 文件 | 读什么 | 何时读 |
|---|---|---|
| `references/templates.md` | 角色卡格式、spawn prompt、讨论板格式、阶段性小结格式 | 生成角色前 |
| `references/role-templates.md` | 已验证的角色模板库（10组37个角色） | 生成角色时调用 |
| `references/discussion-examples.md` | 20个完整讨论案例（含边界场景） | 质量核对或格式参照 |

---

## 🟡 讨论进行中按需引用

| 文件 | 内容 | 触发时机 |
|---|---|---|
| `references/rules-discussion.md` | 点名机制、角色插入、讨论板格式、阶段性小结、收敛机制、异常场景1-12 | 讨论进行中 |
| `references/summary-format.md` | 石叔总结格式（六维框架）、动态终止、量化判定标准 | 总结阶段 |
| `references/roles-rules.md` | 角色选择、增加角色、角色替补、模板库管理、标签筛选器 | 生成/替换角色时 |
| `references/rules-collab.md` | 多人协作、真人插话、主持人模式、L1/L2/L3恢复、归档机制 | 协作场景 |
| `references/auto-tag-rules.md` | 🆕 自动标签规则（8个标签+置信度公式+生命周期） | 成长系统自动标签判定 |
| `references/growth-formula.md` | 🆕 成长系统量化公式（EXP/等级/衰减/影响力/成就） | 成长数据调参或审计 |

---

## 📖 文件导航

### 核心文件

- **SKILL.md**（474行）— 总览、硬性/柔性规则、四种讨论模式、🎩轮次滤镜、交互指令、反馈通道
- **README.md**（本文件）— 导航中枢
- **CHANGELOG.md** — 版本变更历史
- **config.md** — 运行时路径配置（4个路径键+5个偏好键）

### references/ 目录

| 文件 | 行数 | 内容 |
|---|---|---|
| `jargon.md` | ~530 | 术语通俗释义（含 v3.0 成长系统术语） |
| `rules-discussion.md` | 574 | 讨论规则（点名/讨论板/小结/收敛/帽子兼容/异常场景） |
| `summary-format.md` | 326 | 总结格式（4种类型） + 量化判定 + 评分卡 |
| `roles-rules.md` | 220 | 角色管理（选择/增加/替补/模板库/标签筛选） |
| `rules-collab.md` | 361 | 协作与恢复（多人/L1-L3/归档） |
| `templates.md` | 808 | 标准模板参考（含🎩帽子轮Prompt模板） |
| `role-templates.md` | 919 | 角色模板库（10组37个角色） |
| `discussion-examples.md` | 1632 | 20个完整讨论案例 |
| `auto-tag-rules.md` | 140 | 自动标签规则（8标签+置信度公式） |
| `growth-formula.md` | — | 🆕 成长系统量化公式（EXP/等级/衰减/影响力/成就） |

### scripts/ 目录

| 脚本 | 用途 |
|---|---|
| `growth_api.py` | 🆕 角色成长系统核心数据层（7个API：立场/关系/成就/标签/EXP/注入/备份） |
| `growth_renderer.py` | 🆕 成长卡片渲染器（7段：等级→成就墙→成长树→职业事件→关系→统计→标签） |
| `export_role.py` | 🆕 角色集市导出/导入（脱敏处理） |
| `archive_discussion.py` | 讨论归档至知识库 + 评分卡计算 + 成长数据自动更新 |
| `migrate_growth_data.py` | 🆕 成长数据 Schema 迁移（v1→v2） |
| `backup_growth_data.py` | 🆕 成长数据备份/还原（30份循环） |
| `generate_roles.py` | 基于问题关键词生成角色草稿卡 |
| `validate_role.py` | 角色卡质量校验（必填字段+启发式风险检查） |
| `role_tester.py` | 角色 Spawn 测试（生成测试 Prompt） |
| `tag_filter.py` | 角色标签筛选器（多条件 AND 匹配） |
| `audit_docs.py` | 文档一致性审计（角色数/版本头/CHANGELOG/脚本完整性） |
| `verify_alias.py` | ROLE_ALIAS 映射验证（别名→模板匹配检查） |

---

## 🚀 快速上手

### 第一次用（5分钟）

1. 读 `SKILL.md` 前200行（总览+硬性规则+四种模式）
2. 读 `references/jargon.md` 搞懂术语（2分钟）
3. 直接抛一个问题，石叔带你走一遍完整流程

### 生成角色前（10分钟）

1. 读 `references/templates.md` 角色卡标准格式
2. 读 `references/role-templates.md` 挑合适的角色模板
3. 需要动态生成 → 读 `templates.md` 动态生成SOP

### 调试角色质量时

1. 读 `references/role-templates.md` 前置风控三问
2. 读 `references/summary-format.md` 量化判定标准章节
3. 用 `references/discussion-examples.md` 对比格式和质量

---

## 🛠️ 运维指南

### 修改系统规则

1. 修改 `SKILL.md`（核心规则）或对应的 `references/*.md`（详细规则）
2. 在 `CHANGELOG.md` 记录变更
3. 更新对应文件开头的版本头

### 新增角色模板

1. 在 `references/role-templates.md` 对应分组下追加
2. 必须通过前置风控三问
3. 在 `CHANGELOG.md` 记录

### 新增讨论案例

1. 在 `references/discussion-examples.md` 追加
2. 标注"案例N"、讨论问题、完整发言、石叔总结
3. 在 `CHANGELOG.md` 记录

---

## 🤝 贡献指南

欢迎反馈和提交：

- 新增角色模板（需过前置风控三问）
- 新增讨论案例（需完整、含边界场景）
- 优化规则（需说明优化理由 + 影响范围）
- 修复文档错误（typo、断开链接、格式问题）

---

## 📬 反馈通道

用完了觉得哪里不好用？直接说 **"反馈：[你的意见]"** ，石叔会记下来下次改。

常见问题：
- 角色发言太模板化 → 反馈给我，我加软肋和触发后状态
- 讨论跑题了 → 反馈给我，我优化诊断环节
- 想要某个垂直行业的角色（如医疗/法律/教育）→ 反馈给我，我加进模板库
