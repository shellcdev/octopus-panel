> 📌 版本：v3.1.37 | 更新：2026-07-22 | 维护者：石叔
>
> 🌐 英文导航版见 **[README.en.md](README.en.md)**（仅导航中枢，细节参考仍以本中文版为准）。

# 八爪议事厅 · 导航中枢

> 新人/运维上手入口。按优先级阅读，不要跳级。

---

## 🔴 必读（第一次使用前）

| 顺序 | 文件 | 读什么 | 何时读 |
|---|---|---|---|
| 1 | `SKILL.md` | 总览、硬性/柔性规则、四种讨论模式、交互指令 | 第一次用 |
| 2 | `references/jargon.md` | 术语通俗释义（风格约束锁/软肋/标签/成长系统） | 第一次用 |

---

## 🟡 建议读（生成/参与讨论时）

| 文件 | 读什么 | 何时读 |
|---|---|---|
| `references/templates.md` | 角色卡格式、spawn prompt、讨论板格式、阶段性小结格式 | 生成角色前 |
| `references/role-templates.md` | 已验证的角色模板库（8组36个角色） | 生成角色时调用 |
| `references/discussion-examples.md` | 19个完整讨论案例（+3边界+1诊断） | 质量核对或格式参照 |

---


## 📂 文件导航

### 核心文件

- **SKILL.md** — 总览、硬性/柔性规则、四种讨论模式、🎩轮次滤镜、交互指令、反馈通道
- **README.md**（本文件）— 导航中枢
- **CHANGELOG.md** — 版本变更历史
- **config.md** — 运行时配置（5类共17个配置键：路径6 / 角色来源3 / 角色成长4 / 关系网络2 / 输出与校验2）

### references/ 目录

| 文件 | 内容 | 何时引用 |
|---|---|---|
| `jargon.md` | 术语通俗释义（含 v3.0 成长系统术语） | 第一次用 |
| `rules-discussion.md` | 讨论规则（点名/讨论板/小结/收敛/帽子兼容/异常场景1-12） | 讨论进行中 |
| `summary-format.md` | 总结格式（4种类型）+ 量化判定 + 评分卡 | 总结阶段 |
| `roles-rules.md` | 角色管理（选择/增加/替补/模板库/标签筛选） | 生成/替换角色时 |
| `rules-collab.md` | 协作与恢复（多人/L1-L3/归档） | 协作场景 |
| `templates.md` | 标准模板参考（含🎩帽子轮Prompt模板） | 生成角色前 |
| `role-templates.md` | 角色模板库（8组36个角色） | 生成角色时调用 |
| `discussion-examples.md` | 19个完整讨论案例（+3边界+1诊断） | 质量核对/格式参照 |
| `role-templates-archive.md` | 角色模板归档区（退役/合并模板的历史备份） | 查历史模板时 |
| `auto-tag-rules.md` | 🆕 自动标签规则（8标签+置信度公式+生命周期） | 成长系统自动标签判定（默认关闭） |
| `growth-formula.md` | 🆕 成长系统量化公式（EXP/等级/衰减/影响力/成就） | 成长数据调参或审计（默认关闭） |

### scripts/ 目录

| 脚本 | 用途 |
|---|---|
| `growth_api.py` | 🆕 角色成长系统核心数据层（7个API：立场/关系/成就/标签/EXP/注入/备份） |
| `growth_tool.py` | 🆕 成长系统运维总入口（`backup`/`migrate`/`render`；原 growth_backup/migrate/render 合并） |
| `role_export.py` | 🆕 角色集市导出/导入（脱敏处理） |
| `discussion_archive.py` | 讨论归档至知识库 + 评分卡计算 + 成长数据自动更新 |
| `role_generate.py` | 基于问题关键词生成角色草稿卡 |
| `role_validate.py` | 角色卡质量校验（必填字段+启发式风险检查） |
| `role_test.py` | 角色 Spawn 测试（生成测试 Prompt） |
| `tag_filter.py` | 角色标签筛选器（多条件 AND 匹配） |
| `audit.py` | 🆕 文档/一致性审计总入口（`docs`/`alias`/`orphans`/`all`；原 audit_all/docs/orphans + role_verify_alias 合并） |
| `audit_links.py` | 🆕 链接健康扫描（复扫引用死链，0 真死链通过，历史引用豁免） |

