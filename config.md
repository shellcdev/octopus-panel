# config.md · 八爪议事厅运行时配置

> 📌 版本：v3.1.18 | 更新：2026-07-22 | 维护者：石叔
>
> 修改此文件即可自定义路径和偏好，无需改动 SKILL.md。
> 路径支持绝对路径和相对于 workspace 根目录的相对路径。

## 路径

| 键 | 默认值 | 说明 |
|---|---|---|
| workspace_root | C:\Users\Shell\.qclaw\workspace | OpenClaw workspace 根目录 |
| user_md | {workspace_root}\USER.md | 用户偏好存储文件 |
| octopus_dir | {workspace_root}\memory\octopus | 八爪议事厅数据根目录 |
| growth_dir | {octopus_dir}\growth | 角色成长数据目录（JSON 结构化数据） |
| archive_dir | {octopus_dir}\archive | 讨论归档目录（.md 文件） |
| archive_file | {archive_dir}\YYYYMMDD-{topic}.md | 单次归档文件名模板。{topic} 由石叔诊断的"核心矛盾"字段自动提取，截断长度由 topic_slug_length 控制 |

## 成长系统偏好

> 角色成长系统的运行时参数。修改后立即生效，无需重启。

| 键 | 默认值 | 说明 |
|---|---|---|
| relationship_network_mode | auto | 关系网三模式：`auto`（先攒再看）/ `always`（永久展示）/ `never`（关就是关）|
| relationship_network_enabled | false | 关系网三模式在 auto / always 模式下，设为 `true` 后激活关系网络展示和注入，默认 `false `|
| stance_history_max_entries | 10 | 立场履历最大保留条数（超出后删旧留新） |
| stance_history_skip_sessions | (空) | 选择性遗忘：逗号分隔的 session_id（格式 `YYYYMMDD-话题`），spawn 注入时跳过 |
| backup_keep_count | 30 | 成长数据自动备份保留份数（超出后删旧留新）。默认 30 份 ≈ 30 天 |
| deep_mode_inject_count | 3 | deep 模式注入条数（上限 5，设为 0 退化为 light 模式）|
| topic_slug_length | 6 | 归档文件名 {topic} 截断字数，如 `20260609-开咖啡馆.md` |

### 🔘 关系网络开关

**三模式**：`auto`（默认，有数据时引导解锁）/ `always`（永久展示）/ `never`（关就是关，不采集）

**临时开关**：说"这轮不要关系"单场关闭，讨论结束自动恢复

**判断链路**：`never` 优先 > 临时开关 > `always` 直通 > `auto` 检查 enabled

## 🧩 调度预设
> 单开关控制调度模式，无需复杂配置。调度档位与讨论模式、快速模式完全正交可叠加（见下方档位适配）。

| 键 | 默认值 | 可选值 | 说明 |
|---|---|---|---|
| schedule_mode | balanced | auto / balanced / stable | 3档位调度模式——**只控制是否使用子 agent 及如何使用**（fast 已并入 balanced，两者皆不 spawn，仅 spawn 行为不同；“更快”由正交「快速模式」负责）：<br>• `auto`：石叔按议题复杂度自动选档（< `schedule_auto_switch_threshold` → balanced，≥ → stable）<br>• `balanced`（推荐·默认档）：石叔主上下文 inline 复合 Prompt 一次性模拟全部角色（**不 spawn 子 agent**，spawn 行为即定义），保真度接近真子 Agent，默认 1 轮直出结论，日常 90% 场景首选<br>• `stable`：真子 Agent 全量执行（逐角色 spawn，完全隔离），稳定性最高，适合复杂长议题/重要决策 |
| schedule_auto_switch_threshold | 0.7 | 0-1 | auto 模式下自动切换到 stable 档位的复杂度阈值（议题复杂度 ≥ 该值时升级）；default 0.7 |

> 实现状态：✅ 已实装。调度分支逻辑见 SKILL.md「🧩 调度档位执行分支」节（stable 逐角色 spawn / balanced 石叔 inline 复合 Prompt·结果优先·默认1轮 / auto 按复杂度选档）。

### 档位适配场景参考
> 注：本表以 **spawn 行为**为轴（是否/如何使用子 agent）；相对时延为**派生效果**（不 spawn 则无会话创建/回传重排延迟），设计估计，实际随议题长度、轮次、角色数浮动。调度档位与「快速模式」分属执行层/呈现层，可叠加。

| 档位 | spawn 行为（派生时延） | 适用场景 |
|---|---|---|
| auto | 动态 | 所有场景，自动适配 |
| balanced | 不 spawn（无会话创建/回传重排延迟，派生时延最低） | 日常决策、普通讨论、中等复杂度议题（90%场景首选，默认1轮直出结论） |
| stable | 逐角色 spawn（有会话创建/回传重排延迟，派生时延最高） | 复杂长议题、深度分析、重要决策场景（长拉锯用真隔离更稳） |

> 注：`fast` 不单列档——快结果即 `balanced`，极速呈现由正交「快速模式」承担。

## 输出与校验

> 归档命名与引用事实校验。修改后立即生效。

| 键 | 默认值 | 说明 |
|---|---|---|
| cite_verify | true | 引用源数据校验开关（默认开）：开启后 spawn prompt 注入「引用须真实可核验，禁编造法条/案例/数据」；石叔遇强事实主张可派 researcher 实时核验；小结标「未核验」风险；关闭退回宽松 |

> 实现状态：✅ 已实装。开关见 `cite_verify`；机制见 SKILL.md 硬性规则 #10 + references/templates.md「🔍 引用校验指令」节 + references/summary-format.md「未核验风险标注」节。

---

## 用法

SKILL.md 和子文件中遇到路径时，按以下规则解析：

1. 先查 config.md 对应键的值，替换为对应的值
2. 如果键值是绝对路径，直接使用；如果是相对路径，相对于 workspace_root 解析

---

## 示例

**场景 1：换台机器**
只改 `workspace_root` 一行，其余路径自动跟随：

```
workspace_root = /home/user/.claw/workspace
→ octopus_dir = /home/user/.claw/workspace/memory/octopus
→ growth_dir  = /home/user/.claw/workspace/memory/octopus/growth
```

**场景 2：关闭关系网络**（不采集、不展示、不留痕迹）

```
relationship_network_mode = never
→ 关系线采集永久关闭，已有数据保留但不使用
```
