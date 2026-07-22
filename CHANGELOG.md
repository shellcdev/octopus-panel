# 版本变更日志

## v3.1.35 · discussion-examples.md 案例瘦身（2026-07-22）

- **问题**：`references/discussion-examples.md` 达 84.7KB（references 最大文件），含 28 个 ## 段、19 个完整案例，其中虚构四连（一-四）、收敛对比（B/C）、插话机制（D/G 与 F 重叠）、角色验证五连（J-M 与 N 同构）存在大量冗余示范。
- **瘦身**：删 10 个 ## 段（案例三/四/B/C/D/G/J/K/L/M），保留一/二/A/E/F/H/I/N/★/O + 3 边界 + 诊断全流程；体积 84.7KB → 51.2KB（−40%）。同步收敛 TOC、案例索引表、分类说明、实测对比表、角色验证汇总段；头部计数「19个」→「10个」；H/I 段内对 C/D 的对比提及保留（教学参照，非死链）。
- **零断链**：案例A/F（rules-discussion.md 引用）、案例N（README/templates.md 引用）均保留；`audit_links.py` 复扫 exit 0（真死链 0）。

## v3.1.34 · scripts 合并（audit_* / role_verify_alias / growth_*）（2026-07-22）

- **合并**：① `audit_all.py` + `audit_docs.py` + `audit_orphans.py` + `role_verify_alias.py` → `audit.py`（子命令 `docs`/`alias`/`orphans`/`all`，`--strict` 供 CI）；② `growth_backup.py` + `growth_migrate.py` + `growth_render.py` → `growth_tool.py`（子命令 `backup`/`migrate`/`render`，业务逻辑仍复用 `growth_api.py`）。净减 5 个脚本（15→10）。
- **依赖面核查**：`growth_api.py` 模块引用链、README 运维命令、SKILL.md 索引均同步更新；`role_generate.py` 的 `QUESTION_TYPE_MAP` 仅在模块级被 import，无文件级断链。
- **link_audit 白名单扩展**：CHANGELOG 整文件内 `scripts/`、`references/` 引用统一豁免（历史变更流水，非活引用）；原 `split_skill.py` 单条豁免并入此规则。
- **验证**：`audit.py all`/`docs`/`alias`/`orphans`、`growth_tool.py --help` 各子命令运行正常；`link_audit.py` 全仓复扫 exit 0（0 真死链，CHANGELOG 历史引用为常数级豁免）。

## v3.1.33 · 加固 role_verify_alias 常量抽取（2026-07-22）

- **问题**：`role_verify_alias.py` 用正则 `re.search(r'QUESTION_TYPE_MAP\s*=\s*(\{.*?\})')` 从 `role_generate.py` 源码抽取字典再 `ast.literal_eval`。非贪婪匹配遇嵌套括号即截半崩溃，属脆弱解析。
- **修复**：改为直接 `from role_generate import QUESTION_TYPE_MAP`，以模块级常量为单一真相源；删除读源码 + 正则 + `ast` 依赖。字典含嵌套括号也能正确读取。

## v3.1.32 · 修复 config.md 版本头漂移（2026-07-22）

- **问题**：`audit_all` 报「是否全部一致: False / 与文件头版本一致: False」；根因是 config.md 在 v3.1.31 被改动（`workspace_root` 去硬编码 + 示例段）却漏 bump 版本头，停在 v3.1.27，而 SKILL/README/TODO/CHANGELOG 已是 v3.1.31。
- **修复**：config.md 版本头 v3.1.27 → v3.1.32，并将 SKILL/README/TODO 元信息头统一对齐 v3.1.32（包级版本号），消除版本头不一致。

## v3.1.31 · workspace_root 去硬编码（跨机可移植）（2026-07-22）

