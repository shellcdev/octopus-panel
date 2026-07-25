#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八爪议事厅脚本测试统一 runner。

用法（在 skill 根目录或任意目录）：

    python scripts/tests/run_tests.py                  # 跑全部，详细输出
    python scripts/tests/run_tests.py -q              # 安静模式（仅点点点 + 汇总）
    python scripts/tests/run_tests.py test_growth_api # 只跑某模块

也兼容标准 unittest 入口（在 skill 根目录，scripts 需在 path 上）：

    python -m unittest discover -s scripts/tests -p "test_*.py" -v
    python -m unittest tests.test_growth_api -v
"""
import io
import os
import sys
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))              # scripts/tests
SKILL_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))    # skill 根目录
SCRIPTS_DIR = os.path.normpath(os.path.join(HERE, '..'))         # scripts（被测模块所在）
# 确保 tests/ 自身与同级 scripts 在 path 上（兼容直接 python 调用，
# 不依赖 tests/__init__.py 的注入）
for _p in (HERE, SCRIPTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _module_from_path(path):
    rel = os.path.relpath(path, HERE).replace(os.sep, '/')
    return 'tests.' + rel[:-3].replace('/', '.')


def _count_suite(suite):
    """统计 suite 里的用例数。"""
    return suite.countTestCases()


def _per_module_stats(suite):
    """按顶层 TestCase 类所属模块聚合，返回 {module_name: count}。"""
    stats = {}
    for test in _iter_cases(suite):
        # test.id() 形如 "tests.test_xxx.ClassName.method" 或 "test_xxx.Class..."
        parts = test.id().split('.')
        # 找到 test_xxx 段
        mod = 'unknown'
        for p in parts:
            if p.startswith('test_'):
                mod = p
                break
        stats[mod] = stats.get(mod, 0) + 1
    return stats


def _iter_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for t in _iter_cases(item):
                yield t
        else:
            yield item


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    verbosity = 2
    explicit = [a for a in argv if not a.startswith('-')]
    if '-q' in argv or '--quiet' in argv:
        verbosity = 0

    loader = unittest.TestLoader()

    if explicit:
        # 显式指定模块名（如 tests.test_growth_api）
        suite = unittest.TestSuite()
        for name in explicit:
            if not name.startswith('tests.'):
                name = 'tests.' + name if not name.startswith('test_') else 'tests.' + name
            suite.addTests(loader.loadTestsFromName(name))
    else:
        # discover 全部
        suite = loader.discover(HERE, pattern='test_*.py', top_level_dir=SCRIPTS_DIR)

    total = _count_suite(suite)

    print('=' * 64)
    print('八爪议事厅脚本测试 · 共 %d 个用例' % total)
    print('=' * 64)

    stats = _per_module_stats(suite)
    if stats:
        print('模块分布：')
        for mod in sorted(stats):
            print('  %-28s %3d 用例' % (mod, stats[mod]))
        print('-' * 64)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    print()
    print('=' * 64)
    if result.wasSuccessful():
        print('结果：✅ 全部通过（%d 用例）' % total)
    else:
        print('结果：❌ 失败 %d，错误 %d（共 %d 用例）' % (
            len(result.failures), len(result.errors), total))
        if result.failures:
            print('  失败用例：')
            for t, _ in result.failures:
                print('    - ' + t.id())
        if result.errors:
            print('  错误用例：')
            for t, _ in result.errors:
                print('    - ' + t.id())
    print('=' * 64)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # 重包 stdout 为 UTF-8，避免 Windows GBK 终端打印 CJK 报错
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.exit(main())
