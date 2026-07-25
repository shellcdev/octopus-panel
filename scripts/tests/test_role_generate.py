# -*- coding: utf-8 -*-
"""role_generate.py 单元测试。

被测对象：``QUESTION_TYPE_MAP`` / ``detect_question_type`` /
``_dynamic_generate`` / ``generate_roles``（三种模式）/ ``_load_local_roles`` /
``_pick_local_roles`` / ``_inject_growth_hint``。

``generate`` 模式纯逻辑可稳定测；``local_only`` / ``local_priority`` 与
``_load_local_roles`` 会读真实 role-templates.md（只读集成）。
"""
import unittest

from _helpers import IsolatedGrowthTest  # noqa: F401
import role_generate


class QuestionTypeMapTests(IsolatedGrowthTest):

    def test_seven_groups(self):
        self.assertEqual(len(role_generate.QUESTION_TYPE_MAP), 7)

    def test_each_group_is_list_of_names(self):
        for qtype, names in role_generate.QUESTION_TYPE_MAP.items():
            self.assertIsInstance(names, list)
            self.assertTrue(all(isinstance(n, str) for n in names))
            self.assertGreaterEqual(len(names), 3)


class DetectQuestionTypeTests(IsolatedGrowthTest):

    def test_workplace(self):
        self.assertEqual(role_generate.detect_question_type("要不要跳槽换工作"), "职场")

    def test_tech(self):
        self.assertEqual(role_generate.detect_question_type("技术架构选型"), "技术")

    def test_education(self):
        self.assertEqual(role_generate.detect_question_type("孩子升学留学"), "教育")

    def test_medical(self):
        self.assertEqual(role_generate.detect_question_type("手术诊断治疗"), "医疗")

    def test_legal(self):
        self.assertEqual(role_generate.detect_question_type("合同诉讼合规"), "法律")

    def test_startup(self):
        self.assertEqual(role_generate.detect_question_type("融资合伙人股权"), "创业")

    def test_family(self):
        self.assertEqual(role_generate.detect_question_type("父母婆媳结婚"), "家庭")

    def test_life(self):
        self.assertEqual(role_generate.detect_question_type("人生意义后悔该不该"), "人生")

    def test_general_fallback(self):
        self.assertEqual(role_generate.detect_question_type("今天吃什么"), "通用")


class DynamicGenerateGenerateModeTests(IsolatedGrowthTest):
    """mode='generate' 分支纯逻辑：只产空壳，不查本地库。"""

    def test_produces_shells(self):
        roles = role_generate._dynamic_generate("问题", 4, mode='generate')
        self.assertEqual(len(roles), 4)
        for r in roles:
            self.assertIn("待定", r["name"])
            self.assertEqual(r["archetype"], "通用视角")

    def test_count_respected(self):
        self.assertEqual(len(role_generate._dynamic_generate("x", 2, mode='generate')), 2)

    def test_no_local_lookup_in_generate_mode(self):
        # generate 模式不调 _is_local_role_name，名字恒为"待定"
        roles = role_generate._dynamic_generate("x", 3, mode='generate')
        names = {r["name"] for r in roles}
        self.assertEqual(len(names), 1)


class DynamicGenerateLocalModeTests(IsolatedGrowthTest):
    """mode='local' 分支：从 QUESTION_TYPE_MAP 取名。exclude_local=False 时不查本地库。"""

    def test_picks_from_matching_group(self):
        # 职场问题 → 取 QUESTION_TYPE_MAP["职场"] 的名字
        roles = role_generate._dynamic_generate("要不要跳槽", 4, exclude=[], exclude_local=False)
        self.assertEqual(len(roles), 4)
        names = {r["name"] for r in roles}
        self.assertTrue(names.issubset(set(role_generate.QUESTION_TYPE_MAP["职场"])))

    def test_exclude_filters_names(self):
        all_names = role_generate.QUESTION_TYPE_MAP["职场"]
        exclude = all_names[:2]
        roles = role_generate._dynamic_generate("跳槽", 2, exclude=exclude, exclude_local=False)
        for r in roles:
            self.assertNotIn(r["name"], exclude)

    def test_fallback_to_other_groups_when_insufficient(self):
        # 要 6 个但职场组只有 4 个 → 从其他组补
        roles = role_generate._dynamic_generate("跳槽", 6, exclude=[], exclude_local=False)
        self.assertEqual(len(roles), 6)

    def test_count_capped_when_exhausted(self):
        # exclude 掉几乎所有 → 用尽后停止（generic 耗尽）
        all_names = []
        for qt in ["职场", "家庭", "创业", "技术"]:
            all_names.extend(role_generate.QUESTION_TYPE_MAP.get(qt, []))
        roles = role_generate._dynamic_generate("x", 100, exclude=all_names, exclude_local=False)
        # exclude_local=False，所以不兜底合成名 → 数量 < 100
        self.assertLess(len(roles), 100)


