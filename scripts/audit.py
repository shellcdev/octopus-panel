#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit.py — 八爪议事厅文档/一致性审计总入口（合并 audit_all/audit_docs/
role_verify_alias/audit_orphans 四脚本）

子命令:
  docs      文档一致性审计（角色数/版本头/CHANGELOG/脚本完整性/SKILL引用）
  alias     QUESTION_TYPE_MAP 映射完整性校验（需 role_generate.py 同目录）
  orphans   孤儿文件与悬空引用扫描
  all       依次跑 docs + alias，汇总 PASS/WARN（默认；--strict 任一处告警即非零退出）

用法:
  python audit.py                # = --all
  python audit.py --all [--strict]
  python audit.py docs
  python audit.py alias
  python audit.py orphans [<root>]
"""
import os
import re
import sys
import io

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)

# 提前缓存 role_generate（其模块级代码会 rewrap sys.stdout.buffer）。
# 必须在任何 StringIO 重定向之前导入，否则 cmd_alias 捕获输出时会崩。
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
try:
    import role_generate  # noqa: F401  (缓存用，cmd_alias 复用其常量)
except Exception:
    role_generate = None


# ============================================================ cmd: docs
def cmd_docs():
    REFS_DIR = os.path.join(SKILL_ROOT, 'references')
    SCRIPTS_DIR = os.path.join(SKILL_ROOT, 'scripts')

    # 1. role-templates.md 实际角色数
    FP = os.path.join(REFS_DIR, 'role-templates.md')
    with open(FP, encoding='utf-8') as f:
        content = f.read()

    headers = re.findall(r'^### (.+)$', content, re.MULTILINE)
    real_roles = [h for h in headers if '模板' not in h and '占位' not in h and '[角色名]' not in h]
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

    # 5. role_generate.py 的 QUESTION_TYPE_MAP 角色数
    FP3 = os.path.join(SCRIPTS_DIR, 'role_generate.py')
    if os.path.exists(FP3):
        with open(FP3, encoding='utf-8') as f:
            pycode = f.read()
        map_roles = re.findall(r'"([^"]+)"', pycode.split('QUESTION_TYPE_MAP')[1].split('}')[0])
        print(f'\n=== role_generate.py QUESTION_TYPE_MAP ===')
        print(f'映射角色数: {len(map_roles)}')
        missing = [r for r in map_roles if r not in content]
        print(f'role-templates.md 中缺失: {missing if missing else "无"}')
        extra = [r for r in real_roles if not any(m in r for m in map_roles)]
        print(f'映射中未覆盖的模板角色(本地库角色,可忽略): {extra if extra else "无"}')
    else:
        print(f'\n=== role_generate.py === 不存在，跳过')

    # 6. scripts/ 目录完整性
    print(f'\n=== scripts/ 目录完整性 ===')
    expected_scripts = ['discussion_archive.py', 'role_generate.py', 'tag_filter.py',
                        'role_validate.py']
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


# ============================================================ cmd: alias
def cmd_alias():
    # role_generate 已在模块顶层导入并缓存，这里直接复用（避免重定向期间触发模块级 stdout rewrap）
    from role_generate import QUESTION_TYPE_MAP

    FP_TMPL = os.path.join(SKILL_ROOT, 'references', 'role-templates.md')
    with open(FP_TMPL, encoding='utf-8') as f:
        tmpl = f.read()

    names = [n for vals in QUESTION_TYPE_MAP.values() for n in vals]

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


# ============================================================ cmd: orphans
def cmd_orphans(argv):
    import pathlib

    ENTRY_FILES = {"README.md", "SKILL.md", "CHANGELOG.md", "config.md", "TODO.md"}
    TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\-]+\.(?:md|py)")
    LINK_RE = re.compile(r"\]\(([^)]+\.(?:md|py))\)")
    IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
    IMPORTLIB_RE = re.compile(r"(?:importlib\.import_module|__import__)\(\s*['\"]([\w.]+)['\"]\s*\)")
    PLACEHOLDER_RE = re.compile(r"xxx|XXX|示例|example|占位|占位符", re.I)
    INTERNAL_PREFIXES = ("references/", "scripts/")
    HISTORICAL_SOURCES = {"CHANGELOG.md"}

    def norm(p):
        return p.replace("\\", "/").strip()

    def resolve(token, root, tree_names):
        t = norm(token)
        if "://" in t or t.startswith("//"):
            return None
        if "/" in t or "\\" in t:
            cand = (root / t).resolve()
            return cand if cand.exists() else None
        matches = tree_names.get(token, [])
        return matches[0] if len(matches) == 1 else None

    def _is_dangling_candidate(tok, root, tree_names):
        if PLACEHOLDER_RE.search(tok):
            return False
        if "://" in tok or tok.startswith("//"):
            return False
        if not ("/" in tok or "\\" in tok):
            return False
        if not tok.startswith(INTERNAL_PREFIXES):
            return False
        return resolve(tok, root, tree_names) is None

    def extract_refs(text, is_py, root, tree_names):
        found = set()
        for m in LINK_RE.finditer(text):
            r = resolve(m.group(1), root, tree_names)
            if r:
                found.add(r)
        for m in TOKEN_RE.finditer(text):
            r = resolve(m.group(0), root, tree_names)
            if r:
                found.add(r)
        if is_py:
            for m in IMPORT_RE.finditer(text):
                mod = m.group(1) or m.group(2)
                if not mod:
                    continue
                mod = mod.split(".")[-1]
                fname = mod + ".py"
                for c in tree_names.get(fname, []):
                    found.add(c)
            for m in IMPORTLIB_RE.finditer(text):
                mod = m.group(1).split(".")[-1] + ".py"
                for c in tree_names.get(mod, []):
                    found.add(c)
        return found

    root = pathlib.Path(argv[0]).resolve() if argv else pathlib.Path(SCRIPT_DIR).parent
    print(f"扫描根: {root}\n")

    md_files = sorted(root.rglob("*.md"))
    py_files = sorted(root.rglob("*.py"))
    all_files = md_files + py_files

    tree_names = {}
    for f in all_files:
        tree_names.setdefault(f.name, []).append(f.resolve())

    inbound = {f.resolve(): set() for f in all_files}
    dangling = []

    for src in all_files:
        is_py = src.suffix == ".py"
        text = src.read_text(encoding="utf-8", errors="ignore")
        refs = extract_refs(text, is_py, root, tree_names)
        for tgt in refs:
            if tgt != src.resolve():
                inbound[tgt].add(src.resolve())
        if src.name in HISTORICAL_SOURCES:
            continue
        for m in LINK_RE.finditer(text):
            tok = norm(m.group(1))
            if _is_dangling_candidate(tok, root, tree_names):
                dangling.append((src, tok))
        for m in TOKEN_RE.finditer(text):
            tok = norm(m.group(0))
            if _is_dangling_candidate(tok, root, tree_names):
                dangling.append((src, tok))

    print("=" * 64)
    print("① 悬空引用 (dangling)：引用了但文件不存在 —— 通常是缺陷")
    print("=" * 64)
    if dangling:
        for src, tok in sorted(set(dangling), key=lambda x: str(x[0])):
            print(f"  {src.relative_to(root)}  ->  {tok}")
    else:
        print("  ✅ 无悬空引用")

    print()
    print("=" * 64)
    print("② 孤儿文件 (orphan)：存在但 0 入链（入口文件除外）")
    print("=" * 64)
    orphans = []
    for f in all_files:
        fr = f.resolve()
        if f.name in ENTRY_FILES:
            continue
        if len(inbound[fr]) == 0:
            orphans.append(f)
    if orphans:
        for f in orphans:
            kind = "py" if f.suffix == ".py" else "md"
            note = "（脚本：可能由 cron/CLI 外部调用，需人工确认）" if kind == "py" else ""
            print(f"  [{kind}] {f.relative_to(root)}  {note}")
    else:
        print("  ✅ 无孤儿文件")

    print()
    print("=" * 64)
    print("③ 入口文件入链数（供核对，不计孤儿）")
    print("=" * 64)
    for f in all_files:
        if f.name in ENTRY_FILES:
            print(f"  {f.relative_to(root)}: 入链 {len(inbound[f.resolve()])}")

    print()
    print("=" * 64)
    print(f"汇总：{len(all_files)} 个文件 | 悬空引用 {len(set(dangling))} | 孤儿 {len(orphans)}")
    print("=" * 64)


# ============================================================ cmd: all
def cmd_all(strict=False):
    print('=' * 60)
    print('八爪议事厅 · 文档一致性一键审计')
    print('=' * 60)

    # 1) docs
    print('\n--- [1/2] 文档一致性审计 (audit.py docs) ---')
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        cmd_docs()
    finally:
        sys.stdout = old
    out1 = buf.getvalue()
    print(out1)
    warn_audit = []
    for line in out1.splitlines():
        if ('不一致' in line) or ('❌' in line) or ('是否全部一致' in line and 'False' in line):
            warn_audit.append(line.strip())
        elif ('缺失' in line) and ('缺失: 无' not in line) and ('缺失：无' not in line):
            warn_audit.append(line.strip())

    # 2) alias
    print('\n--- [2/2] 别名映射校验 (audit.py alias) ---')
    buf2 = io.StringIO()
    sys.stdout = buf2
    rc_alias = 0
    try:
        try:
            cmd_alias()
        except SystemExit as e:
            rc_alias = e.code or 0
    finally:
        sys.stdout = old
    out2 = buf2.getvalue()
    print(out2)
    warn_alias = []
    for line in out2.splitlines():
        if '匹配失败' in line or '失败' in line:
            warn_alias.append(line.strip())

    # 汇总
    print('\n' + '=' * 60)
    print('审计结论')
    print('=' * 60)
    all_warn = warn_audit + warn_alias
    if not all_warn:
        print('PASS ✅ 文档一致性 / 别名映射全部通过，无失修。')
        return 0
    print('WARN ⚠️ 发现 {} 处需关注：'.format(len(all_warn)))
    for w in all_warn:
        print('  - ' + w)
    if strict:
        return 1
    return 0


# ============================================================ main
def main():
    argv = sys.argv[1:]
    sub = None
    strict = '--strict' in argv
    if strict:
        argv = [a for a in argv if a != '--strict']

    if not argv or argv[0] in ('--all', 'all'):
        sub = 'all'
    elif argv[0] in ('docs', 'alias', 'orphans'):
        sub = argv[0]
    else:
        print('未知子命令: ' + argv[0])
        print('用法: python audit.py [docs|alias|orphans|all] [--strict]')
        return 2

    if sub == 'docs':
        cmd_docs()
        return 0
    if sub == 'alias':
        try:
            cmd_alias()
        except SystemExit as e:
            return e.code or 0
        return 0
    if sub == 'orphans':
        cmd_orphans(argv[1:])
        return 0
    if sub == 'all':
        return cmd_all(strict=strict)
    return 0


if __name__ == '__main__':
    sys.exit(main())
