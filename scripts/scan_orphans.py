#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_orphans.py — 扫描 octopus-panel skill 的孤儿文件与悬空引用。

两类问题：
  1) 悬空引用 (dangling)：某文件引用了另一个路径，但该路径在 skill 树中不存在。
  2) 孤儿文件 (orphan)：文件真实存在，但**没有任何其他文件引用它**（0 入链）。
     入口文件（README/SKILL/CHANGELOG/config/TODO）与脚本运行时入口除外，
     但它们仍以「入口」身份列在报告里供核对。

识别规则：
  - .md 内：markdown 链接 `(path)`、反引号/裸 token 形如 `xxx.md` / `references/xxx.md`。
  - .py 内：import/from-import/importlib/__import__ 的模块名（映射成 .py 文件）+ 路径 token。
  - 解析：含分隔符的视为相对根的路径；裸 basename 在树内唯一匹配则命中。
  - 忽略 http(s):// 等外链、以及 `本文件` 语境（不携带 .md token，天然不产生入链）。

用法：
  python scripts/scan_orphans.py            # 默认扫描脚本所在 skill 根
  python scripts/scan_orphans.py <root>     # 指定根目录
"""
import pathlib
import re
import sys

# 视为“入口/必定存在、不计入孤儿”的文件（相对根）
ENTRY_FILES = {
    "README.md",
    "SKILL.md",
    "CHANGELOG.md",
    "config.md",
    "TODO.md",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\-]+\.(?:md|py)")
LINK_RE = re.compile(r"\]\(([^)]+\.(?:md|py))\)")
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M
)
IMPORTLIB_RE = re.compile(r"(?:importlib\.import_module|__import__)\(\s*['\"]([\w.]+)['\"]\s*\)")

# 占位符 / 示例 token（非真实引用）
PLACEHOLDER_RE = re.compile(r"xxx|XXX|示例|example|占位|占位符", re.I)
# 仅这些前缀的内部指针才算“真·悬空”候选（避免误报外部/历史引用）
INTERNAL_PREFIXES = ("references/", "scripts/")
# 历史变更日志允许引用已删除文件，不作为悬空源
HISTORICAL_SOURCES = {"CHANGELOG.md"}


def norm(p: str) -> str:
    return p.replace("\\", "/").strip()


def resolve(token: str, root: pathlib.Path, tree_names: dict):
    """返回解析到的真实文件路径，或 None。"""
    t = norm(token)
    if "://" in t or t.startswith("//"):
        return None
    if "/" in t or "\\" in t:
        cand = (root / t).resolve()
        return cand if cand.exists() else None
    # 裸 basename：在树内查找唯一同名文件
    matches = tree_names.get(token, [])
    return matches[0] if len(matches) == 1 else None


def _is_dangling_candidate(tok: str, root: pathlib.Path, tree_names: dict) -> bool:
    """判断 tok 是否应作为“悬空引用”上报：内部指针 + 解析失败 + 非占位符。"""
    if PLACEHOLDER_RE.search(tok):
        return False
    if "://" in tok or tok.startswith("//"):
        return False
    if not ("/" in tok or "\\" in tok):
        return False  # 裸 basename 解析失败属歧义（可能是外部/模块），不算
    if not tok.startswith(INTERNAL_PREFIXES):
        return False  # 指向 skill 外部（如 workspace/USER.md），预期外链
    return resolve(tok, root, tree_names) is None


def extract_refs(text: str, is_py: bool, root: pathlib.Path, tree_names: dict):
    """从一段文本里抽出被引用的真实文件路径集合。"""
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
            mod = mod.split(".")[-1]  # 取最后一段
            fname = mod + ".py"
            for c in tree_names.get(fname, []):
                found.add(c)
        for m in IMPORTLIB_RE.finditer(text):
            mod = m.group(1).split(".")[-1] + ".py"
            for c in tree_names.get(mod, []):
                found.add(c)
    return found


def main():
    root = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
    print(f"扫描根: {root}\n")

    md_files = sorted(root.rglob("*.md"))
    py_files = sorted(root.rglob("*.py"))
    all_files = md_files + py_files

    # 文件名 -> 文件路径列表（用于裸 basename 解析）
    tree_names = {}
    for f in all_files:
        tree_names.setdefault(f.name, []).append(f.resolve())

    inbound = {f.resolve(): set() for f in all_files}
    dangling = []  # (source, token)

    for src in all_files:
        is_py = src.suffix == ".py"
        text = src.read_text(encoding="utf-8", errors="ignore")
        # 提取本文件“指向的”引用
        refs = extract_refs(text, is_py, root, tree_names)
        for tgt in refs:
            if tgt != src.resolve():
                inbound[tgt].add(src.resolve())
        # 收集悬空：仅当“内部指针”且解析失败
        if src.name in HISTORICAL_SOURCES:
            continue  # 历史日志允许引用已删除文件
        for m in LINK_RE.finditer(text):
            tok = norm(m.group(1))
            if _is_dangling_candidate(tok, root, tree_names):
                dangling.append((src, tok))
        for m in TOKEN_RE.finditer(text):
            tok = norm(m.group(0))
            if _is_dangling_candidate(tok, root, tree_names):
                dangling.append((src, tok))

    # ---- 输出 ----
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


if __name__ == "__main__":
    main()