class GenerateRolesTests(IsolatedGrowthTest):

    def test_default_generate_mode(self):
        roles, mode, notes = role_generate.generate_roles("问题", count=4)
        self.assertEqual(mode, "generate")
        self.assertEqual(len(roles), 4)
        for r in roles:
            self.assertFalse(r["local_role"])
            self.assertTrue(r.get("ephemeral"))
        self.assertTrue(any("generate" in n for n in notes))

    def test_local_only_mode(self):
        self.patch_config(role_source_mode="local_only")
        roles, mode, notes = role_generate.generate_roles("问题", count=2)
        self.assertEqual(mode, "local_only")
        # 读真实模板，应能取到角色
        self.assertGreater(len(roles), 0)

    def test_local_priority_mode(self):
        self.patch_config(role_source_mode="local_priority")
        roles, mode, notes = role_generate.generate_roles("问题", count=4)
        self.assertEqual(mode, "local_priority")
        # 至少返回部分角色
        self.assertGreater(len(roles), 0)


class LoadLocalRolesTests(IsolatedGrowthTest):
    """读真实 role-templates.md（只读集成）。"""

    def test_returns_dict_nonempty(self):
        local = role_generate._load_local_roles()
        self.assertGreater(len(local), 0)

    def test_template_roles_have_source(self):
        local = role_generate._load_local_roles()
        # 真实模板含 "赌徒"
        self.assertIn("赌徒", local)
        self.assertEqual(local["赌徒"]["source"], "template")

    def test_merge_false_ignores_growth(self):
        self.patch_config(role_extract_merge="false")
        local = role_generate._load_local_roles()
        # merge=false → 只读模板库，不含 growth 角色
        for info in local.values():
            self.assertEqual(info["source"], "template")

    def test_growth_roles_loaded_with_source(self):
        # 回归用例：修复 list.get 误用后，_load_local_roles 应从 growth_record
        # 加载成长角色（source='growth'），不再因 AttributeError 被静默跳过。
        self.write_growth_record([{"role_id": "成长角色A", "total_sessions": 3}])
        local = role_generate._load_local_roles()
        self.assertIn("成长角色A", local)
        self.assertEqual(local["成长角色A"]["source"], "growth")


class PickLocalRolesTests(IsolatedGrowthTest):

    def test_returns_up_to_count(self):
        picked = role_generate._pick_local_roles("问题", 3)
        self.assertLessEqual(len(picked), 3)

    def test_qtype_filter_prefers_matching(self):
        # 职场问题优先取 QUESTION_TYPE_MAP["职场"] 中存在于模板的
        picked = role_generate._pick_local_roles("跳槽", 4, qtype="职场")
        self.assertGreater(len(picked), 0)


class InjectGrowthHintTests(IsolatedGrowthTest):

    def test_no_record_returns_none(self):
        self.assertIsNone(role_generate._inject_growth_hint("不存在的角色XYZ"))

    def test_with_history_injects_stance(self):
        # 回归用例（原锁定用例 test_with_history_currently_inert）：
        # 修复 list.get 误用后，_inject_growth_hint 直接遍历 data，命中 growth_record
        # 同名角色时返回其最新立场。
        self.write_growth_record([{
            "role_id": "有历史的角色",
            "stance_history": [{"stance": "上次立场", "session_id": "x"}],
        }])
        self.assertEqual(role_generate._inject_growth_hint("有历史的角色"), "上次立场")


if __name__ == "__main__":
    unittest.main(verbosity=2)
