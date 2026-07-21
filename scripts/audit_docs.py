# -*- coding: utf-8 -*-
# 文档一致性审计

import re, os, sys, io

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- 路径解析：从脚本位置推导 skill_root ---
def get_skill_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

SKILL_ROOT = get_skill_root()
REFS_DIR = os.path.join(SKILL_ROOT, 'references')
SCRIPTS_DIR = os.path.join(SKILL_ROOT, 'scripts')

# 1. role-templates.md 实际角色数
FP = os.path.join(REFS_DIR, 'role-templates.md')
with open(FP, encoding='utf-8') as f:
    content = f.read()

headers = re.findall(r'^### (.+)$', content, re.MULTILINE)
real_roles = [h for h in headers if '模板' not in h and '占位' not in h]
print('=== role-templates.md ===')
print(f'### 标题行: {len(headers)} 个')
print(f'实际角色: {len(real_roles)} 个')
print(f'列表: {real_roles}')

# 2. README 标注的角色数
FP2 = os.path.join(SKILL_ROOT, 'README.md')
if os.path.exists(FP2):
    with open(FP2, encoding='utf-8') as f:
        readme = f.read()
    nums = re.findall(r'(\d{1,2})\s*个角色', readme)
    print(f'\n=== README.md ===')
    print(f'角色数标注: {nums}')
    print(f'是否一致: {nums[0] == str(len(real_roles)) if nums else "无标注"}')
else:
    print(f'\n=== README.md === 不存在，跳过')

# 3. 所有文件头的版本号
files = [os.path.join(SKILL_ROOT, 'config.md')]
for _nm in sorted(os.listdir(REFS_DIR)):
    if _nm.endswith('.md'):
        files.append(os.path.join(REFS_DIR, _nm))
files += [os.path.join(SKILL_ROOT, 'README.md'),
          os.path.join(SKILL_ROOT, 'SKILL.md'),
          os.path.join(SKILL_ROOT, 'TODO.md')]
print('\n=== 文件头版本号 ===')
versions = {}
for fp in files:
    basename = os.path.basename(fp)
    if not os.path.exists(fp):
        versions[basename] = '（文件不存在）'
        print(f'  {basename}: 文件不存在')
        continue
    with open(fp, encoding='utf-8') as f:
        head = ''.join(f.readline() for _ in range(5))
    m = re.search(r'v[\d.]+', head)
    ver = m.group() if m else '（无版本号）'
    versions[basename] = ver
    print(f'  {basename}: {ver}')

existing_versions = {k: v for k, v in versions.items() if v not in ('（无版本号）', '（文件不存在）')}
if existing_versions:
    all_same = len(set(existing_versions.values())) == 1
    print(f'是否全部一致: {all_same}')

# 4. CHANGELOG 最新版本
cl_fp = os.path.join(SKILL_ROOT, 'CHANGELOG.md')
if os.path.exists(cl_fp):
    with open(cl_fp, encoding='utf-8') as f:
        cl = f.read()
    vers = re.findall(r'^## v(\d+(?:\.\d+)*)', cl, re.MULTILINE)
    if vers:
        cl_ver = 'v' + max(vers, key=lambda x: tuple(int(p) for p in x.split('.')))
    else:
        cl_ver = '无'
    print(f'\n=== CHANGELOG 最新版本 ===')
    print(f'  {cl_ver}')
    if existing_versions:
        first_ver = list(existing_versions.values())[0]
        print(f'  与文件头版本一致: {cl_ver == first_ver}')

# 5. generate_roles.py 的 QUESTION_TYPE_MAP 角色数
FP3 = os.path.join(SCRIPTS_DIR, 'generate_roles.py')
if os.path.exists(FP3):
    with open(FP3, encoding='utf-8') as f:
        pycode = f.read()
    map_roles = re.findall(r'"([^"]+)"', pycode.split('QUESTION_TYPE_MAP')[1].split('}')[0])
    print(f'\n=== generate_roles.py QUESTION_TYPE_MAP ===')
    print(f'映射角色数: {len(map_roles)}')
    missing = [r for r in map_roles if r not in content]
    print(f'role-templates.md 中缺失: {missing if missing else "无"}')
    extra = [r for r in real_roles if not any(m in r for m in map_roles)]
    print(f'映射中未覆盖的模板角色(本地库角色,可忽略): {extra if extra else "无"}')
else:
    print(f'\n=== generate_roles.py === 不存在，跳过')

# 6. scripts/ 目录完整性
print(f'\n=== scripts/ 目录完整性 ===')
expected_scripts = ['archive_discussion.py', 'generate_roles.py', 'tag_filter.py',
                    'validate_role.py']
for s in expected_scripts:
    exists = os.path.exists(os.path.join(SCRIPTS_DIR, s))
    print(f'  {s}: {"✅" if exists else "❌ 缺失"}')

# 7. SKILL.md 引用的文件是否存在
print(f'\n=== SKILL.md 引用文件检查 ===')
ref_files = [
    os.path.join(REFS_DIR, 'jargon.md'),
    os.path.join(REFS_DIR, 'rules-discussion.md'),
    os.path.join(REFS_DIR, 'summary-format.md'),
    os.path.join(REFS_DIR, 'roles-rules.md'),
    os.path.join(REFS_DIR, 'rules-collab.md'),
    os.path.join(REFS_DIR, 'templates.md'),
    os.path.join(REFS_DIR, 'role-templates.md'),
    os.path.join(REFS_DIR, 'discussion-examples.md'),
]
for fp in ref_files:
    basename = os.path.basename(fp)
    exists = os.path.exists(fp)
    print(f'  {basename}: {"✅" if exists else "❌ 缺失"}')
