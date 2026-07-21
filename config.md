# config.md · 八爪议事厅运行时配置

> 📌 版本：v3.0 | 更新：2026-06-11 | 维护者：石叔
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
