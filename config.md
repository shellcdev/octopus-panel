# config.md · 八爪议事厅运行时配置

> 修改此文件即可自定义路径和偏好，无需改动 SKILL.md。
> 路径支持绝对路径和相对于 workspace 根目录的相对路径。

## 路径

| 键 | 默认值 | 说明 |
|---|---|---|
| workspace_root | C:\Users\Shell\.qclaw\workspace | OpenClaw workspace 根目录 |
| user_md | {workspace_root}\USER.md | 用户偏好存储文件 |
| octopus_dir | {workspace_root}\memory\octopus | 八爪议事厅数据根目录 |
| growth_dir | {octopus_dir}\growth | 角色成长数据目录（JSON 结构化数据）|
| archive_dir | {octopus_dir}\archive | 讨论归档目录（.md 文件） |
| archive_file | {archive_dir}\YYYYMMDD-{topic}.md | 单次归档文件名模板。{topic} 由石叔诊断的"核心矛盾"字段自动提取，≤6字 |

---

## 偏好（v2.18 新增）

> 修改偏好键即可改变系统默认值，无需改动 SKILL.md。
> 用户通过「个性化配置指令」设置的值写入 `user_md`，会覆盖这些默认值。

| 键 | 默认值 | 说明 |
|---|---|---|
| default_max_words | 直觉型≤60 / 平衡型≤80 / 分析型≤100 | 发言字数上限（按角色类型） |
| default_mode | 串行 | 默认讨论模式 |
| default_rounds | 2 | 默认讨论轮次 |
| default_roles | 4 | 默认角色数量 |
| consensus_5grid | 启用 | 共识进度条5格模式；设为"禁用"则为10格 |
| relationship_network_enabled | false | 关系网络总开关；设为 true 后才采集角色间关系数据 |
| relationship_network_mode | auto | 关系采集模式：`auto`（自动）/ `always`（每场采集）/ `never`（关闭） |
| stance_history_max_entries | 10 | 立场履历最大保留条数（超出后删旧留新） |
| stance_history_skip_sessions | (空) | 选择性遗忘：逗号分隔的 session_id，spawn 注入时跳过 |
| backup_keep_count | 30 | 成长数据自动备份保留份数（超出后删旧留新） |
| deep_mode_inject_count | 3 | deep 模式注入历史立场条数 |
| archive_keyword_count | 5 | 归档关键词提取数量（≤6字每个） |

---

## 用法

SKILL.md 和子文件中遇到路径时，按以下规则解析：

1. 先查 config.md 对应键的值
2. {workspace_root} 替换为 workspace_root 键的值
3. {archive_dir} 替换为 archive_dir 键的值（已展开 workspace_root）
4. 如果键值是绝对路径，直接使用；如果是相对路径，相对于 workspace_root 解析

---

## 示例

换台机器？只改 workspace_root 一行：

    workspace_root = /home/user/.claw/workspace

其余路径会自动跟随。
