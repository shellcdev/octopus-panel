#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 验证 ROLE_ALIAS 是否能正确匹配 role-templates.md 里的角色

import os
import ast
import sys
import io

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- 路径解析：从 config.md 读取 skill_root ---
def get_skill_root():
    """从 config.md 读取 workspace_root，推导 skill_root"""
    # 脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # skill_root = scripts 的上级目录
    return os.path.dirname(script_dir)

SKILL_ROOT = get_skill_root()

# 读取 role-templates.md
FP = os.path.join(SKILL_ROOT, 'references', 'role-templates.md')
with open(FP, encoding='utf-8') as f:
    content = f.read()

# 读取 generate_roles.py 里的 ROLE_ALIAS
FP2 = os.path.join(SKILL_ROOT, 'scripts', 'generate_roles.py')
with open(FP2, encoding='utf-8') as f:
    pycode = f.read()

# 提取 ROLE_ALIAS 字典
start = pycode.find('ROLE_ALIAS = {')
start += len('ROLE_ALIAS = ')
brace_count = 0
end = start
for i in range(start, len(pycode)):
    if pycode[i] == '{':
        brace_count += 1
    elif pycode[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end = i + 1
            break
alias_dict = ast.literal_eval(pycode[start:end].strip())

print(f'ROLE_ALIAS 映射数: {len(alias_dict)}')

# 检查每个别名是否能匹配到 role-templates.md 里的标题
matched = 0
missing = []
for alias, full_title in alias_dict.items():
    if full_title in content:
        matched += 1
    else:
        title_no_emoji = full_title.split(' ', 1)[1] if ' ' in full_title else full_title
        if title_no_emoji in content:
            matched += 1
        else:
            missing.append((alias, full_title))

print(f'匹配成功: {matched}/{len(alias_dict)}')
if missing:
    print(f'匹配失败:')
    for alias, title in missing:
        print(f'  {alias} -> {title}')
else:
    print('✅ 所有别名都能正确匹配')