- **问题**：config.md `workspace_root` 硬编码绝对路径 `C:\Users\Shell\.qclaw\workspace`，提交即泄漏本机用户名，换机不可用。
- **修复**：① `scripts/growth_api.py` 解析循环在剥反引号后增加 `val = os.path.expanduser(val)`，使 config 值中的 `~` 展开为用户家目录（代码默认 `expanduser('~/.qclaw/workspace')` 本就可移植，但 config 有该行时默认不生效，故需解析器支持）；② config.md `workspace_root` 单元格改为 `~/.qclaw/workspace`，示例段 `/home/user/.claw/workspace` 同步改为 `~/.qclaw/workspace`（顺带修正 `.claw`→`.qclaw` 漂移）。
- **验证**：`growth_api._get_config('workspace_root')` → `C:\Users\Shell/.qclaw/workspace`，`growth_dir`/`archive_dir` 解析为真实存在目录；本机行为不变、去除用户名硬编码；`audit_orphans` 0 悬空 0 孤儿。
- meta 头 SKILL/README/TODO → v3.1.31。

## v3.1.30 · 补全角色来源硬约束（硬性规则12 + 转正流程段）（2026-07-22）

- SKILL.md 新增「硬性规则 12 · 角色来源走脚本」：诊断后**必须调用 `role_generate.py`** 产出角色、不得手编角色名；`PROMPT:` 行触发转正决策、未决前不 spawn。补全 v3.1.29「② 角色生成」段未覆盖的硬约束（移植自 v2.0 副本）
- `references/roles-rules.md` 新增「纯生成角色转正流程」段（背景/触发条件/5步流程/边界），使 ② 段与硬性规则12 的链接有效，消除 v3.1.29 遗留的「记住这个角色」模糊指向
- meta 头 SKILL/README/TODO → v3.1.30

## v3.1.29 · SKILL.md 补「角色来源」行为段（对齐 config + v2.0）（2026-07-22）

- **缺口**：v3.1.27 仅在 config.md 还原了 `## 角色来源`（3 键），但 workspace SKILL.md 始终未描述 `role_source_mode` 如何驱动角色生成（v2.0 的 SKILL.md 有，workspace 重构时整段删了），且未指示调用读取该键的 `role_generate.py` → 配置/代码已生效，运行时行为说明断链。
- **修复**：在 SKILL.md 步骤② 后插入「② 角色生成（受 config.md `role_source_mode` 控制）」段，描述 generate/local_priority/local_only 三模式 + 纯生成角色转正机制；转正链到 workspace 已有的「记住这个角色 → 写入 role-templates.md」（不引用 roles-rules.md 中不存在的「纯生成角色转正流程」子节，避免新断链）。
- **验证**：SKILL.md 现含 `role_source_mode` 引用且指向 config.md `角色来源`；meta 头 + CHANGELOG 对齐 v3.1.29。

## v3.1.28 · 修复模板库占位行被误当角色（2026-07-22）

- **缺陷**：`references/role-templates.md` 末尾格式示例占位头 `### [emoji] [角色名]（[职位/定位]）` 被 `role_generate.py` 与 `role_verify_alias.py` 当作真实角色解析，导致模板兜底候选池混入名为 `[角色名]` 的垃圾角色，且别名校验虚增计数（37→实为 36）。
- **修复**：两脚本解析 `### ` 角色头时跳过含 `[` / `角色名` 占位符的行。
- **验证**：`role_verify_alias` 角色名集合由 37 降为 36；`audit_orphans` 0 悬空 0 孤儿。

## v3.1.27 · 还原角色来源配置段（2026-07-22）

### 修复（跨副本对齐 v2.0）
- **还原「角色来源」配置段**：v3.1.26 在「成长系统偏好」重构中整段丢失 `## 角色来源`（3 键），但 README.md:140/142 仍在教用户改 `role_source_mode` / `pure_generated_handling`（已不存在的键）→ 配置静默失效。本次从 v2.0（config v3.1.15）移植回 3 键：`role_source_mode`(generate/local_priority/local_only) / `role_extract_merge`(true/false) / `pure_generated_handling`(ask/no)。
- **结构对齐 v2.0 的 5 类布局**：原「成长系统偏好」（7 键）拆回「角色成长」(4 键) + 「关系网络」(2 键，含开关子节与 ⚠️ role_source_mode 交互注)；`topic_slug_length` 从成长段移至「输出与校验」，使该段计 2 键。现结构：路径6 / 角色来源3 / 角色成长4 / 关系网络2 / 输出与校验2 = 17 键，README.md:76 声明成立。
- **附带补全**：关系网络段补回 v2.0 的 ⚠️ 交互说明（generate 默认下角色不写 growth_record → 关系网永无数据 → 即便 enabled 也空置），解释默认配置下关系网"开了却没内容"的根因。

