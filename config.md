# config.md · 八爪议事厅运行时配置

> 📌 版本：v3.1.33 | 更新：2026-07-22 | 维护者：石叔
>
> 修改此文件即可自定义路径和偏好，无需改动 SKILL.md。
> 路径支持绝对路径和相对于 workspace 根目录的相对路径。

## 路径

| 键 | 默认值 | 说明 |
|---|---|---|
| `workspace_root` | ~/.qclaw/workspace | OpenClaw workspace 根目录（~ 自动展开为当前用户家目录，跨机可移植，勿硬编码绝对路径）|
| `user_md` | `{workspace_root}\USER.md` | 用户偏好存储文件 |
| `octopus_dir` | `{workspace_root}\memory\octopus` | 八爪议事厅数据根目录 |
| `growth_dir` | `{octopus_dir}\growth` | 角色成长数据目录（JSON 结构化数据） |
| `archive_dir` | `{octopus_dir}\archive` | 讨论归档目录（.md 文件） |
| `archive_file` | `{archive_dir}\YYYYMMDD-{topic}.md` | 单次归档文件名模板。`{topic}` 由石叔诊断的"核心矛盾"字段自动提取，截断长度由 `topic_slug_length` 控制 |

## 角色来源

> 角色如何产生与是否入本地库。修改后立即生效。

| 键 | 默认值 | 说明 |
|---|---|---|
| `role_source_mode` | `generate` | 角色来源模式（语义见下）：`generate`(每次纯动态生成，用完即丢弃，不查本地库/不注入成长/不累积 growth) / `local_priority`(优先复用本地有成长史角色，不足再动态补，补的角色按 `pure_generated_handling` 提示是否存库) / `local_only`(只从本地库挑，绝不现场造) |
| `role_extract_merge` | `true` | 合并提取源（true=growth_record.json 成长角色优先 + role-templates.md 模板库兜底；false=仅模板库） |
| `pure_generated_handling` | `ask` | 纯生成角色(本地库查无此名)处置：`ask`(标记 suggest_localize 并输出 PROMPT 提示石叔询问用户是否转正存库) / `no`(保持一次性，不存库，不提示) |

## 角色成长

> 立场履历与成长数据的保留/备份参数。修改后立即生效。

| 键 | 默认值 | 说明 |
|---|---|---|
| `stance_history_max_entries` | `10` | 立场履历最大保留条数（超出后删旧留新） |
| `stance_history_skip_sessions` | `(空)` | 选择性遗忘：逗号分隔的 `session_id`（格式 `YYYYMMDD-话题`），spawn 注入时跳过 |
| `backup_keep_count` | `30` | 成长数据自动备份保留份数（超出后删旧留新）。默认 30 份 ≈ 30 天 |
| `deep_mode_inject_count` | `3` | deep 模式注入条数（上限 5，设为 0 退化为 light 模式） |

## 关系网络

> 角色间关系线采集与展示。修改后立即生效。

| 键 | 默认值 | 说明 |
|---|---|---|
| `relationship_network_mode` | `auto` | 关系网三模式：`auto`（先攒再看）/ `always`（永久展示）/ `never`（关就是关） |
| `relationship_network_enabled` | `false` | 关系网三模式在 `auto` / `always` 模式下，设为 `true` 后激活关系网络展示和注入，默认 `false` |

### 🔘 关系网络开关

**三模式**：`auto`（默认，有数据时引导解锁）/ `always`（永久展示）/ `never`（关就是关，不采集）

**临时开关**：说"这轮不要关系"单场关闭，讨论结束自动恢复

**判断链路**：`never` 优先 > 临时开关 > `always` 直通 > `auto` 检查 `relationship_network_enabled`

> ⚠️ 与 `role_source_mode` 的关系：关系网数据**仅来自角色历史**（累积进 growth_record.json 的 relationship_lines）。`role_source_mode=generate`（默认）下角色纯动态生成、用完丢弃、不写 growth_record，**因此永远不会累积关系网数据**——即便 `relationship_network_enabled=true` 也因无数据而空置；`auto` 模式的"引导解锁"提示也因检测不到任何角色有关系数据而不会弹出。要让关系网真正生效，须改用 `local_priority` 或 `local_only`（角色有持久历史），或将 generate 角色手动转正入本地库。

