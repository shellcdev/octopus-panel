#!/usr/bin/env python3
"""
audit_links.py — 八爪议事厅 skill 链接审计总入口

合并原三脚本:
  - deadlink_scan.py    全仓死链(裸文件引用 + markdown链接 + 章节锚点)
  - ref_interlink.py    references/ 文件间互链拓扑
  - skill_link_report.py SKILL.md 对外/内部链接健康

用法:
  python scripts/audit_links.py            # 全部检查
  python scripts/audit_links.py --dead     # 仅死链
  python scripts/audit_links.py --inter    # 仅 references 互链
  python scripts/audit_links.py --skill    # 仅 SKILL.md 链接

返回码: 发现"真死链"(非合规历史) 则 exit 1, 否则 0。
合规历史死链(如 CHANGELOG 中标注未纳入版本管理的 split_skill.py)不计为失败。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "SKILL.md")
REF_DIR = os.path.join(ROOT, "references")

BARE_EXT = r"(?:md|py|json|yaml|yml|txt)"
PAT_FILE = re.compile(r'`?([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|py|json|yaml|yml|txt))`?')
PAT_MDLINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
LOCAL_DIRS = ("references/", "specs/", "scripts/", "assets/", "examples/", "templates/")

# 合规历史死链白名单(路径 -> 出现文件)
WHITELIST = {
    "scripts/split_skill.py": {"CHANGELOG.md"},
    "scripts/growth_render.py": {"CHANGELOG.md"},
    "scripts/growth_migrate.py": {"CHANGELOG.md"},
    "scripts/growth_backup.py": {"CHANGELOG.md"},
    "scripts/audit_all.py": {"CHANGELOG.md"},
    "scripts/audit_docs.py": {"CHANGELOG.md"},
    "scripts/audit_orphans.py": {"CHANGELOG.md"},
    "scripts/role_verify_alias.py": {"CHANGELOG.md"},
}


def slugify(heading):
    """GitHub-style anchor slug (keeps CJK, preserves leading hyphen from symbols)."""
    s = heading.lower()
    s = re.sub(r"[`*_~]", "", s)
    s = re.sub(r"[^\w\u4e00-\u9fff \-]", "", s)
    s = s.replace(" ", "-")
    return s


def collect_anchors(path):
    anchors = set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"^#{1,6}\s+(.*)", line)
                if m:
                    anchors.add(slugify(m.group(1)))
    except FileNotFoundError:
        pass
    return anchors


def is_whitelisted(ref, rel):
    return ref in WHITELIST and rel in WHITELIST[ref]


# ---------------------------------------------------------------- dead links
def audit_dead():
    print("=" * 60)
    print(" [1] 全仓死链扫描 (裸文件引用 + Markdown链接 + 章节锚点)")
    print("=" * 60)

    md_files = []
    for dp, _, fs in os.walk(ROOT):
        if ".git" in dp:
            continue
        for fn in fs:
            if fn.endswith(".md"):
                md_files.append(os.path.join(dp, fn))

    anchor_cache = {}
    dead_file, dead_link, dead_anchor = [], [], []
    seen = {}

    for fpath in md_files:
        rel = os.path.relpath(fpath, ROOT).replace("\\", "/")
        with open(fpath, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            for m in PAT_FILE.finditer(line):
                ref = m.group(1)
                if not ref.startswith(LOCAL_DIRS):
                    continue
                seen[ref] = seen.get(ref, 0) + 1
                if not os.path.exists(os.path.join(ROOT, ref)):
                    # CHANGELOG.md 内 scripts/references 引用多为历史变更流水，整体豁免
                    if rel == "CHANGELOG.md" and (ref.startswith("scripts/") or ref.startswith("references/")):
                        print(f"  (whitelist) {rel}:{i} -> {ref}")
                    elif not is_whitelisted(ref, rel):
                        dead_file.append((rel, i, ref))
                    else:
                        print(f"  (whitelist) {rel}:{i} -> {ref}")

            for m in PAT_MDLINK.finditer(line):
                tgt = m.group(1).strip()
                if tgt.startswith(("http://", "https://", "mailto:")):
                    continue
                if tgt.startswith("#"):
                    path_part, anchor = "", tgt[1:]
                elif "#" in tgt:
                    path_part, anchor = tgt.split("#", 1)
                else:
                    path_part, anchor = tgt, ""

                if path_part == "":
                    target_file = fpath
                else:
                    target_file = os.path.normpath(
                        os.path.join(os.path.dirname(fpath), path_part)
                    )
                    if not os.path.exists(target_file):
                        if not is_whitelisted(path_part, rel):
                            dead_link.append((rel, i, tgt))
                        continue

                if anchor and target_file.endswith(".md"):
                    if target_file not in anchor_cache:
                        anchor_cache[target_file] = collect_anchors(target_file)
                    if slugify(anchor) not in anchor_cache[target_file]:
                        dead_anchor.append((rel, i, tgt))

    for rel, i, ref in dead_file:
        print(f"  XX L{rel}:{i}  ->  {ref}")
    for rel, i, tgt in dead_link:
        print(f"  XX L{rel}:{i}  ->  {tgt}")
    for rel, i, tgt in dead_anchor:
        print(f"  XX L{rel}:{i}  ->  {tgt}")

    total = len(dead_file) + len(dead_link) + len(dead_anchor)
    print(f"\n  真死链: {total} (files:{len(dead_file)} links:{len(dead_link)} anchors:{len(dead_anchor)})")
    print(f"  已登记引用: {len(seen)} unique")
    return total


# ------------------------------------------------------------ inter-links
def audit_inter():
    print("\n" + "=" * 60)
    print(" [2] references/ 内部互链拓扑")
    print("=" * 60)

    refs = sorted(f for f in os.listdir(REF_DIR) if f.endswith(".md"))
    refs_set = set(refs)

    graph = {r: set() for r in refs}
    incoming = {r: [] for r in refs}

    for f in refs:
        fpath = os.path.join(REF_DIR, f)
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in PAT_FILE.finditer(text):
            t = m.group(1)
            base = t.split("/")[-1] if "/" in t else t
            if base in refs_set and base != f:
                graph[f].add(base)
        for m in PAT_MDLINK.finditer(text):
            t = m.group(1)
            base = t.split("/")[-1]
            if base in refs_set and base != f:
                graph[f].add(base)

    total = 0
    for f in refs:
        if graph[f]:
            total += len(graph[f])
            print(f"  {f}  ->  {len(graph[f])} 个: {', '.join(sorted(graph[f]))}")
        else:
            print(f"  {f}  ->  (无内链)")

    print(f"\n  内链总数: {total}")
    print("\n  入链数:")
    for r in sorted(refs, key=lambda x: len(incoming[x])):
        # recompute incoming properly
        pass
    inc = {r: [] for r in refs}
    for f in refs:
        for t in graph[f]:
            inc[t].append(f)
    for r in sorted(refs, key=lambda x: len(inc[x])):
        n = len(inc[r])
        tag = "[孤岛]" if n == 0 else ("[弱]" if n == 1 else "[ok]")
        extra = "" if n == 0 else f"  <- {', '.join(inc[r])}"
        print(f"    {tag} {r}: 被 {n} 引用{extra}")
    return 0


# ------------------------------------------------------------ skill links
def audit_skill():
    print("\n" + "=" * 60)
    print(" [3] SKILL.md 链接健康 (对外 + 内部锚点)")
    print("=" * 60)

    with open(SKILL, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    anchors = {}
    for i, line in enumerate(lines, 1):
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            anchors[slugify(m.group(1))] = i

    bare_hits, md_hits = [], []
    for i, line in enumerate(lines, 1):
        for m in PAT_FILE.finditer(line):
            t = m.group(1)
            if t.startswith(("references/", "specs/")):
                ok = os.path.exists(os.path.join(ROOT, t))
                bare_hits.append((i, t, ok))
        for m in PAT_MDLINK.finditer(line):
            tgt = m.group(1).strip()
            if tgt.startswith(("http", "mailto")):
                continue
            pp = tgt.split("#")[0]
            if pp.startswith(("references/", "specs/")):
                ok = os.path.exists(os.path.normpath(os.path.join(ROOT, pp)))
                md_hits.append((i, tgt, ok))

    for i, t, ok in bare_hits + md_hits:
        print(f"  {'OK ' if ok else 'XX '}L{i:<4} {t}")
    ext_dead = sum(1 for _, _, o in bare_hits + md_hits if not o)
    print(f"\n  对外链接 {len(bare_hits)+len(md_hits)} 条, 死链 {ext_dead}")

    # internal anchors
    n_jump, n_dead = 0, 0
    for i, line in enumerate(lines, 1):
        for m in PAT_MDLINK.finditer(line):
            tgt = m.group(1).strip()
            if tgt.startswith("#"):
                anchor = tgt[1:]
                n_jump += 1
                if slugify(anchor) not in anchors:
                    n_dead += 1
                    print(f"  XX  L{i:<4} #{anchor}")
    print(f"  内部锚点跳转 {n_jump} 条, 死链 {n_dead}")
    return ext_dead + n_dead


def main():
    args = sys.argv[1:]
    run_all = not any(a in ("--dead", "--inter", "--skill") for a in args)
    rc = 0

    if run_all or "--dead" in args:
        rc |= 1 if audit_dead() > 0 else 0
    if run_all or "--inter" in args:
        audit_inter()
    if run_all or "--skill" in args:
        rc |= 1 if audit_skill() > 0 else 0

    print("\n" + "=" * 60)
    if rc:
        print(" 结果: 发现真死链 (exit 1)")
    else:
        print(" 结果: 全绿, 无真死链 (exit 0)")
    print("=" * 60)
    sys.exit(rc)


if __name__ == "__main__":
    main()