### 验证
- config 键数实测：路径6 / 角色来源3 / 角色成长4 / 关系网络2 / 输出与校验2（5 类共 17 键）；调度预设另 2 键
- README.md:76「5类共17个配置键」声明现与实际一致；README:140/142 引用的 `role_source_mode` / `pure_generated_handling` 现已真实存在
- 无 成长系统偏好 悬空引用（该段标题已移除，外部仅引用键名）

## v3.1.26 · scripts 命名规范化（2026-07-22）

### 优化
- scripts/ 命名统一为 `域_动词` 约定，消除混合风格与草稿散兵（全仓库 `git mv` 保留历史）：
  - `scan_orphans.py` → `audit_orphans.py`（审计域前缀统一，与 audit_all/audit_docs 同族）
  - `generate_roles.py` → `role_generate.py`、`export_role.py` → `role_export.py`、`validate_role.py` → `role_validate.py`、`verify_alias.py` → `role_verify_alias.py`、`role_tester.py` → `role_test.py`（角色域前缀前移 + `-er`→动词）
  - `growth_renderer.py` → `growth_render.py`、`backup_growth_data.py` → `growth_backup.py`、`migrate_growth_data.py` → `growth_migrate.py`（成长域前缀前移 + 去冗余 `data`）
  - `archive_discussion.py` → `discussion_archive.py`（讨论域前缀前移）
- 清理草稿：`_verify.py`（未跟踪、零引用、无 `__main__`）从 scripts/ 删除
- `growth_api.py` 为唯一 hub，保持不变；import / subprocess / 文档中所有旧名引用同步更新

### 修复（重排中发现的真实 bug）
- `growth_api.py` 补 `import re`：`_is_local_role_name` 用 `re.finditer`（L115）但此前漏导入，是潜在 NameError，借本次全量引用替换发现并修复

### 验证
- 全仓库旧名引用清零（`role_role_verify_alias` 双前缀已归一化）；`audit_orphans` 悬空引用 0
- `audit_all` 仅余 `references/*` per-doc 版本 WARN（设计内，非缺陷）
- 14 模块 import OK；`role_verify_alias` 校验 `QUESTION_TYPE_MAP`（27 角色）PASS

## v3.1.25 · 健壮性缺陷收口（2026-07-22）

### 修复
- 🔴 **话题分类覆盖（P2）**：`_classify_topic` 类别集从 4 类扩到 8 类（对齐 role-templates 8 组角色），新增 `legal`/`medical`/`education`；`_CATEGORY_MATRIX` 同步补 3 行互相关性与既有 4 类映射。归档时 `topic` 改存**原文**（`args.question`）而非截断 slug，修复相关性权重对医疗/法务/教育及丢词讨论恒返 `general` 的退化（spawn 注入失准）。教育类置于 family 之前，避免「孩子升学」误归 family。
- 🔴 **归档目录回退配置（P2）**：`discussion_archive.py --output` 缺省从相对 cwd 的 `memory/octopus-archive` 改为回退 `config.archive_dir`（保留显式 `--output` 覆盖），修复换 cwd 跑归档落到错误目录。
- 🔴 **损坏 JSON 救援（P2）**：`_read_growth_record` 在 `JSONDecodeError` 分支先把损坏文件 `cp` 为 `.corrupt-<ts>.bak` 再返 `[]`，保留现场供 `restore_all`（原 read-modify-write 清空后才 backup，已不可逆）。
- 🟡 **半角 [TAG] 正则（P3）**：`calc_role_differentiation` 半角分支 `$$` 误写为行尾锚点，改为 `\[`/`\]`，半角 `[TAG] NAME：` 日志现可正常抽取角色名。
- 🟡 **UTF-8 重包装（P3）**：`tag_filter`/`growth_render`/`role_test`/`discussion_archive` 头部补 `sys.stdout` UTF-8 重包装守卫（与另 5 脚本一致），防中文 Windows cp936 下 `print` CJK 崩溃。

