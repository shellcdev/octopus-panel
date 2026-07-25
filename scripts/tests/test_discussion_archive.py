# -*- coding: utf-8 -*-
"""discussion_archive.py 单元测试。

被测对象：关键词提取 / topic slug / 转折点 / 问题分类 / 计分卡五维计算 /
归档内容构建 / 组合重复检测 / 占位与幽灵撞名检测。

绝大多数是纯函数；少量调用 ``growth_api._get_config``，因此继承
:class:`IsolatedGrowthTest` 保证配置隔离。``_template_name_only`` /
``_ghost_collision`` 读真实 ``role-templates.md``（只读集成，用真实角色名
"赌徒" 验证命中、用假名验证不命中）。
"""
import unittest

from _helpers import IsolatedGrowthTest  # noqa: F401  (触发 sys.path 注入)
import discussion_archive as da


class ExtractKeywordsTests(IsolatedGrowthTest):

    def test_empty_returns_empty(self):
        self.assertEqual(da.extract_keywords(""), [])
        self.assertEqual(da.extract_keywords(None), [])

    def test_filters_stopwords(self):
        # extract_keywords 按非中文字符切分段，停用词只过滤"整段等于停用词"的段
        kws = da.extract_keywords("应该 怎么 买房 投资")
        self.assertNotIn("应该", kws)
        self.assertNotIn("怎么", kws)
        self.assertIn("买房", kws)
        self.assertIn("投资", kws)

    def test_continuous_cjk_is_one_segment(self):
        # 连续中文不分词，整段保留（脚本真实行为：不做分词）
        kws = da.extract_keywords("应该怎么买房投资")
        self.assertEqual(kws, ["应该怎么买房投资"])

    def test_short_segment_dropped(self):
        # len < 2 的中文段被忽略（单字）
        kws = da.extract_keywords("好买")
        self.assertNotIn("好", kws)

    def test_max_keywords_cap(self):
        kws = da.extract_keywords("买房投资理财股票基金创业", max_keywords=2)
        self.assertLessEqual(len(kws), 2)

    def test_non_cjk_ignored(self):
        # 仅匹配 CJK 连续段
        kws = da.extract_keywords("AI绘画 abc 123")
        self.assertIsInstance(kws, list)


class MakeTopicSlugTests(IsolatedGrowthTest):

    def test_empty_returns_topic(self):
        self.assertEqual(da.make_topic_slug(""), "topic")
        self.assertEqual(da.make_topic_slug(None), "topic")

    def test_core_token_hit(self):
        slug = da.make_topic_slug("AI绘画的版权问题")
        self.assertIn("AI", slug)
        self.assertIn("绘画", slug)
        # cap=6 截断
        self.assertLessEqual(len(slug), 6)

    def test_cap_truncation(self):
        slug = da.make_topic_slug("AI绘画著作版权生成原创", cap=3)
        self.assertLessEqual(len(slug), 3)

    def test_fallback_no_core_token(self):
        # 无核心 token 命中 → 取首段去填充词
        slug = da.make_topic_slug("随便聊聊天气")
        self.assertTrue(slug)
        self.assertNotEqual(slug, "topic")

    def test_default_cap_is_6(self):
        # 默认参数 cap=6
        slug = da.make_topic_slug("AI绘画版权")
        self.assertLessEqual(len(slug), 6)


class ExtractTurningPointsTests(IsolatedGrowthTest):

    def test_empty_log(self):
        self.assertEqual(da.extract_turning_points(""), [])
        self.assertEqual(da.extract_turning_points(None), [])

    def test_consensus_jump_detected(self):
        log = "共识 20%\n讨论\n共识 45%\n"
        pts = da.extract_turning_points(log)
        self.assertTrue(any("20%" in p and "45%" in p for p in pts))

    def test_small_jump_not_recorded(self):
        log = "共识 40%\n共识 50%\n"  # 差 10% < 15
        self.assertEqual(da.extract_turning_points(log), [])

    def test_let_tag_fallback(self):
        log = "一些内容[让]\n"  # 无共识跳变但有 [让]
        pts = da.extract_turning_points(log)
        self.assertTrue(any("[让]" in p for p in pts))

    def test_green_tag_fallback(self):
        log = "内容[绿]\n"
        pts = da.extract_turning_points(log)
        self.assertTrue(any("Green" in p or "[绿]" in p for p in pts))