## 🧩 调度预设

> 单开关控制调度模式，无需复杂配置。调度档位与讨论模式、快速模式完全正交可叠加（见下方档位适配）。

| 键 | 默认值 | 可选值 | 说明 |
|---|---|---|---|
| `schedule_mode` | `balanced` | `auto` / `balanced` / `stable` | 3 档位调度开关——**只控制是否/如何使用子 agent**；"更快"由正交「快速模式」负责，各档 spawn 行为与适用场景见下方「档位适配场景参考」 |
| `schedule_auto_switch_threshold` | `0.7` | `0`–`1` | `auto` 模式下升级到 `stable` 的复杂度阈值（议题复杂度 ≥ 该值时升级） |

> 实现状态：✅ 已实装。调度分支逻辑见 SKILL.md「🧩 调度档位执行分支」节（`stable` 逐角色 spawn / `balanced` 石叔 inline 复合 Prompt·结果优先·轮次由收敛驱动 / `auto` 按复杂度选档）。

### 档位适配场景参考

> 选型轴 = **spawn 行为**（是否/如何使用子 agent）；「派生时延」列是 spawn 行为的自然结果，非独立优化目标（设计估计，随议题长度、轮次、角色数浮动）。调度档位与「快速模式」正交可叠加（执行层 vs 呈现层）。

| 档位 | spawn 行为 | 派生时延 | 适用场景 |
|---|---|---|---|
| auto | 按复杂度在 balanced / stable 间自动选 | 动态 | 不想手动选档时；硬权衡+价值冲突组合自动升 stable |
| ⚖️ balanced（默认）| 不 spawn，石叔主上下文 inline 复合 Prompt | 最低（无会话创建/回传重排） | 绝大多数日常讨论（90% 场景）、中等复杂度、需快出结论 |
| 🛡️ stable | 逐角色 spawn 真子 agent，完全隔离 | 最高（有会话创建/回传重排） | 复杂长议题 / 深度分析 / 重要决策；长拉锯用真隔离防串味 |

> 注：`fast` 不单列档——它与 `balanced` 同样不 spawn（仅 spawn 细节不同），“更快”由正交「快速模式」（呈现层）承担。

## 输出与校验

> 归档命名与引用事实校验。修改后立即生效。

| 键 | 默认值 | 说明 |
|---|---|---|
| `topic_slug_length` | `6` | 归档文件名 `{topic}` 截断字数，如 `20260609-开咖啡馆.md` |
| `cite_verify` | `true` | 引用源数据校验开关（默认开）：开启后 spawn prompt 注入「引用须真实可核验，禁编造法条/案例/数据」；石叔遇强事实主张可派 researcher 实时核验；小结标「未核验」风险；关闭退回宽松 |

> 实现状态：✅ 已实装。开关见 `cite_verify`；机制见 SKILL.md 硬性规则 #10 + references/templates.md「🔍 引用校验指令」节 + references/summary-format.md「未核验风险标注」节。

---

## 📖 用法

SKILL.md 和子文件中遇到路径时，按以下规则解析：

1. 先查 `config.md` 对应键的值，替换为对应的值
2. 如果键值是绝对路径，直接使用；如果是相对路径，相对于 `workspace_root` 解析

---

## 💡 示例

**场景 1：换台机器**

只改 `workspace_root` 一行，其余路径自动跟随：

```text
workspace_root = ~/.qclaw/workspace
→ octopus_dir = /home/user/.qclaw/workspace/memory/octopus
→ growth_dir  = /home/user/.qclaw/workspace/memory/octopus/growth
```

**场景 2：关闭关系网络**（不采集、不展示、不留痕迹）

```text
relationship_network_mode = never
→ 关系线采集永久关闭，已有数据保留但不使用
```