### 验证
- `_classify_topic` 10/10 单测通过（含教育优先于家庭边界）；损坏备份探针生成 `.corrupt-*.bak`；audit_all/audit_orphans/role_verify_alias 无回归；5 模块 import OK。

## v3.1.24 · scripts 缺陷修复与去重（2026-07-22）

### 修复
- 🔴 修复 growth_api.py config.md 解析 bug：`key=parts[1]` 未剥反引号，导致换机器改 `workspace_root`/`growth_dir`/`archive_dir` 无效（`_get_config('topic_slug_length')` 原返回 `''`，修复后返回 `'6'`）
- 角色数校正：声明「8组37个角色」→「8组36个角色」（role-templates.md:899 `### [emoji] [角色名]` 为格式说明行，非角色卡；audit_docs 一并排除该格式行）
- 修审计误报：audit_all.py 新增捕获 `是否全部一致: False` 信号，不再误报 PASS
- 悬空引用：补建 `references/role-templates-archive.md`（归档区）；CHANGELOG 标注 `scripts/split_skill.py` 未纳入版本管理
- 重复代码下沉：本地角色判定统一到 `growth_api._is_local_role_name`（role_generate / discussion_archive 共用）；删除 role_generate 的死数据 `ROLE_ALIAS`，role_verify_alias.py 改为校验 `QUESTION_TYPE_MAP` 映射完整性

## v3.1.23 · 跨文档一致性修复（2026-07-22）

### 修复
- 补 CHANGELOG 缺口：追平 v3.1.20（Emoji 语义规范+排版优化）、v3.1.21（逻辑结构优化：TOC+核心流程上移+参考索引去重）、v3.1.22（冗余分析：反馈通道去重，移出 SKILL.md 仅留 README）三条历史条目
- README 角色模板库描述校正：「10组40个角色」→「8组36个角色」（实际 8 个角色分组、36 个角色卡；role-templates.md:899 `### [emoji] [角色名]` 为格式说明行，不计入角色）
- Meta 文档版本头对齐：README / TODO / config / CHANGELOG 同步至 v3.1.23（SKILL 为权威版本号）

## v3.1.22 · 冗余分析：反馈通道去重（2026-07-22）

### 优化
- 删除 SKILL.md 内联的 `# 💬 反馈通道` 段（与 README `# 📬 反馈通道` 文本重复），仅保留 README 副本；同步移除 TOC 第 11 条

## v3.1.21 · 逻辑结构优化（2026-07-22）

### 优化
- 新增「本文结构」TOC 导航
- 「核心流程（6步）」上移至总览之后作为主干骨架
- 合并两处重复文件索引表为单一「参考文件索引」
- 「快速模式」三处表述收敛为规则体系下单一子节

## v3.1.20 · 新增 Emoji 语义规范 + 文档排版优化（2026-07-22）

### 新增
- README 新增 Emoji 语义规范（视觉语义标记统一）
- 文档排版优化

## v3.1.19 · 轮次去目标化（收敛驱动）（2026-07-22）

### 修复
- 订正「讨论轮次」定位：轮次是**问题复杂度×收敛结果**的涌现量，不再设轮次目标/上限；停止唯一闸门= summary-format.md 动态终止机制（6出口）。删除「2轮默认/1-4轮/标准2轮/默认1轮直出/≤2轮硬闸第3轮升stable」等把轮次当目标的表述；用户可显式指「N轮」(约定长度提示)或「聊到收敛为止」(解除轮次暗示)。balanced 升 stable 触发从「第3轮」改「长拉锯多轮未收敛」

## v3.1.18 · schedule_mode 定义轴校正（2026-07-22）

### 修复
- 订正 `schedule_mode` 的**定义轴**：它只控制「是否/如何使用子 agent」（spawn 机制），不再把「时延优先/快结果」当定义——快结果只是不 spawn 的**派生效果**。SKILL.md 表格/balanced 节/注释、config.md 调度预设/档位适配表 全部改为 spawn 行为为轴、时延为派生

## v3.1.17 · 术语口径统一（2026-07-22）