---

## 🚀 快速上手

### 🚀 开源用户：先安装（把仓库变成可用技能）

> 本仓库就是技能源码。要让客户端加载它，须放进对应 AI 客户端的 `skills/` 目录。

**OpenClaw（qclaw）**
```bash
git clone https://github.com/shellcdev/octopus-panel.git
# Windows：%USERPROFILE%\.qclaw\skills\   |  Linux/macOS：~/.qclaw/skills/
cp -r octopus-panel ~/.qclaw/skills/
```
重启客户端，直接抛一个两难问题（如"该不该辞职"）即触发圆桌流程。

**WorkBuddy**
1. 克隆/下载本仓库；
2. 放入用户级技能目录 `~/.workbuddy/skills/octopus-panel/`；
3. 重启 WorkBuddy，按 `SKILL.md` 的 `name`（octopus-panel）自动加载。

**验证安装**
- 脚本自测：`python scripts/tests/run_tests.py -q` 应全绿；
- 客户端内：说"用八爪议事厅讨论：XX"或直接抛多方视角问题，应进入圆桌流程。

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

## 🌱 角色成长系统（默认关闭 · opt-in）

> **默认不启用**——这是有意设计，不是 bug。

- **默认行为**：`config.md` 的 `role_source_mode = generate`，每场角色纯动态生成、用完即弃，不写 `growth_record.json`。因此立场履历 / 成就 / 关系网 / 自动标签在默认配置下**不会累积**。
- **如何开启（二选一）**：
  1. 改 `config.md`：`role_source_mode = local_priority`（优先复用有成长史角色，不足角色按 `pure_generated_handling` 提示转正）；想让关系网真正展示，再设 `relationship_network_enabled = true`。
  2. 手动转正：纯生成角色归档时被标记 `suggest_localize`，按提示存库即转持久角色，下场起带入成长史。
- 详见 `references/growth-formula.md`（量化公式）与 `references/auto-tag-rules.md`（标签规则）。

---

## 🛠️ 运维指南

### 维护与审计

1. 改完角色/规则/版本后，跑 `python scripts/audit.py all` 做文档一致性 + 别名校验
2. 改动/增删 `scripts/` 或 `references/` 内文件后，跑 `python scripts/audit_links.py` 复扫链接健康（0 真死链才算通过，CHANGELOG 历史引用为合规豁免）；改了文件名务必同步更新 README 脚本表与 SKILL.md 索引
3. 成长数据在每次归档后由 `discussion_archive.py` 自动调用 `growth_api.auto_backup_if_needed()`（≥24h 一次，循环保留 `backup_keep_count` 份）；手动全量备份用 `python scripts/growth_tool.py backup --backup`，还原用 `backup --restore <file>`
4. 导出/导入角色（角色集市）用 `python scripts/role_export.py <role_id>` / `--import-file <json>`
5. 新角色转正前可用 `python scripts/role_test.py --role-card <card.json> --test-question "..."` 生成风格锁自检 prompt

### 新增角色模板

1. 在 `references/role-templates.md` 对应分组下追加
2. 必须通过前置风控三问
3. 在 `CHANGELOG.md` 记录

### 新增讨论案例

1. 在 `references/discussion-examples.md` 追加
2. 标注"案例N"、讨论问题、完整发言、石叔总结
3. 在 `CHANGELOG.md` 记录

---

## 🎨 Emoji 语义规范

> 文档中使用的 emoji 不是装饰，而是**视觉语义标记**。每张脸对应一种固定的信息类型，全文统一，不随意更换。

### 语义总览

