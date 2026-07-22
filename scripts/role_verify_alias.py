#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校验 role_generate.py 的 QUESTION_TYPE_MAP 中每个角色名是否都能在
# role-templates.md 模板库中找到定义（检测悬空映射 / 拼写漂移）。
# 替代原 ROLE_ALIAS 死数据校验（ROLE_ALIAS 已下沉移除）。

import os
import re
import sys
import io

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 确保同目录模块可 import（复用 role_generate 的常量，避免正则扒源码的脆弱性）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from role_generate import QUESTION_TYPE_MAP

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP_TMPL = os.path.join(SKILL_ROOT, 'references', 'role-templates.md')

with open(FP_TMPL, encoding='utf-8') as f:
    tmpl = f.read()

# 映射角色名直接复用 role_generate.QUESTION_TYPE_MAP（模块级常量，单一真相源）
# 一旦该 dict 含嵌套括号也能正确读取，不再依赖非贪婪正则截半
names = [n for vals in QUESTION_TYPE_MAP.values() for n in vals]

# 模板库角色名集合：括号前全名 + 核心名
# 跳过格式示例占位行（如 '### [emoji] [角色名]（...）'）
full = [n for n in re.findall(r'^###\s+\S+\s+([^\n（(]+)', tmpl, re.M)
        if n and '[' not in n and '角色名' not in n]
core = [s.split('（')[0].split('(')[0].strip()
        for s in re.findall(r'^###\s+\S+\s+(\S+)', tmpl, re.M) if '[' not in s]
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
