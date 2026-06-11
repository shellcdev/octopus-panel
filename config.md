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
| archive_file | {archive_dir}\YYYYMMDD-{topic}.md | 单次归档文件名模板。{topic} 由石叔诊断的"核心矛盾"字段自动提取，≤6字 |

## 讨论行为偏好

> 修改即可改变讨论默认行为。用户通过「个性化配置指令」设置的值写入 `user_md`，会覆盖这里。

| 键 | 默认值 | 说明 |
|---|---|---|
| default_max_words | 直觉型≤60 / 平衡型≤80 / 分析型≤100 | 发言字数上限（按角色类型） |
| default_mode | 串行 | 默认讨论模式（串行 / 分组 / 圆桌 / 结对） |
| default_rounds | 2 | 默认讨论轮次 |
| default_roles | 4 | 默认角色数量 |
| consensus_5grid | 启用 | 共识进度条5格模式；设为"禁用"则为10格 |

## 成长系统偏好

> 角色成长系统的运行时参数。修改后立即生效，无需重启。

| 键 | 默认值 | 说明 |
|---|---|---|
| relationship_network_mode | auto | 关系网三模式：`auto`（先攒再看）/ `always`（永久展示）/ `never`（关就是关）。|
| relationship_network_enabled | false | 在 auto 模式下，设为 true 后激活关系网络展示和注入 |
| stance_history_max_entries | 10 | 立场履历最大保留条数（超出后删旧留新） |
| stance_history_skip_sessions | (空) | 选择性遗忘：逗号分隔的 session_id，spawn 注入时跳过 |
| backup_keep_count | 30 | 成长数据自动备份保留份数（超出后删旧留新） |
| deep_mode_inject_count | 3 | deep 模式注入历史立场条数 |
| archive_keyword_count | 5 | 归档关键词提取数量，每个 ≤6 字 |

### 🔘 关系网络开关详解

#### 全局三模式

| 模式 | 展示 | 采集 | 一句话 |
|------|------|------|--------|
| `auto`（默认） | ❌ 条件触发引导 | ✅ 全量采集 | "先攒着，以后再看" |
| `always` | ✅ 永久展示 | ✅ 全量采集 | "我就要这个" |
| `never` | ❌ 不展示 | ❌ 不采集 | **"关就是关"** |

配置位置：`relationship_network_enabled`（触发开关）/ `relationship_network_mode`（行为模式）

#### 条件触发引导（auto 模式）

当系统内任意角色有 ≥1 条已建立的关系线时，渲染引导提示：

> 💡 有些角色之间开始建立关系了。说"开启关系网络"解锁。🔗

**原则**：有数据才提示，不提前画饼。

#### 临时开关（单场临时覆盖）

| 用户说 | 效果 | 生命周期 |
|--------|------|---------|
| "这轮不要关系" | 当前讨论临时关闭，spawn inject 不注入 | 讨论结束自动清空 |
| "这轮恢复关系" | 当前讨论提前恢复 | — |

**判断链路**：
1. 全局 mode=="never" → ❌ 关死了，临时开关无效
2. 有临时开关（set_session_override）→ 按临时值
3. mode=="always" → ✅ 直通，跳过 enabled 检查
4. mode=="auto" → 检查 `relationship_network_enabled`

#### 开关影响对照

| 组件 | auto | always | never |
|------|------|--------|-------|
| relationship_lines 采集 | ✅ 全量 | ✅ 全量 | ❌ 不采集 |
| 角色卡展示 | ❌→开启后→✅ | ✅ | ❌ |
| spawn inject | ❌→开启后→✅ | ✅ | ❌ |
| 完整档关系网络图 | ❌→开启后→✅ | ✅ | ❌ |

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