| Emoji | 语义角色 | 用途定义 | 使用场景示例 |
|---|---|---|---|
| 📌 | 元信息 | 版本、更新、维护者等文档元数据 | 文档顶部版本声明 |
| 🐙 | 项目标识 | 八爪议事厅品牌符号、入口提示 | 首次使用引导 |
| 🔴 | 强提醒 | 必读/高风险/不可跳过 | 🔴 必读、硬性规则 |
| 🟡 | 中提醒 | 建议读/需注意/半强制 | 🟡 建议、柔性规则 |
| 🟢 | 轻提醒 | 可选/锦上添花 | 🟢 可选参考资料 |
| 🎩 | 功能插件 | 特殊功能模块标识（六帽滤镜） | 轮次滤镜、功能开关 |
| 🧩 | 功能模块 | 系统功能、调度、机制组件 | 调度预设、调度档位 |
| 🎨 | 视觉标记系统 | 🆕 emoji 语义规范本体、标记体系总览 | Emoji 语义规范段 |
| 🔘 | 开关控制 | 配置开关、模式切换 | 关系网络开关 |
| 🚀 | 快速操作 | 快速上手、速查、捷径 | 快速上手指南 |
| 🌱 | 成长系统 | 角色成长、数据、标签相关 | 角色成长系统说明 |
| 🛠️ | 运维工具 | 维护操作、脚本、审计 | 运维指南、脚本说明 |
| 🤝 | 协作相关 | 多人协作、贡献、社区 | 贡献指南 |
| 📬 | 反馈通道 | 意见反馈、问题报告 | 反馈入口 |
| ⚠️ | 警告/违规 | 规则违反、风险提示 | 硬性规则、⚠️标注 |
| 💡 | 观点/要点 | 核心观点、关键信息 | 前一轮观点摘要 |
| 📜 | 履历/历史 | 立场记录、历史数据 | 立场履历注入 |
| 🔍 | 校验/核验 | 引用校验、事实核查 | 引用校验指令 |
| 🆕 | 新增标记 | 文档/功能新增（含变更日志） | references/scripts 新增条目 |
| 📂 | 文件/目录 | 文件导航、目录结构 | 文件地图 |

### 使用规则

1. **唯一性**：每个 emoji 语义角色在全文档中唯一，不出现同一 emoji 表示多种含义
2. **位置固定**：
   - 章节标题：放在标题左侧（如 `## 🔴 必读`）
   - 正文强调：紧跟关键词后（如 `规则⚠️`）
   - 元信息行：行首独占（如 `> 📌 版本：v3.1.14`）
3. **不重复**：同一行内不超过 2 个 emoji（避免视觉噪音）
4. **不滥用**：没有明确语义的 emoji 不随意使用
5. **新增审批**：需新增 emoji 语义时，先在 CHANGELOG.md 记录并更新本规范

---

## 🤝 贡献指南

欢迎反馈和提交：

- 新增角色模板（需过前置风控三问）
- 新增讨论案例（需完整、含边界场景）
- 优化规则（需说明优化理由 + 影响范围）
- 修复文档错误（typo、断开链接、格式问题）

提交方式：开 Issue 或 PR（详见 [CONTRIBUTING.md](CONTRIBUTING.md)）。

---

## 📬 反馈通道

### 作为使用者（运行技能时）
用完了觉得哪里不好用？直接说 **"反馈：[你的意见]"** ，石叔会记下来下次改。

常见问题：
- 角色发言太模板化 → 反馈给我，我加软肋和触发后状态
- 讨论跑题了 → 反馈给我，我优化诊断环节
- 想要某个垂直行业的角色（如医疗/法律/教育）→ 反馈给我，我加进模板库

### 作为开源贡献者
- 功能建议 / Bug 报告：开 [GitHub Issue](https://github.com/shellcdev/octopus-panel/issues)
- 提交改动：Fork 本仓库 → 修改 → 开 PR（流程见 [CONTRIBUTING.md](CONTRIBUTING.md)）
- 安全漏洞：**勿开公开 issue**，请走 [SECURITY.md](SECURITY.md) 的私报通道
