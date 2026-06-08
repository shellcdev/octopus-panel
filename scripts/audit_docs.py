# -*- coding: utf-8 -*-
# 文档一致性审计

import re, os

# 1. role-templates.md 实际角色数
FP = r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\role-templates.md'
with open(FP, encoding='utf-8') as f:
    content = f.read()

headers = re.findall(r'^### (.+)$', content, re.MULTILINE)
real_roles = [h for h in headers if '模板' not in h and '占位' not in h]
print('=== role-templates.md ===')
print(f'### 标题行: {len(headers)} 个')
print(f'实际角色: {len(real_roles)} 个')
print(f'列表: {real_roles}')

# 2. README 标注的角色数
FP2 = r'C:\Users\Shell\.qclaw\skills\octopus-panel\README.md'
with open(FP2, encoding='utf-8') as f:
    readme = f.read()
nums = re.findall(r'(\d{1,2})\s*个角色', readme)
print(f'\n=== README.md ===')
print(f'角色数标注: {nums}')
print(f'是否一致: {nums[0] == str(len(real_roles)) if nums else "无标注"}')

# 3. 所有文件头的版本号
files = [
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\CHANGELOG.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\README.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\SKILL.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\role-templates.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\templates.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\jargon.md',
    r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\discussion-examples.md',
]
print('\n=== 文件头版本号 ===')
versions = {}
for fp in files:
    with open(fp, encoding='utf-8') as f:
        head = ''.join(f.readline() for _ in range(5))
    m = re.search(r'v[\d.]+', head)
    ver = m.group() if m else '（无版本号）'
    versions[os.path.basename(fp)] = ver
    print(f'  {os.path.basename(fp)}: {ver}')

# 检查是否一致
all_same = len(set(versions.values())) == 1
print(f'是否全部一致: {all_same}')

# 4. CHANGELOG 最新版本
with open(r'C:\Users\Shell\.qclaw\skills\octopus-panel\CHANGELOG.md', encoding='utf-8') as f:
    cl = f.read()
m = re.search(r'^## (v[\d.]+)', cl, re.MULTILINE)
cl_ver = m.group(1) if m else '无'
print(f'\n=== CHANGELOG 最新版本 ===')
print(f'  {cl_ver}')
print(f'  与文件头版本一致: {cl_ver == list(versions.values())[0] if versions else False}')

# 5. generate_roles.py 的 QUESTION_TYPE_MAP 角色数
FP3 = r'C:\Users\Shell\.qclaw\skills\octopus-panel\scripts\generate_roles.py'
with open(FP3, encoding='utf-8') as f:
    pycode = f.read()
# 找 QUESTION_TYPE_MAP 里所有角色名
map_roles = re.findall(r'\"([^\"]+)\"', pycode.split('QUESTION_TYPE_MAP')[1].split('}')[0])
print(f'\n=== generate_roles.py QUESTION_TYPE_MAP ===')
print(f'映射角色数: {len(map_roles)}')
# 检查是否都在 role-templates.md 里
missing = [r for r in map_roles if r not in content]
print(f'role-templates.md 中缺失: {missing if missing else "无"}')
extra = [r for r in real_roles if r not in map_roles]
print(f'映射中缺失的角色: {extra if extra else "无"}')