### 修复
- 全量将残留的 Token 术语改为**时间/时延**口径，与 schedule_mode 优化轴（时延优先/快结果）对齐：SKILL.md「字数硬截断」由「Hard Token Limit」改「防拖长时延」，明确其作用是压低整体生成时延

## v3.1.16 · 调度三档 + 引用校验实装（2026-07-22）

### 新增
- **调度档位执行分支（schedule_mode 实装）**：SKILL.md 新增「🧩 调度档位执行分支」节，stable（真子 Agent 逐角色 spawn）/ balanced（复合 Prompt 单次模拟 + 虚拟隔离墙三技术：状态切换标记 / 负向约束注入 / 字数硬截断）/ auto（按议题复杂度选档，阈值 `schedule_auto_switch_threshold` 默认 0.7）；fast 并入 balanced，极速呈现由正交快速模式承担；硬规则 #11 约束选档
- **cite_verify 引用校验实装**：SKILL.md 硬规则 #10 + references/templates.md「🔍 引用校验指令」节 + references/summary-format.md「未核验风险标注」节 + references/rules-discussion.md 白帽行标注

### 配置
- config.md `schedule_mode` 由 4 档改 3 档并标记已实装；`cite_verify` 标记已实装；新增 `schedule_auto_switch_threshold` 默认 0.7
- config.md 版本 → v3.1.16

### 提交
- `3b52ee2`（commit + 推裸仓 main；与 v3.1 tag 同线）


## v3.1 · 格式统一（2026-06-12）

### 修复
- **共识进度条升级为 10 格**：templates.md / rules-discussion.md / jargon.md，判定标准调整为每轮+10%
- **对峙型总结优先级分级**：summary-format.md 补入高/中/低三级，与六维框架总结格式统一

## v3.0 · 角色成长系统（2026-06-10）

> 6 个 Phase，5 次提交，逐层构建。

| Phase | 提交 | 核心交付 |
|-------|------|---------|
| **Phase 0** 🏗️ | `f4310fc` | `growth_api.py` — 7个核心接口（立场履历/关系网络/成就/标签/EXP/注入/备份）+ `growth_migrate.py` + `growth_backup.py` + `config.md` 成长键 |
| **Phase 1** 🚀 | `c6f320f` | 紧凑履历渲染 + spawn inject MVP（light 模式单条注入） |
| **Phase 2** 🏷️ | `b36e9af` | 8个自动标签规则 + 议题相关度排序 + `auto-tag-rules.md` 规则库文档 |
| **Phase 3** 🌳 | `a6256f4` | `growth_render.py` — 完整成长卡片（7段：等级→成就墙→成长树/心路→职业事件→关系网络→统计仪表盘→标签墙） |
| **Phase 4** 🧠 | `64921bb` | deep 模式（top 3 注入 + 话题相关度矩阵 + 选择性遗忘）+ 影响力权重公式 |
| **Phase 5** 🎉 | `33424f0` | `role_export.py` 角色集市（导出脱敏 + 导入重置 Lv.1）+ 生涯事件检测（6 种里程碑） |

### 新增文件
- `scripts/growth_api.py`（975行，7个API）
- `scripts/growth_render.py`（321行，7段渲染）
- `scripts/role_export.py`（170行，集市I/O）
- `scripts/growth_migrate.py`（130行，Schema迁移）
- `scripts/growth_backup.py`（101行，备份/还原）
- `references/auto-tag-rules.md`（140行，8标签规则）
- `references/growth-formula.md`（量化公式参考）

### 修改文件
- `discussion_archive.py` — 集成成长更新、评分卡计算、备份触发
- `config.md` — 新增成长系统运行时键
- `templates.md` — 角色卡注入立场历史
- `SKILL.md` / `README.md` — 文件索引更新

---

## v2.18（2026-06-09）

### 新增
- 角色成长系统规格文档完成（v1.4）
- 少数派异议总结格式升级（双变体：坚决型 + 说服型）
- 新增4份实测报告（帽子优化/结对帽子轮/少数派异议/结对红帽）
- 新增案例 J-N（虚构·角色验证，覆盖5组首次出场角色）

### 变更
- 路径重构：`memory/octopus/{archive,growth}/`
- 归档文件名改为 `YYYYMMDD-{topic}.md`（≤6字议题摘要）
- 结对模式适用范围修正
- 总结格式分档表新增少数派异议型

