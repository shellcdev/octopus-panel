#!/usr/bin/env python3
"""Split SKILL.md into core + references sub-files."""
import os

SKILL_PATH = r'C:\Users\Shell\.qclaw\skills\octopus-panel\SKILL.md'
REFS_DIR = r'C:\Users\Shell\.qclaw\skills\octopus-panel\references'

with open(SKILL_PATH, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

def header_line(title_fragment):
    """Find the FIRST ## header matching a fragment, skipping code blocks."""
    in_code = False
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            in_code = not in_code
        if not in_code and line.startswith('## ') and title_fragment in line:
            return i
    raise ValueError(f"Header not found: {title_fragment}")

# All section boundaries (0-based), in document order
H = {}
H['点名'] = header_line('## @点名机制')            # 215
H['角色插入'] = header_line('## 角色灵活插入')      # 271
H['讨论板'] = header_line('## 讨论板 · 升级版')     # 313
H['小结'] = header_line('## 阶段性小结')            # 497
H['收敛'] = header_line('## 长讨论议题收敛')        # 573
H['角色选择'] = header_line('## 角色选择指南')      # 598
H['总结格式'] = header_line('## 石叔总结格式')      # 611
H['动态终止'] = header_line('## 动态终止机制')      # 665
H['量化判定'] = header_line('## 量化判定标准')      # 676
H['异常场景'] = header_line('## 异常场景处置')      # 788
H['增加角色'] = header_line('## 增加角色规则')      # 920
H['交互指令'] = header_line('## 交互指令·语义兼容') # 969
H['多人协作'] = header_line('## 多人实时协作')      # 1023
H['反馈通道'] = header_line('## 💬 反馈通道')      # 1134
H['L1L2L3'] = header_line('## L1/L2/L3')           # 1143
H['归档'] = header_line('## 讨论归档机制')          # 1195
H['模板库'] = header_line('## 角色模板库管理')      # 1257
H['标签筛选'] = header_line('## 角色标签筛选器')   # 1310

def extract(start, end=None):
    if end is None:
        end = len(lines)
    return '\n'.join(lines[start:end])

# === Sub-file contents ===

# 1. references/rules-discussion.md
# 点名 + 角色插入 + 讨论板 + 小结 + 收敛 + 异常场景
rules_discussion = """# 讨论规则 · 详细规范

> 📌 本文件由 SKILL.md 拆分而来，包含讨论过程中的所有规则。
> 石叔在讨论过程中按需引用。

""" + extract(H['点名'], H['角色选择'])

# 2. references/summary-format.md
# 角色选择之后：总结格式 + 动态终止 + 量化判定
summary_fmt = """# 总结与判定规则

> 📌 本文件由 SKILL.md 拆分而来，包含总结格式、动态终止和量化判定标准。
> 石叔在总结阶段和判定违规时按需引用。

""" + extract(H['总结格式'], H['异常场景'])

# 3. references/roles-rules.md
# 角色选择 + 增加角色 + 模板库 + 标签筛选器
rules_roles = """# 角色管理规则

> 📌 本文件由 SKILL.md 拆分而来，包含角色选择、增加角色、模板库管理和标签筛选。

""" + extract(H['角色选择'], H['总结格式']) + "\n\n" + extract(H['增加角色'], H['交互指令']) + "\n\n" + extract(H['模板库'], len(lines))

# 4. references/rules-collab.md
# 多人协作 + L1/L2/L3 + 归档
rules_collab = """# 协作、恢复与归档

> 📌 本文件由 SKILL.md 拆分而来，包含多人协作模式、错误恢复机制和讨论归档。

""" + extract(H['多人协作'], H['反馈通道']) + "\n\n" + extract(H['L1L2L3'], H['模板库'])

# === New SKILL.md core ===
# frontmatter (0 to 点名) + 参考索引 + 交互指令(含讨论偏好) + 反馈通道

ref_index = """## 详细规则索引

以下规则已拆分到独立文件，石叔在讨论过程中按需引用：

| 文件 | 内容 | 触发时机 |
|---|---|---|
| `references/rules-discussion.md` | 点名机制、角色插入、讨论板格式、阶段性小结、收敛机制、异常场景 | 讨论进行中 |
| `references/summary-format.md` | 石叔总结格式、动态终止、量化判定标准 | 总结阶段 / 判定违规时 |
| `references/roles-rules.md` | 角色选择、增加角色、模板库管理、标签筛选器 | 生成/替换角色时 |
| `references/rules-collab.md` | 多人协作、真人插话、L1/L2/L3恢复、归档机制 | 协作场景 / 错误恢复时 |

"""

new_core = (extract(0, H['点名']) + "\n" + ref_index + 
            extract(H['交互指令'], H['多人协作']) + "\n" +
            extract(H['反馈通道'], H['L1L2L3']) + "\n")

# Write files
os.makedirs(REFS_DIR, exist_ok=True)

files_to_write = {
    os.path.join(REFS_DIR, 'summary-format.md'): summary_fmt,
    os.path.join(REFS_DIR, 'rules-discussion.md'): rules_discussion,
    os.path.join(REFS_DIR, 'roles-rules.md'): rules_roles,
    os.path.join(REFS_DIR, 'rules-collab.md'): rules_collab,
    SKILL_PATH: new_core,
}

for path, content in files_to_write.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.rstrip('\n') + '\n')
    line_count = content.strip().count('\n') + 1
    print(f"  {os.path.basename(path):30s} {line_count:4d} lines")

# Verify no content lost
original_total = len(lines)
new_total = sum(content.strip().count('\n') + 1 for content in files_to_write.values())
print(f"\nOriginal: {original_total} lines | New total: {new_total} lines | Delta: {new_total - original_total}")
print("Done!")