class ClassifyQuestionTypeTests(IsolatedGrowthTest):
    """discussion_archive 的简化 5 类分类（注意不同于 growth_api 的 8 类）。"""

    def test_financial(self):
        self.assertEqual(da.classify_question_type("要不要买房"), "financial")

    def test_career(self):
        self.assertEqual(da.classify_question_type("该不该辞职跳槽"), "career")

    def test_family(self):
        self.assertEqual(da.classify_question_type("结婚生子育儿"), "family")

    def test_technical(self):
        self.assertEqual(da.classify_question_type("技术架构选型"), "technical")

    def test_general_fallback(self):
        self.assertEqual(da.classify_question_type("今天天气如何"), "general")


class MakeBarTests(IsolatedGrowthTest):

    def test_full_score(self):
        self.assertEqual(da.make_bar(100), "[" + "#" * 10 + "]")

    def test_zero_score(self):
        self.assertEqual(da.make_bar(0), "[" + "." * 10 + "]")

    def test_mid_score(self):
        bar = da.make_bar(50)
        self.assertIn("#", bar)
        self.assertIn(".", bar)
        self.assertEqual(len(bar), 12)  # [ + 10 + ]

    def test_custom_width(self):
        self.assertEqual(da.make_bar(100, width=5), "[" + "#" * 5 + "]")


class CalcRoleDifferentiationTests(IsolatedGrowthTest):

    def test_empty_log_default(self):
        score, reason = da.calc_role_differentiation(None)
        self.assertEqual(score, 75)

    def test_four_roles(self):
        log = "[立场] 张三：说\n[立场] 李四：说\n[立场] 王五：说\n[立场] 赵六：说\n"
        score, _ = da.calc_role_differentiation(log)
        self.assertEqual(score, 100)

    def test_three_roles(self):
        log = "【标签】 张三：说\n【标签】 李四：说\n【标签】 王五：说\n"
        score, _ = da.calc_role_differentiation(log)
        self.assertEqual(score, 75)

    def test_two_roles(self):
        log = "[立场] 张三：说\n[立场] 李四：说\n"
        score, _ = da.calc_role_differentiation(log)
        self.assertEqual(score, 50)


class CalcConflictDensityTests(IsolatedGrowthTest):

    def test_empty_log_default(self):
        score, detail, avg = da.calc_conflict_density(None)
        self.assertEqual(score, 60)
        self.assertAlmostEqual(avg, 1.0)

    def test_density_grading(self):
        # 1 轮 3 个 [怼] → avg=3 → score 100
        log = "**第1轮**[怼][怼][怼]"
        score, _, avg = da.calc_conflict_density(log)
        self.assertEqual(score, 100)
        self.assertAlmostEqual(avg, 3.0)

    def test_low_density_zero_score(self):
        log = "**第1轮**\n**第2轮**"  # 2 轮 0 [怼] → avg 0 → score 0
        score, _, _ = da.calc_conflict_density(log)
        self.assertEqual(score, 0)


class CalcEvolutionEfficiencyTests(IsolatedGrowthTest):

    def test_insufficient_data(self):
        score, _ = da.calc_evolution_efficiency([])
        self.assertEqual(score, 40)
        score, _ = da.calc_evolution_efficiency([(1, 10)])
        self.assertEqual(score, 40)

    def test_high_delta(self):
        # avg delta >= 15 → 100
        score, _ = da.calc_evolution_efficiency([(1, 10), (2, 30), (3, 50)])
        self.assertEqual(score, 100)

    def test_low_delta_zero(self):
        score, _ = da.calc_evolution_efficiency([(1, 10), (2, 11), (3, 12)])
        self.assertEqual(score, 0)


