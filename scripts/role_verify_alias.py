#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校验 role_generate.py 的 QUESTION_TYPE_MAP 中每个角色名是否都能在
# role-templates.md 模板库中找到定义（检测悬空映射 / 拼写漂移）。
# 替代原 ROLE_ALIAS 死数据校验（ROLE_ALIAS 已下沉移除）。

import os
import re
import sys
import io
import ast

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP_TMPL = os.path.join(SKILL_ROOT, 'references', 'role-templates.md')
FP_GEN = os.path.join(SKILL_ROOT, 'scripts', 'role_generate.py')

with open(FP_TMPL, encoding='utf-8') as f:
    tmpl = f.read()
with open(FP_GEN, encoding='utf-8') as f:
    pycode = f.read()

# 提取 QUESTION_TYPE_MAP 字典
m = re.search(r'QUESTION_TYPE_MAP\s*=\s*(\{.*?\})', pycode, re.S)
if not m:
    print('❌ 未在 role_generate.py 找到 QUESTION_TYPE_MAP')
    sys.exit(1)
map_dict = ast.literal_eval(m.group(1))
names = [n for vals in map_dict.values() for n in vals]

# 模板库角色名集合：括号前全名 + 核心名
full = re.findall(r'^###\s+\S+\s+([^\n（(]+)', tmpl, re.M)
core = [s.split('（')[0].split('(')[0].strip()
        for s in re.findall(r'^###\s+\S+\s+(\S+)', tmpl, re.M)]
tmpl_roles = set(full) | set(core)

missing = [n for n in names if n not in tmpl_roles]
print(f'QUESTION_TYPE_MAP 引用角色名: {len(names)}')
print(f'role-templates.md 角色名集合: {len(tmpl_roles)}')
if missing:
    print('❌ 模板库缺失以下映射角色:')
    for n in missing:
        print(f'  {n}')
    sys.exit(1)
else:
    print('✅ 所有映射角色均在模板库中找到定义')
