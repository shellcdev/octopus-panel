# -*- coding: utf-8 -*-
"""tag_filter.py 单元测试。

被测对象：``GROUP_KEYWORDS`` / ``parse_roles`` / ``match_role``。

策略：
  - ``parse_roles`` 用临时构造的 mini 模板文件精确验证章节分组、角色行、
    标签行解析（含引用前缀剥离）；
  - ``match_role`` 覆盖单/多条件、大小写、header/group/tags 各源；
  - 用真实 role-templates.md 做只读集成，验证实际角色数 > 0 且分组合理。
"""
import os
import tempfile
import unittest

from _helpers import SCRIPTS_DIR, ROLE_TEMPLATES  # noqa: F401
import tag_filter


SAMPLE_TEMPLATE = """# 角色模板库

## 通用角色组：人生决策类

### 🃏 测试甲（代号一）

> 🏷️ 立场：激进 | 视角：当事人 | 风格：情绪型

背景正文。

### 💀 测试乙

> 🏷️ 立场：保守 | 视角：第三方

正文。

## 通用角色组：商业决策类

### 🎯 测试丙

正文无标签行。
"""


class GroupKeywordsTests(unittest.TestCase):

    def test_eight_groups(self):
        self.assertEqual(len(tag_filter.GROUP_KEYWORDS), 8)
        for kw, gname in tag_filter.GROUP_KEYWORDS.items():
            self.assertTrue(kw)
            self.assertTrue(gname.endswith('组'))


class ParseRolesTests(unittest.TestCase):

    def _write(self, content):
        f = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_parse_sample_roles_count(self):
        path = self._write(SAMPLE_TEMPLATE)
        roles = tag_filter.parse_roles(path)
        self.assertEqual(len(roles), 3)

    def test_group_assignment(self):
        path = self._write(SAMPLE_TEMPLATE)
        roles = tag_filter.parse_roles(path)
        by_header = {r['header']: r for r in roles}
        self.assertEqual(by_header['🃏 测试甲（代号一）']['group'], '人生组')
        self.assertEqual(by_header['💀 测试乙']['group'], '人生组')
        self.assertEqual(by_header['🎯 测试丙']['group'], '商业组')

    def test_tags_parsed_from_blockquote(self):
        path = self._write(SAMPLE_TEMPLATE)
        roles = tag_filter.parse_roles(path)
        a = [r for r in roles if '测试甲' in r['header']][0]
        # 引用前缀 > 应被剥离；标签值被解析（key 会带 emoji 前缀如 '🏷️ 立场'，
        # 故用 value 断言更贴脚本真实行为）
        self.assertIn('激进', a['tags'].values())
        self.assertIn('当事人', a['tags'].values())
        self.assertIn('情绪型', a['tags'].values())
        self.assertIn('立场：激进', a['tag_line'])
        # 不应残留引用前缀
        self.assertFalse(a['tag_line'].startswith('>'))

    def test_role_without_tagline(self):
        path = self._write(SAMPLE_TEMPLATE)
        roles = tag_filter.parse_roles(path)
        c = [r for r in roles if '测试丙' in r['header']][0]
        self.assertEqual(c['tags'], {})
        self.assertEqual(c['tag_line'], '')

    def test_empty_file(self):
        path = self._write("")
        self.assertEqual(tag_filter.parse_roles(path), [])


class MatchRoleTests(unittest.TestCase):

    def _role(self, header, group, tags):
        return {'header': header, 'group': group, 'tags': tags, 'tag_line': ''}

    def test_single_condition_in_header(self):
        r = self._role('测试甲', '人生组', {})
        self.assertTrue(tag_filter.match_role(r, ['测试']))

    def test_multi_condition_all_match(self):
        r = self._role('测试甲', '人生组', {'立场': '激进', '视角': '当事人'})
        self.assertTrue(tag_filter.match_role(r, ['激进', '当事人', '人生']))

    def test_one_missing_condition_fails(self):
        r = self._role('测试甲', '人生组', {'立场': '激进'})
        self.assertFalse(tag_filter.match_role(r, ['激进', '不存在']))

    def test_case_insensitive(self):
        r = self._role('Aggressive Role', '商业组', {'立场': 'Hostile'})
        self.assertTrue(tag_filter.match_role(r, ['AGGRESSIVE', 'hostile']))

    def test_tag_value_matched(self):
        r = self._role('某角色', '技术架构组', {'风格': '数据型'})
        self.assertTrue(tag_filter.match_role(r, ['数据型']))

    def test_empty_conditions_match_all(self):
        # 无条件 → 空 for 循环不返回 False → True
        r = self._role('任意', '家庭组', {})
        self.assertTrue(tag_filter.match_role(r, []))


class RealTemplateIntegrationTests(unittest.TestCase):

    def test_parse_real_templates(self):
        roles = tag_filter.parse_roles(ROLE_TEMPLATES)
        self.assertGreater(len(roles), 0, "真实模板应解析出至少 1 个角色")
        for r in roles:
            self.assertIn('header', r)
            self.assertIn('group', r)
            self.assertTrue(r['group'].endswith('组') or r['group'] == '未分组')

    def test_group_distribution(self):
        roles = tag_filter.parse_roles(ROLE_TEMPLATES)
        groups = {r['group'] for r in roles}
        # 至少命中 2 个组
        self.assertGreater(len(groups), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