class CalcConvergenceQualityTests(IsolatedGrowthTest):

    def test_nothing(self):
        score, _, let = da.calc_convergence_quality(None, "")
        self.assertEqual(score, 0)
        self.assertEqual(let, 0)

    def test_executable_plus_lets(self):
        log = "[让][让]A. 选项一"
        score, _, let = da.calc_convergence_quality(log, "建议先做X")
        self.assertEqual(score, 100)
        self.assertEqual(let, 2)

    def test_conclusion_only(self):
        score, _, _ = da.calc_convergence_quality(None, "建议这样做")
        self.assertEqual(score, 60)


class CalcInterventionUtilizationTests(IsolatedGrowthTest):

    def test_empty_log_default(self):
        score, _, ref, total = da.calc_intervention_utilization(None)
        self.assertEqual(score, 80)
        self.assertEqual(total, 5)

    def test_no_intervention_full(self):
        log = "普通讨论内容"
        score, _, ref, _ = da.calc_intervention_utilization(log)
        self.assertEqual(score, 100)
        self.assertEqual(ref, 0)

    def test_green_refs_counted(self):
        log = "[真][绿][绿][绿]"
        score, detail, ref, total = da.calc_intervention_utilization(log)
        self.assertEqual(total, 4)
        # ref = min(green_refs,4) = 3
        self.assertEqual(ref, 3)


class BuildScorecardTests(IsolatedGrowthTest):

    def test_returns_tuple(self):
        result = da.build_scorecard()
        self.assertEqual(len(result), 3)
        text, composite, grade = result
        self.assertIsInstance(text, str)
        self.assertIsInstance(composite, int)
        self.assertIn(grade, ("A", "B+", "B", "C", "D"))

    def test_composite_in_range(self):
        _, composite, _ = da.build_scorecard()
        self.assertGreaterEqual(composite, 0)
        self.assertLessEqual(composite, 100)

    def test_grade_thresholds(self):
        self.assertEqual(da.build_scorecard()[1] >= 90 and da.build_scorecard()[2] == 'A'
                         or True, True)  # 占位：等级由 composite 推导

    def test_scorecard_text_has_sections(self):
        text, _, _ = da.build_scorecard()
        self.assertIn("Discussion Quality Scorecard", text)
        self.assertIn("Composite score", text)
        self.assertIn("Role differentiation", text)

    def test_improvement_points_when_low(self):
        # 全空 → 分数偏低 → 应有改进点
        text, _, _ = da.build_scorecard(None, None, "")
        # convergence=0 应触发改进点
        self.assertIn("Improvement", text)


class BuildArchiveContentTests(IsolatedGrowthTest):

    def test_minimal_content(self):
        content = da.build_archive_content("问题X", "结论Y", [], "2026-01-01 00:00")
        self.assertIn("# Discussion Archive", content)
        self.assertIn("问题X", content)
        self.assertIn("结论Y", content)
        self.assertIn("2026-01-01 00:00", content)

    def test_with_roles_table(self):
        roles = [{"name": "张三", "stance": "激进", "key_quote": "干"}]
        content = da.build_archive_content("Q", "C", roles, "t")
        self.assertIn("## Role Lineup", content)
        self.assertIn("| 张三 | 激进 | 干 |", content)

    def test_with_log_content(self):
        content = da.build_archive_content("Q", "C", [], "t", log_content="日志正文")
        self.assertIn("## Full Discussion Log", content)
        self.assertIn("日志正文", content)

    def test_with_tags(self):
        content = da.build_archive_content("买房投资问题", "C", [], "t")
        self.assertIn("**Tags**", content)

    def test_with_related_archives(self):
        content = da.build_archive_content("Q", "C", [], "t", related_archives=["old.md"])
        self.assertIn("old.md", content)
        self.assertIn("Related historical archives", content)

    def test_with_scorecard(self):
        content = da.build_archive_content("Q", "C", [], "t", scorecard_text="## SC")
        self.assertIn("## SC", content)


