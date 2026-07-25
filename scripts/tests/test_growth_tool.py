# -*- coding: utf-8 -*-
"""growth_tool.py 单元测试。

被测对象：``render_full_profile`` / ``_build_narrative_summary`` /
``_period_label`` / ``_relation_type_icon`` / ``_compute_stats`` /
``render_guidance`` / ``render_session_override_notice``。

大部分是接受 dict/list 的纯函数；``render_full_profile`` / ``render_guidance``
经由 ``growth_api`` 读数据，继承 :class:`IsolatedGrowthTest` 隔离。
"""
import unittest

from _helpers import IsolatedGrowthTest  # noqa: F401
import growth_tool


class BuildNarrativeSummaryTests(IsolatedGrowthTest):

    def _entry(self, stance):
        return {"stance": stance, "topic": "x", "session_id": "x"}

    def test_less_than_two_empty(self):
        self.assertEqual(growth_tool._build_narrative_summary([self._entry("a")], "R"), "")

    def test_empty_empty(self):
        self.assertEqual(growth_tool._build_narrative_summary([], "R"), "")

    def test_consistent_stance(self):
        sh = [self._entry("立场X"), self._entry("立场X")]
        out = growth_tool._build_narrative_summary(sh, "R")
        self.assertIn("从一而终", out)

    def test_hedged_condition(self):
        sh = [self._entry("立场A"), self._entry("立场B但要看条件")]
        out = growth_tool._build_narrative_summary(sh, "R")
        self.assertIn("加条件", out)

    def test_richer_expression(self):
        # last 比 first 长，且无"条件/但"
        sh = [self._entry("短"), self._entry("这一段比较长的丰富表达")]
        out = growth_tool._build_narrative_summary(sh, "R")
        self.assertIn("丰富", out)

    def test_other_shift(self):
        # last 不比 first 长，无 hedged
        sh = [self._entry("很长很长的立场表述"), self._entry("短立场")]
        out = growth_tool._build_narrative_summary(sh, "R")
        self.assertIn("换角度", out)


class PeriodLabelTests(IsolatedGrowthTest):

    def test_single_session(self):
        self.assertEqual(growth_tool._period_label(0, 1, "stance"), "初登场")

    def test_first_is_debut_period(self):
        self.assertEqual(growth_tool._period_label(0, 5, "x"), "初登场期")

    def test_last_with_condition(self):
        self.assertEqual(growth_tool._period_label(4, 5, "带条件的立场"), "条件反思期")

    def test_last_without_condition(self):
        self.assertEqual(growth_tool._period_label(4, 5, "普通立场"), "最新立场期")

    def test_early_period(self):
        # ratio = 1/5 = 0.2 < 0.3
        self.assertEqual(growth_tool._period_label(1, 5, "x"), "早期立场期")

    def test_mid_period(self):
        # ratio = 2/5 = 0.4
        self.assertEqual(growth_tool._period_label(2, 5, "x"), "中期演化期")

    def test_late_period(self):
        # ratio = 3/5 = 0.6，非 last
        self.assertEqual(growth_tool._period_label(3, 5, "x"), "近期调整期")


class RelationTypeIconTests(IsolatedGrowthTest):

    def test_known_mappings(self):
        cases = {
            "欠人情": "🤝",
            "合作": "🤝",
            "对抗": "⚔️",
            "中立": "➖",
            "neutral": "➖",
            "friendly": "👍",
            "hostile": "👎",
        }
        for rtype, expected in cases.items():
            self.assertEqual(growth_tool._relation_type_icon(rtype), expected,
                             msg="%s 应映射到 %s" % (rtype, expected))

    def test_unknown_defaults_dash(self):
        self.assertEqual(growth_tool._relation_type_icon("未知类型"), "➖")

    def test_empty_defaults_dash(self):
        self.assertEqual(growth_tool._relation_type_icon(""), "➖")


class ComputeStatsTests(IsolatedGrowthTest):

    def test_empty_returns_empty(self):
        self.assertEqual(growth_tool._compute_stats({"stance_history": []}), [])

    def test_topic_distribution(self):
        data = {
            "stance_history": [
                {"topic": "跳槽", "stance": "x", "score": 50},
                {"topic": "加薪", "stance": "x", "score": 70},
            ],
            "relationship_lines": [],
        }
        stats = growth_tool._compute_stats(data)
        # 至少有"最爱讨论"或"平均讨论评分"
        labels = [s[0] for s in stats]
        self.assertTrue(any("讨论" in l for l in labels))

    def test_avg_score(self):
        data = {
            "stance_history": [
                {"topic": "x", "stance": "s", "score": 60},
                {"topic": "x", "stance": "s", "score": 80},
            ],
            "relationship_lines": [],
        }
        stats = dict(growth_tool._compute_stats(data))
        self.assertIn("平均讨论评分", stats)
        self.assertIn("70", stats["平均讨论评分"])

    def test_relationship_stat(self):
        data = {
            "stance_history": [],
            "relationship_lines": [
                {"target_id": "B", "co_sessions": 3, "relation_type": "neutral"},
            ],
        }
        stats = dict(growth_tool._compute_stats(data))
        self.assertIn("最常对抗", stats)
        self.assertIn("B", stats["最常对抗"])


class RenderFullProfileTests(IsolatedGrowthTest):

    def test_missing_role_empty(self):
        self.assertEqual(growth_tool.render_full_profile("Nobody"), "")

    def test_renders_header_and_level(self):
        import growth_api
        growth_api.upsert_role({"role_id": "甲", "level": 3, "total_sessions": 2, "exp": 500})
        out = growth_tool.render_full_profile("甲")
        self.assertIn("角色成长卡", out)
        self.assertIn("甲", out)
        self.assertIn("Lv.3", out)
        self.assertIn("2场", out)

    def test_renders_achievements_when_present(self):
        import growth_api
        growth_api.upsert_role({"role_id": "甲", "level": 1, "achievements": [
            {"id": "X", "name": "成就名", "description": "描述"}]})
        out = growth_tool.render_full_profile("甲")
        self.assertIn("成就墙", out)
        self.assertIn("成就名", out)

    def test_renders_growth_tree_with_history(self):
        import growth_api
        growth_api.update_stance_history("甲", "20260101-x", "跳槽", "走", 60)
        out = growth_tool.render_full_profile("甲")
        self.assertIn("成长树", out)

    def test_renders_tags_when_present(self):
        import growth_api
        growth_api.upsert_role({"role_id": "甲", "auto_tags": ["标签A(80%)"], "manual_tags": []})
        out = growth_tool.render_full_profile("甲")
        self.assertIn("标签", out)
        self.assertIn("标签A", out)


class RenderGuidanceTests(IsolatedGrowthTest):

    def test_no_data_no_guidance(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        self.assertEqual(growth_tool.render_guidance(), "")

    def test_with_relationship_data_shows_hint(self):
        import growth_api
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        growth_api.upsert_role({"role_id": "A", "relationship_lines": [{"target_id": "B"}]})
        out = growth_tool.render_guidance()
        self.assertIn("关系网络", out)


class RenderSessionOverrideNoticeTests(IsolatedGrowthTest):

    def test_disabled_notice(self):
        out = growth_tool.render_session_override_notice(False)
        self.assertIn("临时关闭", out)
        self.assertIn("下一场自动恢复", out)

    def test_restored_notice(self):
        out = growth_tool.render_session_override_notice(True)
        self.assertIn("已恢复", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
