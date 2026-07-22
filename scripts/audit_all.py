# -*- coding: utf-8 -*-
"""
audit_all.py - 一键文档一致性审计（audit_docs + verify_alias）
用法：
    python audit_all.py            # 跑审计 + 别名校验
    python audit_all.py --strict   # 任一告警即非零退出（适合 CI / pre-commit）

输出：汇总两脚本结果，末尾给 PASS / WARN 结论。
依赖：scripts/audit_docs.py, scripts/verify_alias.py（同目录）
"""
import os
import sys
import io
import subprocess

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)


def _run(script_name):
    """运行同目录脚本，返回 (rc, stdout)。"""
    path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(path):
        return None, '[缺失] {}'.format(script_name)
    try:
        r = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
        )
        return r.returncode, r.stdout
    except Exception as e:
        return -1, '[异常] {}: {}'.format(script_name, e)


def main():
    strict = '--strict' in sys.argv[1:]

    print('=' * 60)
    print('八爪议事厅 · 文档一致性一键审计')
    print('=' * 60)

    # 1) audit_docs.py
    print('\n--- [1/2] 文档一致性审计 (audit_docs.py) ---')
    rc1, out1 = _run('audit_docs.py')
    if out1:
        print(out1)
    # 提取关键不一致信号
    warn_audit = []
    if out1:
        for line in out1.splitlines():
            # 仅捕获「真正不一致/缺失」信号，忽略 "缺失: 无" 这类否定表述
            if ('不一致' in line) or ('❌' in line) or ('是否全部一致' in line and 'False' in line):
                warn_audit.append(line.strip())
            elif ('缺失' in line) and ('缺失: 无' not in line) and ('缺失：无' not in line):
                warn_audit.append(line.strip())

    # 2) verify_alias.py
    print('\n--- [2/2] 别名映射校验 (verify_alias.py) ---')
    rc2, out2 = _run('verify_alias.py')
    if out2:
        print(out2)
    warn_alias = []
    if out2:
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


if __name__ == '__main__':
    sys.exit(main())
