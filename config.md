# config.md · 八爪议事厅运行时配置

> 修改此文件即可自定义路径，无需改动 SKILL.md。
> 路径支持绝对路径和相对于 workspace 根目录的相对路径。

## 路径

| 键 | 默认值 | 说明 |
|---|---|---|
| workspace_root | C:\Users\Shell\.qclaw\workspace | OpenClaw workspace 根目录 |
| user_md | {workspace_root}\USER.md | 用户偏好存储文件 |
| archive_dir | {workspace_root}\memory\octopus-archive | 讨论归档目录 |
| archive_file | {archive_dir}\YYYYMMDD-HHMM.md | 单次归档文件名模板 |

## 用法

SKILL.md 和子文件中遇到路径时，按以下规则解析：

1. 先查 config.md 对应键的值
2. {workspace_root} 替换为 workspace_root 键的值
3. {archive_dir} 替换为 archive_dir 键的值（已展开 workspace_root）
4. 如果键值是绝对路径，直接使用；如果是相对路径，相对于 workspace_root 解析

## 示例

换台机器？只改 workspace_root 一行：

    workspace_root = /home/user/.qclaw/workspace

其余路径会自动跟随。