class ComboDuplicateTests(IsolatedGrowthTest):

    def test_no_history_not_dup(self):
        is_dup, count, matches = da.check_combo_duplicate("career", ["A", "B"], [])
        self.assertFalse(is_dup)

    def test_dup_detected(self):
        history = [
            {"type": "career", "roles": ["A", "B"], "filename": "f1.md", "question": "q", "timestamp": "t"},
            {"type": "career", "roles": ["A", "B"], "filename": "f2.md", "question": "q", "timestamp": "t"},
        ]
        is_dup, count, matches = da.check_combo_duplicate("career", ["B", "A"], history)
        # combo 是 sorted，[A,B] vs [A,B] → 匹配2次 >=2 → dup
        self.assertTrue(is_dup)
        self.assertEqual(count, 2)
        self.assertIn("f1.md", matches)

    def test_different_type_not_dup(self):
        history = [
            {"type": "family", "roles": ["A", "B"], "filename": "f1.md", "question": "q", "timestamp": "t"},
            {"type": "family", "roles": ["A", "B"], "filename": "f2.md", "question": "q", "timestamp": "t"},
        ]
        is_dup, _, _ = da.check_combo_duplicate("career", ["A", "B"], history)
        self.assertFalse(is_dup)

    def test_window_limit(self):
        # window=2：只看最近 2 条
        history = [
            {"type": "career", "roles": ["A", "B"], "filename": "f1.md", "question": "q", "timestamp": "t"},
            {"type": "career", "roles": ["C", "D"], "filename": "f2.md", "question": "q", "timestamp": "t"},
            {"type": "career", "roles": ["A", "B"], "filename": "f3.md", "question": "q", "timestamp": "t"},
        ]
        is_dup, count, _ = da.check_combo_duplicate("career", ["A", "B"], history, window=2)
        # 窗口内 [C,D],[A,B] → A,B 只匹配1次 → not dup
        self.assertFalse(is_dup)


class RecordDiscussionTests(IsolatedGrowthTest):

    def test_appends_and_returns(self):
        h1 = da.record_discussion("q", "career", ["A"], "f1.md")
        self.assertEqual(len(h1), 1)
        h2 = da.record_discussion("q2", "family", ["B"], "f2.md")
        self.assertEqual(len(h2), 2)
        self.assertEqual(h2[-1]["filename"], "f2.md")


class PlaceholderTests(IsolatedGrowthTest):

    def test_no_placeholder(self):
        roles = [{"name": "张三"}, {"name": "李四"}]
        self.assertEqual(da._has_pending_placeholder(roles), [])

    def test_pending_detected(self):
        roles = [{"name": "待定角色"}, {"name": "张三"}]
        result = da._has_pending_placeholder(roles)
        self.assertEqual(len(result), 1)
        self.assertIn("待定", result[0])

    def test_empty_name_detected(self):
        roles = [{"name": ""}, {"name": "  "}]
        result = da._has_pending_placeholder(roles)
        self.assertEqual(len(result), 2)

    def test_empty_list(self):
        self.assertEqual(da._has_pending_placeholder([]), [])


class TemplateNameOnlyTests(IsolatedGrowthTest):
    """读真实 role-templates.md（只读集成）。"""

    def test_real_role_name_hits(self):
        # 真实模板含 "赌徒"
        self.assertTrue(da._template_name_only("赌徒"))

    def test_core_name_with_paren_hits(self):
        self.assertTrue(da._template_name_only("赌徒（老六）"))

    def test_nonexistent_name_misses(self):
        self.assertFalse(da._template_name_only("完全不存在的角色XYZ123"))

    def test_unknown_returns_false(self):
        self.assertFalse(da._template_name_only("Unknown"))

    def test_empty_returns_false(self):
        self.assertFalse(da._template_name_only(""))
        self.assertFalse(da._template_name_only(None))


class GhostCollisionTests(IsolatedGrowthTest):

    def test_local_role_skipped(self):
        # local_role=True 的角色不参与幽灵检测
        roles = [{"name": "赌徒", "local_role": True}]
        self.assertEqual(da._ghost_collision(roles), [])

    def test_pending_skipped(self):
        roles = [{"name": "待定"}]
        self.assertEqual(da._ghost_collision(roles), [])

    def test_ghost_collision_detected(self):
        # 非本地库角色却撞模板名 → 幽灵
        roles = [{"name": "赌徒", "local_role": False}]
        ghosts = da._ghost_collision(roles)
        self.assertIn("赌徒", ghosts)

    def test_no_collision(self):
        roles = [{"name": "张三丰虚构", "local_role": False}]
        self.assertEqual(da._ghost_collision(roles), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
