# -*- coding: utf-8 -*-
"""role_export.py 单元测试。

被测对象：``export_role`` / ``import_role`` / ``_avg_score`` / ``_top_category``。

export/import 经由 ``growth_api`` 读写，继承 :class:`IsolatedGrowthTest` 隔离；
``_avg_score`` / ``_top_category`` 接受 dict 的纯函数。
"""
import unittest

from _helpers import IsolatedGrowthTest  # noqa: F401
import role_export


class AvgScoreTests(IsolatedGrowthTest):

    def test_no_scores_returns_zero(self):
        self.assertEqual(role_export._avg_score({"stance_history": []}), 0)

    def test_with_scores(self):
        data = {"stance_history": [{"score": 60}, {"score": 80}]}
        self.assertEqual(role_export._avg_score(data), 70.0)

    def test_ignores_none_scores(self):
        data = {"stance_history": [{"score": 60}, {"score": None}, {"score": 80}]}
        self.assertEqual(role_export._avg_score(data), 70.0)


class TopCategoryTests(IsolatedGrowthTest):

    def test_no_history_returns_general(self):
        self.assertEqual(role_export._top_category({"stance_history": []}), "general")

    def test_most_frequent_category(self):
        # 两个 career + 一个 financial → career
        data = {"stance_history": [
            {"topic": "跳槽"}, {"topic": "加薪"}, {"topic": "买房"},
        ]}
        self.assertEqual(role_export._top_category(data), "career")

    def test_tie_returns_one_of_winners(self):
        data = {"stance_history": [{"topic": "跳槽"}, {"topic": "买房"}]}
        top = role_export._top_category(data)
        self.assertIn(top, ("career", "financial"))


class ExportRoleTests(IsolatedGrowthTest):

    def test_missing_role_returns_none(self):
        self.assertIsNone(role_export.export_role("Nobody"))

    def test_export_structure(self):
        import growth_api
        growth_api.upsert_role({
            "role_id": "甲", "level": 3, "total_sessions": 2, "exp": 500,
            "stance_history": [{"topic": "跳槽", "stance": "走", "score": 70, "session_id": "secret-id"}],
            "career_events": [{"event": "E", "description": "描述", "occurred_at": "t"}],
            "achievements": [{"id": "A", "name": "n", "description": "d"}],
            "auto_tags": ["标签(80%)"],
        })
        export = role_export.export_role("甲")
        self.assertEqual(export["role_id"], "甲")
        self.assertEqual(export["template_source"], "octopus-panel")
        self.assertIn("stats", export)
        self.assertIn("stance_history", export)
        self.assertIn("career_events", export)
        self.assertIn("achievements", export)

    def test_stance_history_sanitized(self):
        import growth_api
        growth_api.upsert_role({
            "role_id": "甲",
            "stance_history": [{"topic": "跳槽", "stance": "走", "score": 70, "session_id": "secret"}],
        })
        export = role_export.export_role("甲")
        s = export["stance_history"][0]
        # 敏感字段被剥离，保留分类
        self.assertNotIn("session_id", s)
        self.assertNotIn("topic", s)
        self.assertIn("topic_category", s)
        self.assertEqual(s["topic_category"], "career")
        self.assertEqual(s["stance"], "走")

    def test_career_events_description_truncated(self):
        import growth_api
        long_desc = "描述" * 50  # 100 字
        growth_api.upsert_role({
            "role_id": "甲",
            "career_events": [{"event": "E", "description": long_desc, "occurred_at": "t"}],
        })
        export = role_export.export_role("甲")
        desc = export["career_events"][0]["description"]
        self.assertLessEqual(len(desc), 60)
        # discussion 上下文被剥离，只保留 event + description
        self.assertNotIn("occurred_at", export["career_events"][0])

    def test_stats_computed(self):
        import growth_api
        growth_api.upsert_role({
            "role_id": "甲", "total_sessions": 5,
            "stance_history": [{"topic": "跳槽", "stance": "走", "score": 80}],
            "achievements": [{"id": "A"}],
        })
        export = role_export.export_role("甲")
        self.assertEqual(export["stats"]["total_sessions"], 5)
        self.assertEqual(export["stats"]["avg_score"], 80.0)
        self.assertEqual(export["stats"]["achievements_count"], 1)
        self.assertEqual(export["stats"]["top_category"], "career")


class ImportRoleTests(IsolatedGrowthTest):

    def test_import_creates_role(self):
        export_data = {
            "role_id": "导入角色",
            "template_source": "外部来源",
            "exported_at": "2026-01-01T00:00:00",
            "stats": {"total_sessions": 10},
        }
        ok = role_export.import_role(export_data)
        self.assertTrue(ok)

    def test_import_already_exists_skipped(self):
        import growth_api
        growth_api.upsert_role({"role_id": "已存在", "level": 5})
        export_data = {"role_id": "已存在", "template_source": "x", "exported_at": "t", "stats": {}}
        ok = role_export.import_role(export_data)
        self.assertFalse(ok)
        # 原数据不被覆盖
        self.assertEqual(growth_api.get_role_growth("已存在")["level"], 5)

    def test_imported_role_starts_fresh(self):
        export_data = {
            "role_id": "新角色",
            "template_source": "集市",
            "exported_at": "2026-01-01",
            "stats": {"total_sessions": 99},  # 历史场次不带入
        }
        role_export.import_role(export_data)
        import growth_api
        role = growth_api.get_role_growth("新角色")
        self.assertEqual(role["level"], 1)
        self.assertEqual(role["exp"], 0)
        self.assertEqual(role["total_sessions"], 0)
        # 含 IMPORTED 生涯事件
        self.assertTrue(any(e["event"] == "IMPORTED" for e in role["career_events"]))

    def test_import_default_role_id(self):
        # 缺 role_id → 用默认 'ImportedRole'
        role_export.import_role({"template_source": "x", "exported_at": "t", "stats": {}})
        import growth_api
        self.assertIsNotNone(growth_api.get_role_growth("ImportedRole"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