### 实测验证
- 结对+帽子轮兼容 ✅
- 帽子轮上限2→5 ✅
- 绿帽共识跳跃公式 ✅
- 少数派异议型总结格式 ✅

---

## v2.15（2026-06-09）

### 新增
- **六帽轮次滤镜**：讨论中可切换6顶思考帽子（白/红/黑/黄/绿/蓝）
- **讨论质量评分卡**：5维评分（逻辑严谨性/立场一致性/证据充分性/建设性/共识推进）
- 新增 `scripts/discussion_archive.py` 评分卡功能

### 关键设计
- 蓝帽触发门槛：连续2轮触发（对齐系统检查节奏）
- 绿帽回锚：[绿]标签例外规则（可引用但不翻转立场）
- 黄帽+对抗位：分角色处理（数据型→正面魔鬼代言人 / 情绪型→降为普通位）

---

## v2.13（2026-06-08）

### 架构重构
- `SKILL.md` 拆分：1353行 → 288行核心 + 4个 `references/` 子文件
  - `rules-discussion.md`（讨论规则）
  - `summary-format.md`（总结格式）
  - `roles-rules.md`（角色规则）
  - `rules-collab.md`（协作规则）
- 新增 `scripts/split_skill.py`（用于 SKILL.md 拆分；该脚本未纳入版本管理，仅历史记录）

### 新增文档
- 点名机制/角色插入/讨论板格式/阶段性小结/收敛机制/异常场景 等详细规则

---

## v2.12（2026-06-08）

### 新增
- **[绕]标签**：角色巧妙避开正面冲突的规则
- **快速模式开关**：跳过观点萃取/共识进度/彩色标识
- **结对辩论并行spawn**：第1轮同对角色可并行生成
- **真人插话增强**：引用深度分级/石叔复述确认/任意轮次间隙插话
- **角色替补机制**：连续2轮违反风格锁/用户主动替换

---

## v2.11（2026-06-08）

### 新增
- **[怼]标签升级**：允许反问和方法论攻击
- **[让]标签**：3个触发条件（明确表达让步/放弃原有立场/支持对方方案）
- **动态终止机制**：共识收敛完成出口（≥70%+≥1个[让]）/ 讨论饱和出口
- **config.md**：运行时路径配置（替换硬编码路径）
- 新增案例 A/B/C（单向收敛/对峙不收敛/快收敛）

---

## v2.10（2026-06-08）

### 讨论板升级
- 冲突角色彩色标识（🔴高冲突 / 🟡中冲突）
- 长内容折叠（≥3轮默认展示最新4轮）
- 观点萃取（每轮后追加1句话核心观点）

### 总结格式升级
- 可执行下一步分级（🔴高/🟡中/🟢低）
- 多话题场景支持（按主话题/子话题分块）
- 观点汇总附录（角色立场表 + 未解决问题 + 可执行下一步）

---

## v2.9（2026-06-08）

### 新增讨论模式
- **混合讨论模式**：串行+结对 / 分组+圆桌 / 结对+圆桌
- **长讨论收敛机制**：轮次≥4轮且未达成共识时，提炼核心争议点
- **多人联动点名**：批量点名（`@全体`/`@正方三人`）/ 链式点名（`A→B→C`）
- **角色灵活插入**：临时插播 / 角色替补

---

## v2.8（2026-06-08）

