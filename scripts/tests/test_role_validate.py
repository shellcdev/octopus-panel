# -*- coding: utf-8 -*-
"""role_validate.py 单元测试。

被测对象：``validate_role_card`` / ``RISK_QUESTIONS``。
纯函数，无文件 I/O，无需隔离。
"""
import unittest

from _helpers import SCRIPTS_DIR  # noqa: F401  (触发 sys.path 注入)
import role_validate


GOOD_CARD = {
    "name": "测试角色",
    "archetype": "通用视角",
    "stance": "干就完了",
    "style_lock": "每句话含数字不用比喻",
    "soft_spot": "被问到细节会卡壳",
}


class ValidateRoleCardTests(unittest.TestCase):

    def test_good_card_passes(self):
        passed, issues = role_validate.validate_role_card(dict(GOOD_CARD))
        self.assertTrue(passed)
        self.assertEqual(issues, [])

    def test_missing_required_field(self):
        card = dict(GOOD_CARD)
        del card["name"]
        passed, issues = role_validate.validate_role_card(card)
        self.assertFalse(passed)
        self.assertTrue(any("name" in i for i in issues))

    def test_missing_all_required(self):
        passed, issues = role_validate.validate_role_card({})
        self.assertFalse(passed)
        names = {"name", "archetype", "stance", "style_lock", "soft_spot"}
        joined = " ".join(issues)
        for n in names:
            self.assertIn(n, joined)

    def test_empty_string_value_treated_as_missing(self):
        card = dict(GOOD_CARD)
        card["stance"] = ""
        passed, issues = role_validate.validate_role_card(card)
        self.assertFalse(passed)
        self.assertTrue(any("stance" in i for i in issues))

    def test_risk_archetypes_flagged(self):
        for risk in ["小资", "凤凰男", "体制内"]:
            card = dict(GOOD_CARD)
            card["archetype"] = risk
            _, issues = role_validate.validate_role_card(card)
            self.assertTrue(any("冒犯" in i and risk in i for i in issues),
                            msg="应标记风险 archetype: %s" % risk)

    def test_normal_archetype_not_flagged(self):
        card = dict(GOOD_CARD)
        card["archetype"] = "老六"
        _, issues = role_validate.validate_role_card(card)
        self.assertFalse(any("冒犯" in i for i in issues))

    def test_short_style_lock_flagged(self):
        card = dict(GOOD_CARD)
        card["style_lock"] = "短锁"  # 2 字 < 4
        _, issues = role_validate.validate_role_card(card)
        self.assertTrue(any("风格锁过短" in i for i in issues))

    def test_style_lock_boundary_4_chars_ok(self):
        card = dict(GOOD_CARD)
        card["style_lock"] = "四字风格锁"  # 正好 5 字，≥4
        passed, issues = role_validate.validate_role_card(card)
        self.assertTrue(passed, msg=str(issues))

    def test_empty_style_lock_not_flagged(self):
        # 空字符串不进入长度判断（逻辑：if style and len(style) < 4）
        card = dict(GOOD_CARD)
        card["style_lock"] = ""
        _, issues = role_validate.validate_role_card(card)
        self.assertFalse(any("风格锁过短" in i for i in issues))

    def test_short_soft_spot_flagged(self):
        card = dict(GOOD_CARD)
        card["soft_spot"] = "软"  # 1 字 < 4
        _, issues = role_validate.validate_role_card(card)
        self.assertTrue(any("软肋描述过短" in i for i in issues))

    def test_multiple_issues_aggregated(self):
        card = {"name": "", "archetype": "凤凰男", "style_lock": "短", "soft_spot": "短"}
        passed, issues = role_validate.validate_role_card(card)
        self.assertFalse(passed)
        # 至少命中：缺字段、风险 archetype、风格锁过短、软肋过短
        self.assertGreaterEqual(len(issues), 4)


class RiskQuestionsConstantTests(unittest.TestCase):

    def test_three_questions_present(self):
        self.assertEqual(len(role_validate.RISK_QUESTIONS), 3)
        for q in role_validate.RISK_QUESTIONS:
            self.assertIsInstance(q, str)
            self.assertTrue(q.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
