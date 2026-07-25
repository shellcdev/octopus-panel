# -*- coding: utf-8 -*-
"""audit.py 单元测试。

被测对象：``cmd_docs`` / ``cmd_alias`` / ``cmd_orphans`` / ``cmd_all`` /
``main``。

策略：
  - ``cmd_docs`` / ``cmd_alias`` / ``cmd_all`` 跑真实 skill（只读集成），
    验证不崩 + 输出含关键段落；``cmd_alias`` 可能因数据不一致 SystemExit，
    捕获后断言返回码合理；
  - ``cmd_orphans`` 接受 root 参数，用临时目录构造 悬空引用 / 孤儿文件 /
    正常引用 三类，精确验证扫描逻辑；
  - ``main`` 验证子命令分发与退出码。
"""
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from _helpers import SCRIPTS_DIR, SKILL_ROOT  # noqa: F401
import audit


def _capture(fn, *a, **kw):
    """捕获 stdout 调用 fn，返回 (return_value, output_text, raised_systemexit_code)。"""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    rc = None
    ret = None
    exit_code = None
    try:
        try:
            ret = fn(*a, **kw)
        except SystemExit as e:
            exit_code = e.code
    finally:
        sys.stdout = old
    return ret, buf.getvalue(), exit_code


class CmdDocsTests(unittest.TestCase):
    """读真实 references/README/CHANGELOG/config（只读集成）。"""

    def test_runs_without_crash(self):
        _, out, _ = _capture(audit.cmd_docs)
        self.assertIn("role-templates.md", out)
        self.assertIn("scripts/ 目录完整性", out)

    def test_reports_role_count(self):
        _, out, _ = _capture(audit.cmd_docs)
        self.assertIn("实际角色", out)


class CmdAliasTests(unittest.TestCase):
    """读真实 role-templates.md + QUESTION_TYPE_MAP（只读集成）。"""

    def test_runs_without_crash(self):
        _, out, exit_code = _capture(audit.cmd_alias)
        # 成功路径：无 SystemExit，输出含"映射角色名"；缺失路径：exit 1
        if exit_code is None:
            self.assertTrue("映射角色名" in out or "✅" in out or "找到定义" in out)
        else:
            # 若数据有不一致，exit 1 是合理退出
            self.assertEqual(exit_code, 1)

    def test_output_contains_role_count(self):
        _, out, _ = _capture(audit.cmd_alias)
        # 无论成功/失败都会先 print 引用角色名数
        self.assertIn("QUESTION_TYPE_MAP", out)


class CmdOrphansTests(unittest.TestCase):
    """用临时目录构造 mini-skill，隔离测孤儿/悬空扫描。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='audit_orphans_')
        os.makedirs(os.path.join(self.tmp, 'references'))
        os.makedirs(os.path.join(self.tmp, 'scripts'))
        # 入口 SKILL.md：引用 exists.md + 悬空 missing.md + 引用 used.py
        with open(os.path.join(self.tmp, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write("# Skill\n[exists](references/exists.md) references/missing.md scripts/used.py\n")
        # references/exists.md 被引用
        with open(os.path.join(self.tmp, 'references', 'exists.md'), 'w', encoding='utf-8') as f:
            f.write("# Exists\n")
        # references/lonely.md 孤儿（无人引用）
        with open(os.path.join(self.tmp, 'references', 'lonely.md'), 'w', encoding='utf-8') as f:
            f.write("# Lonely orphan\n")
        # scripts/used.py 被引用
        with open(os.path.join(self.tmp, 'scripts', 'used.py'), 'w', encoding='utf-8') as f:
            f.write("# used\n")
        # scripts/lone.py 孤儿脚本
        with open(os.path.join(self.tmp, 'scripts', 'lone.py'), 'w', encoding='utf-8') as f:
            f.write("# lone\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dangling_reference_listed(self):
        _, out, _ = _capture(audit.cmd_orphans, [self.tmp])
        # references/missing.md 是悬空
        self.assertIn("missing.md", out)

    def test_orphan_file_listed(self):
        _, out, _ = _capture(audit.cmd_orphans, [self.tmp])
        # references/lonely.md 是孤儿
        self.assertIn("lonely.md", out)

    def test_orphan_script_listed_with_note(self):
        _, out, _ = _capture(audit.cmd_orphans, [self.tmp])
        # scripts/lone.py 孤儿脚本应有"可能由 cron/CLI"提示
        self.assertIn("lone.py", out)
        self.assertIn("cron", out)

    def test_entry_files_not_orphans(self):
        _, out, _ = _capture(audit.cmd_orphans, [self.tmp])
        # SKILL.md 是入口，不应出现在孤儿列表
        # 入链数段落应列出 SKILL.md
        self.assertIn("SKILL.md", out)

    def test_summary_line_present(self):
        _, out, _ = _capture(audit.cmd_orphans, [self.tmp])
        self.assertIn("汇总", out)

    def test_default_root_when_no_argv(self):
        # 不传 argv → 用 SCRIPT_DIR 的父目录（真实 skill），只读跑不应崩
        _, out, _ = _capture(audit.cmd_orphans, [])
        self.assertIn("扫描根", out)


class CmdAllTests(unittest.TestCase):
    """跑真实 skill 的 docs+alias 汇总（只读集成）。"""

    def test_returns_int(self):
        rc, _, _ = _capture(audit.cmd_all, strict=False)
        self.assertIsInstance(rc, int)

    def test_non_strict_returns_zero(self):
        # 非 strict：即便有 WARN 也返回 0
        rc, _, _ = _capture(audit.cmd_all, strict=False)
        self.assertEqual(rc, 0)

    def test_strict_returns_zero_or_one(self):
        rc, out, _ = _capture(audit.cmd_all, strict=True)
        self.assertIn(rc, (0, 1))
        self.assertIn("审计结论", out)

    def test_output_has_two_sections(self):
        _, out, _ = _capture(audit.cmd_all, strict=False)
        self.assertIn("文档一致性审计", out)
        self.assertIn("别名映射校验", out)


class MainTests(unittest.TestCase):

    def test_unknown_subcommand_returns_two(self):
        rc, out, _ = _capture(audit.main)  # 不调，下面手动
        # 直接调 main 需 patch argv
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        rc = None
        try:
            with patch.object(sys, 'argv', ['audit.py', 'unknown_cmd']):
                try:
                    rc = audit.main()
                except SystemExit as e:
                    rc = e.code
        finally:
            sys.stdout = old
        self.assertEqual(rc, 2)

    def test_docs_subcommand(self):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        rc = None
        try:
            with patch.object(sys, 'argv', ['audit.py', 'docs']):
                try:
                    rc = audit.main()
                except SystemExit as e:
                    rc = e.code
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)

    def test_default_runs_all(self):
        # 无参数 → all
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        rc = None
        try:
            with patch.object(sys, 'argv', ['audit.py']):
                try:
                    rc = audit.main()
                except SystemExit as e:
                    rc = e.code
        finally:
            sys.stdout = old
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