### 角色模板升级
- **专业领域支持多选**（用、`分隔，最多3个）
- 匹配规则更新：用户专业领域中至少有1个匹配即推荐该角色

---

## v2.7（2026-06-08）

### 角色模板重构
- 新增**专业领域**字段（必填，20个选项）
- 删除**风险偏好**字段（推断准确率未达标准）
- 核心建议向量从3维改为2维（方向 + 紧迫性）

---

## v2.4（2026-06-08）

### 新增
- **角色模板库管理规则**：新增/删除/修改/查看角色模板的操作流程
- **异常场景11/12/13**：角色拒绝发言 / 用户中途换问题 / 角色发言语言错误

---

## v2.3（2026-06-08）

### 新增
- **异常场景10**：用户沉默（连续2轮未发言 → 询问 → 提供选项 → 生成总结）
- 支持"纯观察模式"（用户可只看不参与）

---

## v2.2（2026-06-08）

### 修复
- 主持人模式退出格式（补充讨论板标注格式）
- 真人插话处理（区分回合制和实时讨论）
- 删除不可实现的主持人权限（查看AI思考过程）

---

## v2.1（2026-06-08）

### 新增
- **多人实时协作模式**：
  - 真人+AI混合讨论（真人角色标记`[真]`）
  - 主持人模式（真人接管石叔权限）
  - 群聊场景适配（真人随时插话，AI实时响应）
  - 线下会议场景适配（投影AI角色）

---

## v2.0（2026-06-08）

### 副冰机制升级
- 副冰必须保持中立（不能有自己主导的提案）
- 副冰有利益冲突 → 取消资格，另指派临时冰
- 副冰申请被拒 → 冷却期1轮
- 附议不足时强制指派临时冰验证

---

## v1.9（2026-06-08）

### 新增
- **共识进度**双展示（字符进度 + 百分比），停滞≥2轮时变红提示
- **冰培养副冰机制**（冰离场前必须指定副冰，防单点故障）

---

## v1.8（2026-06-08）

### 新增
- **讨论阶段识别与干预**：
  - 三阶段模型：阶段1（该不该）/ 阶段2（怎么）/ 阶段3（收敛）
  - 阶段2卡住检测：连续2轮无让步 → 引入外部角色或强制换角度

---

## v1.7（2026-06-08）

### 新增
- **场景9**：软肋触发规则
- **外部角色机制**：跨组借用，每场最多1个
- **@点名联动规则**：讨论板`↳`行自动渲染
- 讨论案例 +2（共6个）

### 修复
- 场景8改写为连续重复 + 非连续重复双检测
- 共识进度条量化为3维向量公式
- 诊断字数/终止机制描述与实际行为对齐

---

## v1.6（2026-06-07）

### 新增
- 家庭组 +2 角色（年轻人伴侣/邻居王阿姨）
- 创业组替换为独立角色（天使投资人老钱/连续创业者老孙）

### 修复
- 家庭组从2角色扩展为4角色，解决冲突不足

---

## v1.5（2026-06-07）

### 新增
- 补6个缺失角色（医疗组/法律组/创业组各2个）
- 医疗决策组/法律风控组/创业组 完整（各4角色）

---

## v1.4（2026-06-07）

### 修复
- 风格锁去重（安全老王/医生老李/合规官小刘/冰 约束完全不同）
- 版本号全统一（所有文件头 v1.0 → v1.4）
- README 角色数修正（28 → 35）

---

## v1.3（2026-06-07）

### 新增
- **全维度角色标签体系**（6类：立场/视角/风格/场景/冲突强度/状态）
- 所有角色模板加入标签行
- **标签筛选器** `tag_filter.py`
- SKILL.md 新增标签筛选器章节

---

## v1.2（2026-06-07）

### 修复
- 版本号统一（所有文件头 v1.0 → v1.2）
- README 角色数修正（28 → 25）

> 📌 v1.2 为纯修复版本，未单独发布 skill 包。

---

## v1.1（2026-06-07）

### 新增
- **量化判定标准**（立场对立公式/风格锁判定/角色质量自检）
- **L1/L2/L3 错误恢复机制**
- **讨论归档机制**
- 4个辅助脚本（`role_generate.py` / `role_validate.py` / `discussion_archive.py` / `role_test.py`）
- 所有 .md 文件加版本头

### 修复
- 共识进度条自动计算规则
- 角色对立性强制验证

---

## v1.0（2026-06-07）

### 首次发布
- **核心机制**：角色卡/风格锁/@点名/石叔总结
- **四种讨论模式**：串行/结对/分组/圆桌
- **动态角色生成 SOP** + 前置风控三问
- **9组角色模板**（35个角色）
- **讨论板升级版**（可视化标记/共识进度条）
- **8个异常处置场景**
- **5个辅助脚本**

---

**图例说明**：
- ✅ 已验证
- 📌 纯修复版本
- 🎯 核心功能
- 🔧 技术改进
- 🐛 修复问题
