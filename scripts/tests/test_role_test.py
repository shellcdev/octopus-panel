# -*- coding: utf-8 -*-
"""role_test.py 单元测试。

被测对象：``build_test_prompt``（构建发给子 Agent 的测试 prompt）。
纯函数，无 I/O。
"""
import unittest

from _helpers import SCRIPTS_DIR  # noqa: F401
import role_test


CARD = {
    "name": "赌徒",
    "archetype": "激进派",
    "stance": "梭了",
    "style_lock": "每句话必须有数字",
    "soft_spot": "提最后一次会沉默",
}


class BuildTestPromptTests(unittest.TestCase):

    def test_prompt_contains_all_role_fields(self):
        prompt = role_test.build_test_prompt(dict(CARD), "要不要辞职")
        for v in CARD.values():
            self.assertIn(v, prompt)

    def test_question_embedded(self):
        q = "要不要把全部积蓄投入股市"
        prompt = role_test.build_test_prompt(dict(CARD), q)
        self.assertIn(q, prompt)
        self.assertIn("问题：" + q, prompt)

    def test_round_number_customizable(self):
        p1 = role_test.build_test_prompt(dict(CARD), "x", round_num=1)
        p2 = role_test.build_test_prompt(dict(CARD), "x", round_num=2)
        self.assertIn("第 1 轮", p1)
        self.assertIn("第 2 轮", p2)
        self.assertIn("共 2 轮", p2)

    def test_default_round_is_1(self):
        prompt = role_test.build_test_prompt(dict(CARD), "x")
        self.assertIn("第 1 轮", prompt)

    def test_missing_fields_use_defaults(self):
        prompt = role_test.build_test_prompt({}, "问题")
        # 缺 name → "未知角色"
        self.assertIn("未知角色", prompt)
        # 立场行为空串
        self.assertIn("你的立场：", prompt)
        self.assertIn("你的风格约束锁：", prompt)
        self.assertIn("你的软肋：", prompt)

    def test_style_lock_appears_twice(self):
        sl = "特殊风格锁XYZ"
        card = dict(CARD, style_lock=sl)
        prompt = role_test.build_test_prompt(card, "问题")
        # 一次在"你的风格约束锁"，一次在"必须遵守风格约束锁"
        self.assertEqual(prompt.count(sl), 2)

    def test_required_constraints_present(self):
        prompt = role_test.build_test_prompt(dict(CARD), "问题")
        self.assertIn("≤50 字", prompt)
        self.assertIn("立场鲜明", prompt)
        self.assertIn("直接输出你的发言", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
