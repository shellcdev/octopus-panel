# -*- coding: utf-8 -*-
# 验证 ROLE_ALIAS 是否能正确匹配 role-templates.md 里的角色

import re

# 读取 role-templates.md
FP = r'C:\Users\Shell\.qclaw\skills\octopus-panel\references\role-templates.md'
with open(FP, encoding='utf-8') as f:
    content = f.read()

# 读取 generate_roles.py 里的 ROLE_ALIAS
FP2 = r'C:\Users\Shell\.qclaw\skills\octopus-panel\scripts\generate_roles.py'
with open(FP2, encoding='utf-8') as f:
    pycode = f.read()

# 提取 ROLE_ALIAS 字典
import ast
# 找到 ROLE_ALIAS 定义块（只要字典部分）
start = pycode.find('ROLE_ALIAS = {')
# 跳过 'ROLE_ALIAS = '
start += len('ROLE_ALIAS = ')
# 找到匹配的 closing brace
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
    # 检查完整标题是否在文件中
    if full_title in content:
        matched += 1
    else:
        # 尝试模糊匹配（去掉 emoji）
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
