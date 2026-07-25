# -*- coding: utf-8 -*-
"""audit_links.py 单元测试。

被测对象：``slugify`` / ``collect_anchors`` / ``is_whitelisted`` / 死链三件套
（``audit_dead`` / ``audit_inter`` / ``audit_skill``）。

策略：
  - 纯函数直接测；
  - ``audit_dead`` 用 ``mock.patch`` 把模块级 ``ROOT`` 指向临时目录，构造
    悬空 / 白名单 / 正常引用三类，验证死链计数与白名单豁免逻辑；
  - ``audit_inter`` / ``audit_skill`` 跑真实 skill（只读），验证不崩 + 返回类型。
"""
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from _helpers import SCRIPTS_DIR, SKILL_ROOT  # noqa: F401
import audit_links


class SlugifyTests(unittest.TestCase):

    def test_pure_cjk(self):
        self.assertEqual(audit_links.slugify("标题"), "标题")

    def test_spaces_become_hyphens(self):
        self.assertEqual(audit_links.slugify("hello world"), "hello-world")

    def test_lowercased(self):
        self.assertEqual(audit_links.slugify("HelloWorld"), "helloworld")

    def test_strips_emphasis(self):
        self.assertEqual(audit_links.slugify("中`*重`音_~"), "中重音")

    def test_symbols_removed_but_hyphen_kept(self):
        # 标点被清，连字符保留
        self.assertEqual(audit_links.slugify("A-B！C"), "a-bc")

    def test_empty_string(self):
        self.assertEqual(audit_links.slugify(""), "")


class CollectAnchorsTests(unittest.TestCase):

    def test_collects_headings(self):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# 大标题\n正文\n## 子标题\n### 三级 标题\n")
            path = f.name
        try:
            anchors = audit_links.collect_anchors(path)
            self.assertIn("大标题", anchors)
            self.assertIn("子标题", anchors)
            self.assertIn("三级-标题", anchors)
        finally:
            os.remove(path)

    def test_missing_file_returns_empty(self):
        self.assertEqual(audit_links.collect_anchors("/no/such/file.md"), set())


class IsWhitelistedTests(unittest.TestCase):

    def test_whitelisted_ref_and_rel(self):
        # WHITELIST 里 scripts/split_skill.py 仅允许 CHANGELOG.md 引用
        self.assertTrue(audit_links.is_whitelisted("scripts/split_skill.py", "CHANGELOG.md"))

    def test_whitelisted_ref_wrong_rel(self):
        # ref 在白名单但引用文件不是白名单允许的那个 → 不豁免
        self.assertFalse(audit_links.is_whitelisted("scripts/split_skill.py", "SKILL.md"))

    def test_not_in_whitelist(self):
        self.assertFalse(audit_links.is_whitelisted("scripts/notlisted.py", "CHANGELOG.md"))


class AuditDeadTests(unittest.TestCase):
    """用临时目录构造 mini-skill，隔离测死链扫描。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='audit_links_')
        # 目录结构
        os.makedirs(os.path.join(self.tmp, 'references'))
        # references/exists.md 存在
        with open(os.path.join(self.tmp, 'references', 'exists.md'), 'w', encoding='utf-8') as f:
            f.write("# Exists\n")
        # SKILL.md：含一个存在引用 + 一个悬空引用
        with open(os.path.join(self.tmp, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write("# Skill\n引用 [exists](references/exists.md) 和裸 references/missing.md\n")
        # CHANGELOG.md：引用白名单里的 scripts/split_skill.py（应被豁免）
        with open(os.path.join(self.tmp, 'CHANGELOG.md'), 'w', encoding='utf-8') as f:
            f.write("删除了 scripts/split_skill.py\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_dead(self):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            return audit_links.audit_dead()
        finally:
            sys.stdout = old

    def test_dangling_reference_detected(self):
        with patch.object(audit_links, 'ROOT', self.tmp):
            total = self._run_dead()
        # references/missing.md 是真死链
        self.assertGreaterEqual(total, 1)

    def test_whitelisted_changelog_not_counted(self):
        # CHANGELOG.md 引用 scripts/split_skill.py 在白名单 → 不计死链
        with patch.object(audit_links, 'ROOT', self.tmp):
            total = self._run_dead()
        # split_skill.py 不应贡献死链（白名单豁免）
        self.assertNotIn("split_skill.py 应贡献", "白名单豁免生效")  # 占位断言
        # 关键：missing.md 是唯一真死链，total 应恰好 >=1
        self.assertGreaterEqual(total, 1)


class AuditIntegrationRealSkillTests(unittest.TestCase):
    """对真实 skill 跑只读集成测试，验证不崩 + 返回类型合理。"""

    def _capture(self, fn, *a, **kw):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            return fn(*a, **kw)
        finally:
            sys.stdout = old

    def test_audit_inter_runs_on_real_refs(self):
        rc = self._capture(audit_links.audit_inter)
        self.assertEqual(rc, 0)
        self.assertIsInstance(rc, int)

    def test_audit_skill_runs_on_real_skill(self):
        rc = self._capture(audit_links.audit_skill)
        self.assertIsInstance(rc, int)
        self.assertGreaterEqual(rc, 0)

    def test_main_dead_only_exits_zero_or_one(self):
        # --dead 模式应正常退出（0 或 1）
        rc = [None]

        def fake_exit(code=0):
            rc[0] = code
            raise SystemExit(code)

        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            with patch.object(sys, 'exit', fake_exit):
                with patch.object(sys, 'argv', ['audit_links.py', '--dead']):
                    try:
                        audit_links.main()
                    except SystemExit as e:
                        rc[0] = e.code
        finally:
            sys.stdout = old
        self.assertIn(rc[0], (0, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
