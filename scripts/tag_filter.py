#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色标签筛选器 v5（英文变量名，缩进安全）
用法：python tag_filter.py [条件1] [条件2] ...
"""

import re
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, '..', 'references', 'role-templates.md')

GROUP_KEYWORDS = {
    '人生决策': '人生组',
    '商业决策': '商业组',
    '家庭': '家庭组',
    '技术架构': '技术架构组',
    '职场管理': '职场管理组',
    '教育规划': '教育规划组',
    '医疗决策': '医疗决策组',
    '法律风控': '法律风控组',
}


def parse_roles(filepath):
    with open(filepath, encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    roles = []
    current_group = '未分组'
    i = 0

    while i < len(lines):
        line = lines[i]

        # 章节行
        if line.startswith('## '):
            section = line[3:].strip()
            for kw, gname in GROUP_KEYWORDS.items():
                if kw in section:
                    current_group = gname
                    break
            i += 1
            continue

        # 角色行
        if line.startswith('### '):
            header = line[4:].strip()
            role = {
                'header': header,
                'group': current_group,
                'tags': {},
                'tag_line': '',
            }

            # 往后看 5 行找标签行
            for j in range(i + 1, min(i + 6, len(lines))):
                candidate = lines[j]
                if '立场：' in candidate and '|' in candidate:
                    tag_line = re.sub(r'^>\s*', '', candidate).strip()
                    role['tag_line'] = tag_line
                    parts = [p.strip() for p in tag_line.split('|')]
                    for part in parts:
                        if '：' in part:
                            k, v = part.split('：', 1)
                            role['tags'][k.strip()] = v.strip()
                    break

            roles.append(role)
            i += 1
            continue

        i += 1

    return roles


def match_role(role, conditions):
    text = (role['header'] + ' ' + role['group']).lower()
    for v in role['tags'].values():
        text += ' ' + v.lower()

    for cond in conditions:
        if cond.lower() not in text:
            return False
    return True


def main():
    if len(sys.argv) < 2:
        roles = parse_roles(TEMPLATE_FILE)
        print(f'共 {len(roles)} 个角色：\n')
        for r in roles:
            tl = r.get('tag_line', '(无标签)')
            print(f'  [{r["group"]}] {r["header"]}')
            print(f'    {tl}')
        return

    conditions = sys.argv[1:]
    roles = parse_roles(TEMPLATE_FILE)
    matched = [r for r in roles if match_role(r, conditions)]

    if not matched:
        print(f'未找到匹配角色（条件：{" + ".join(conditions)}）')
        return

    print(f'匹配到 {len(matched)} 个角色（条件：{" + ".join(conditions)}）：\n')
    for r in matched:
        tl = r.get('tag_line', '(无标签)')
        print(f'  [{r["group"]}] {r["header"]}')
        print(f'    {tl}')
        print()


if __name__ == '__main__':
    main()
