# -*- coding: utf-8 -*-
"""growth_api.py 单元测试（核心数据层）。

被测对象覆盖：
  - 纯/半纯函数：``_classify_topic`` / ``_influence_weight`` / ``_find_role``；
  - 配置与状态：``_get_config`` / ``is_relationship_enabled`` / session override；
  - 读写 I/O：``_read/_write_growth_record``（含损坏救援）、schema version；
  - 核心 API：``update_stance_history``（EXP/level/驱逐）、``update_relationship``
    （status 升级）、``check_achievements``、``_check_milestones``、
    ``update_auto_tags``、``upsert_role``；
  - spawn 注入：``get_spawn_inject`` light/deep/skip/关系；
  - 备份/迁移：``backup_all`` / ``restore_all`` / ``auto_backup_if_needed`` /
    ``migrate_schema``。

全部用例继承 :class:`IsolatedGrowthTest`，数据隔离到临时目录，绝不触碰真实
growth_record.json。``_is_local_role_name`` 读真实 role-templates.md（只读）。
"""
import datetime
import glob
import json
import os
import unittest

from _helpers import IsolatedGrowthTest  # noqa: F401
import growth_api


# ============================================================ 纯函数
class ClassifyTopicTests(IsolatedGrowthTest):
    """growth_api 的 8 类分类（注意不同于 discussion_archive 的 5 类）。"""

    def test_empty_returns_general(self):
        self.assertEqual(growth_api._classify_topic(""), "general")
        self.assertEqual(growth_api._classify_topic(None), "general")

    def test_financial(self):
        self.assertEqual(growth_api._classify_topic("买房投资理财"), "financial")

    def test_career(self):
        self.assertEqual(growth_api._classify_topic("辞职跳槽创业"), "career")

    def test_technical(self):
        self.assertEqual(growth_api._classify_topic("技术架构选型"), "technical")

    def test_legal(self):
        self.assertEqual(growth_api._classify_topic("版权合同诉讼"), "legal")

    def test_medical(self):
        self.assertEqual(growth_api._classify_topic("看病诊断手术"), "medical")

    def test_education_over_family(self):
        # "孩子升学" 同时含 family(孩子) 和 education(升学) → 教育优先
        self.assertEqual(growth_api._classify_topic("孩子升学择校"), "education")

    def test_family(self):
        self.assertEqual(growth_api._classify_topic("结婚离婚育儿"), "family")

    def test_general_fallback(self):
        self.assertEqual(growth_api._classify_topic("随便聊聊天气"), "general")


class InfluenceWeightTests(IsolatedGrowthTest):

    def test_base_weight_no_signals(self):
        entry = {"topic": "无关话题", "stance": "中立", "score": None, "session_id": ""}
        w = growth_api._influence_weight(entry, current_category="")
        # base 0.3 + rel 0.3*0.35 = 0.405 → round(,2) 受浮点表示影响得 0.4
        self.assertAlmostEqual(w, 0.4, places=2)

    def test_relevance_boost(self):
        entry = {"topic": "跳槽", "stance": "走", "score": None, "session_id": ""}
        w = growth_api._influence_weight(entry, current_category="career")
        # 0.3 + 1.0*0.35 = 0.65
        self.assertAlmostEqual(w, 0.65, places=2)

    def test_score_boost(self):
        entry = {"topic": "跳槽", "stance": "走", "score": 100, "session_id": ""}
        w = growth_api._influence_weight(entry, current_category="career")
        # 0.3 + 0.35 + 1.0*0.2 = 0.85
        self.assertAlmostEqual(w, 0.85, places=2)

    def test_hedged_penalty(self):
        entry = {"topic": "跳槽", "stance": "走，但要考虑条件", "score": 100, "session_id": ""}
        w = growth_api._influence_weight(entry, current_category="career")
        # 0.85 * 0.8 = 0.68
        self.assertAlmostEqual(w, 0.68, places=2)

    def test_recency_bonus_today(self):
        today = datetime.datetime.now().strftime("%Y%m%d")
        entry = {"topic": "跳槽", "stance": "走", "score": 100, "session_id": today + "-x"}
        w = growth_api._influence_weight(entry, current_category="career")
        # 0.85 + 0.15 = 1.0 → 封顶 1.0
        self.assertAlmostEqual(w, 1.0, places=2)

    def test_capped_at_one(self):
        today = datetime.datetime.now().strftime("%Y%m%d")
        entry = {"topic": "跳槽", "stance": "走", "score": 100, "session_id": today + "-x"}
        w = growth_api._influence_weight(entry, current_category="career")
        self.assertLessEqual(w, 1.0)

    def test_calc_influence_weight_delegates(self):
        entry = {"topic": "x", "stance": "y", "score": None, "session_id": ""}
        self.assertEqual(growth_api.calc_influence_weight(entry),
                         growth_api._influence_weight(entry))


class FindRoleTests(IsolatedGrowthTest):

    def test_found(self):
        roles = [{"role_id": "A"}, {"role_id": "B"}]
        idx, role = growth_api._find_role(roles, "B")
        self.assertEqual(idx, 1)
        self.assertEqual(role["role_id"], "B")

    def test_not_found(self):
        idx, role = growth_api._find_role([{"role_id": "A"}], "Z")
        self.assertIsNone(idx)
        self.assertIsNone(role)


# ============================================================ 配置/状态
class ConfigTests(IsolatedGrowthTest):

    def test_get_config_from_isolated(self):
        self.assertEqual(growth_api._get_config("growth_dir"), self.growth_dir)
        self.assertEqual(growth_api._get_config("stance_history_max_entries"), "10")

    def test_get_config_default(self):
        self.assertEqual(growth_api._get_config("not_exist_key", "fallback"), "fallback")

    def test_patch_config_override(self):
        self.patch_config(stance_history_max_entries="3")
        self.assertEqual(growth_api._get_config("stance_history_max_entries"), "3")


class RelationshipEnabledTests(IsolatedGrowthTest):

    def test_never_mode(self):
        self.patch_config(relationship_network_mode="never")
        self.assertFalse(growth_api.is_relationship_enabled())

    def test_always_mode(self):
        self.patch_config(relationship_network_mode="always")
        self.assertTrue(growth_api.is_relationship_enabled())

    def test_auto_disabled_by_default(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        self.assertFalse(growth_api.is_relationship_enabled())

    def test_auto_enabled_flag(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="true")
        self.assertTrue(growth_api.is_relationship_enabled())

    def test_session_override_false(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="true")
        growth_api.set_session_override(False)
        self.assertFalse(growth_api.is_relationship_enabled())
        growth_api.clear_session_override()
        self.assertTrue(growth_api.is_relationship_enabled())

    def test_session_override_true(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        growth_api.set_session_override(True)
        self.assertTrue(growth_api.is_relationship_enabled())
        growth_api.clear_session_override()


class IsGuidanceNeededTests(IsolatedGrowthTest):

    def test_no_roles_no_guidance(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        self.assertFalse(growth_api._is_guidance_needed())

    def test_with_relationship_data(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="false")
        # 造一个有 relationship_lines 的角色
        self.write_growth_record([{"role_id": "A", "relationship_lines": [{"target_id": "B", "co_sessions": 1}]}])
        self.assertTrue(growth_api._is_guidance_needed())

    def test_enabled_true_no_guidance(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="true")
        self.write_growth_record([{"role_id": "A", "relationship_lines": [{"target_id": "B"}]}])
        self.assertFalse(growth_api._is_guidance_needed())


# ============================================================ 读写 I/O
class ReadWriteRecordTests(IsolatedGrowthTest):

    def test_read_nonexistent_returns_empty(self):
        self.assertEqual(growth_api._read_growth_record(), [])

    def test_write_then_read(self):
        growth_api._write_growth_record([{"role_id": "A", "level": 5}])
        roles = growth_api._read_growth_record()
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]["role_id"], "A")

    def test_write_sets_version_and_timestamp(self):
        growth_api._write_growth_record([])
        data = self.read_growth_record()
        self.assertIn("version", data)
        self.assertIn("updated_at", data)
        self.assertEqual(data["roles"], [])

    def test_write_atomic_no_tmp_leftover(self):
        growth_api._write_growth_record([{"role_id": "A"}])
        tmp = growth_api._get_growth_filepath() + ".tmp"
        self.assertFalse(os.path.isfile(tmp), "临时文件应已被 rename 清理")

    def test_corrupt_record_rescue(self):
        fp = growth_api._get_growth_filepath()
        with open(fp, "w", encoding="utf-8") as f:
            f.write("{invalid json,,,")
        result = growth_api._read_growth_record()
        self.assertEqual(result, [])
        # 应生成 .corrupt- 救援备份
        backups = glob.glob(fp + ".corrupt-*")
        self.assertEqual(len(backups), 1, "损坏文件应被救援备份")

    def test_read_dict_with_version_wrapper(self):
        # 旧格式 dict-with-version 也能读出 roles
        self.write_growth_record([{"role_id": "A"}])
        roles = growth_api._read_growth_record()
        self.assertEqual(len(roles), 1)


class SchemaVersionTests(IsolatedGrowthTest):

    def test_default_version_one(self):
        self.assertEqual(growth_api._get_current_schema_version(), 1)

    def test_set_then_get(self):
        growth_api._set_schema_version(2)
        self.assertEqual(growth_api._get_current_schema_version(), 2)


# ============================================================ 核心 API
class GetRoleGrowthTests(IsolatedGrowthTest):

    def test_missing_role_returns_none(self):
        self.assertIsNone(growth_api.get_role_growth("Nobody"))

    def test_found_returns_role(self):
        self.write_growth_record([{"role_id": "A", "level": 3}])
        role = growth_api.get_role_growth("A")
        self.assertEqual(role["level"], 3)


class UpdateStanceHistoryTests(IsolatedGrowthTest):

    def test_creates_new_role(self):
        role = growth_api.update_stance_history("A", "20260101-x", "跳槽", "走", 80)
        self.assertEqual(role["role_id"], "A")
        self.assertEqual(role["total_sessions"], 1)
        self.assertEqual(role["exp"], 80)  # decay=1.0, int(80*1.0)
        self.assertEqual(role["level"], 1)  # 80//200+1
        self.assertEqual(len(role["stance_history"]), 1)

    def test_level_threshold(self):
        # score=200 → exp=200 → level=2
        role = growth_api.update_stance_history("A", "20260101-x", "q", "s", 200)
        self.assertEqual(role["level"], 2)

    def test_accumulate_sessions(self):
        growth_api.update_stance_history("A", "20260101-a", "q", "s", 100)
        role = growth_api.update_stance_history("A", "20260102-b", "q", "s", 100)
        self.assertEqual(role["total_sessions"], 2)
        # decay = max(0.6, 1.0-0.02) = 0.98, gained = int(100*0.98)=98, exp=100+98=198
        self.assertEqual(role["exp"], 198)
        self.assertEqual(len(role["stance_history"]), 2)

    def test_eviction_when_exceeding_max(self):
        self.patch_config(stance_history_max_entries="3")
        for i in range(5):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 50)
        role = growth_api.get_role_growth("A")
        self.assertEqual(len(role["stance_history"]), 3)
        # 保留最后 3 条（session_id 2,3,4）
        ids = [s["session_id"] for s in role["stance_history"]]
        self.assertIn("20260102-x", ids)
        self.assertIn("20260104-x", ids)
        self.assertNotIn("20260100-x", ids)

    def test_score_none_no_exp_change(self):
        role = growth_api.update_stance_history("A", "20260101-x", "q", "s", None)
        self.assertEqual(role["exp"], 0)
        self.assertEqual(role["level"], 1)


class UpdateRelationshipTests(IsolatedGrowthTest):

    def test_never_mode_skipped(self):
        self.patch_config(relationship_network_mode="never")
        self.assertFalse(growth_api.update_relationship("A", "B"))

    def test_new_relationship(self):
        self.patch_config(relationship_network_mode="auto", relationship_network_enabled="true")
        growth_api.update_relationship("A", "B")
        role = growth_api.get_role_growth("A")
        self.assertEqual(len(role["relationship_lines"]), 1)
        self.assertEqual(role["relationship_lines"][0]["co_sessions"], 1)
        self.assertEqual(role["relationship_lines"][0]["status"], "一面之缘")

    def test_status_upgrades_with_sessions(self):
        self.patch_config(relationship_network_mode="always")
        for _ in range(5):
            growth_api.update_relationship("A", "B")
        role = growth_api.get_role_growth("A")
        rel = role["relationship_lines"][0]
        self.assertEqual(rel["co_sessions"], 5)
        self.assertEqual(rel["status"], "老对手/deep")

    def test_two_to_acquaintance(self):
        self.patch_config(relationship_network_mode="always")
        growth_api.update_relationship("A", "B")
        growth_api.update_relationship("A", "B")
        rel = growth_api.get_role_growth("A")["relationship_lines"][0]
        self.assertEqual(rel["status"], "同场熟人")

    def test_three_to_old_rival(self):
        self.patch_config(relationship_network_mode="always")
        for _ in range(3):
            growth_api.update_relationship("A", "B")
        rel = growth_api.get_role_growth("A")["relationship_lines"][0]
        self.assertEqual(rel["status"], "老对手")


class CheckAchievementsTests(IsolatedGrowthTest):

    def test_changed_the_wind(self):
        # 预置一个角色
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        new = growth_api.check_achievements("A", {"consensus_jump": 25, "session_id": "20260101-x"})
        self.assertIn("CHANGED_THE_WIND", new)

    def test_three_session_veteran(self):
        for i in range(3):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 50)
        new = growth_api.check_achievements("A", {"session_id": "20260102-x"})
        self.assertIn("THREE_SESSION_VETERAN", new)

    def test_ten_session_veteran(self):
        for i in range(10):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 50)
        new = growth_api.check_achievements("A", {"session_id": "20260109-x"})
        self.assertIn("TEN_SESSION_VETERAN", new)

    def test_not_re_unlocked(self):
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        growth_api.check_achievements("A", {"consensus_jump": 25, "session_id": "x"})
        # 第二次同条件不应重复解锁
        new = growth_api.check_achievements("A", {"consensus_jump": 25, "session_id": "x"})
        self.assertNotIn("CHANGED_THE_WIND", new)

    def test_first_stance_shift(self):
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        new = growth_api.check_achievements("A", {"stance_shifted": True, "session_id": "x"})
        self.assertIn("FIRST_STANCE_SHIFT", new)

    def test_highest_score(self):
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        growth_api.update_stance_history("A", "20260102-x", "q", "s", 50)
        new = growth_api.check_achievements("A", {"session_score": 90, "session_id": "x"})
        self.assertIn("HIGHEST_SCORE", new)

    def test_missing_role_returns_empty(self):
        self.assertEqual(growth_api.check_achievements("Nobody", {}), [])

    def test_career_events_recorded(self):
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        growth_api.check_achievements("A", {"consensus_jump": 25, "session_id": "x"})
        role = growth_api.get_role_growth("A")
        self.assertTrue(any(e["event"] == "CHANGED_THE_WIND" for e in role["career_events"]))


class CheckMilestonesTests(IsolatedGrowthTest):

    def test_five_session_milestone(self):
        for i in range(5):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 50)
        ms = growth_api._check_milestones("A", "20260104-x")
        ids = [m["event"] for m in ms]
        self.assertIn("FIVE_SESSION_MILESTONE", ids)

    def test_milestone_not_re_added(self):
        for i in range(5):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 50)
        growth_api._check_milestones("A", "x")
        ms = growth_api._check_milestones("A", "x")
        # 第二次不应重复加
        self.assertNotIn("FIVE_SESSION_MILESTONE", [m["event"] for m in ms])

    def test_missing_role_returns_empty(self):
        self.assertEqual(growth_api._check_milestones("Nobody"), [])


class UpdateAutoTagsTests(IsolatedGrowthTest):

    def test_missing_role_returns_empty(self):
        self.assertEqual(growth_api.update_auto_tags("Nobody"), [])

    def test_duwang_candidate(self):
        # 3 场 score>=80 → 怼王候选
        for i in range(3):
            growth_api.update_stance_history("A", "2026010%d-x" % i, "q", "s", 85)
        growth_api.update_auto_tags("A")
        role = growth_api.get_role_growth("A")
        self.assertTrue(any("怼王候选" in t for t in role["auto_tags"]))

    def test_low_confidence_filtered(self):
        # 1 场低分，不足以触发任何 >=60% 的标签
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 30)
        growth_api.update_auto_tags("A")
        role = growth_api.get_role_growth("A")
        # total_sessions=1 不满足多数标签的 N>=3 门槛
        for t in role["auto_tags"]:
            # 标签格式 "名(XX%)"，XX 应 >= 60
            self.assertGreaterEqual(int(t.split("(")[1].split("%")[0]), 60)


class UpsertRoleTests(IsolatedGrowthTest):

    def test_add_new_role(self):
        ok = growth_api.upsert_role({"role_id": "A", "level": 1})
        self.assertTrue(ok)
        self.assertEqual(growth_api.get_role_growth("A")["level"], 1)

    def test_existing_not_overwritten(self):
        growth_api.upsert_role({"role_id": "A", "level": 5})
        ok = growth_api.upsert_role({"role_id": "A", "level": 99})
        self.assertFalse(ok)
        # 原值不被覆盖
        self.assertEqual(growth_api.get_role_growth("A")["level"], 5)


# ============================================================ spawn 注入
class SpawnInjectTests(IsolatedGrowthTest):

    def test_round_ge2_returns_empty(self):
        growth_api.update_stance_history("A", "20260101-x", "q", "s", 50)
        self.assertEqual(growth_api.get_spawn_inject("A", round_n=2), "")

    def test_missing_role_returns_empty(self):
        self.assertEqual(growth_api.get_spawn_inject("Nobody", round_n=1), "")

    def test_no_history_returns_empty(self):
        growth_api.upsert_role({"role_id": "A"})
        self.assertEqual(growth_api.get_spawn_inject("A", round_n=1), "")

    def test_light_inject_one_entry(self):
        growth_api.update_stance_history("A", "20260101-x", "跳槽", "走", 80)
        out = growth_api.get_spawn_inject("A", current_topic="换工作", round_n=1, mode="light")
        self.assertIn("你之前说过", out)
        self.assertIn("跳槽", out)

    def test_deep_inject_multiple(self):
        for i, t in enumerate(["跳槽", "加薪", "面试"]):
            growth_api.update_stance_history("A", "2026010%d-x" % i, t, "走", 80)
        out = growth_api.get_spawn_inject("A", current_topic="换工作", round_n=1, mode="deep")
        self.assertIn("上次", out)
        self.assertIn("第", out)

    def test_skip_sessions_filtered(self):
        growth_api.update_stance_history("A", "20260101-x", "跳槽", "走", 80)
        growth_api.update_stance_history("A", "20260102-y", "加薪", "留", 80)
        self.patch_config(stance_history_skip_sessions="20260101-x")
        out = growth_api.get_spawn_inject("A", round_n=1)
        # 第一条被跳过，注入的应是加薪
        self.assertIn("加薪", out)
        self.assertIn("跳过", out)


class CompactHistoryTests(IsolatedGrowthTest):

    def test_missing_role_empty(self):
        self.assertEqual(growth_api.get_compact_history("Nobody"), "")

    def test_no_history_empty(self):
        growth_api.upsert_role({"role_id": "A"})
        self.assertEqual(growth_api.get_compact_history("A"), "")

    def test_history_formatted(self):
        for t in ["跳槽", "加薪"]:
            growth_api.update_stance_history("A", "20260101-x", t, "走", 50)
        out = growth_api.get_compact_history("A")
        self.assertIn("履历", out)
        self.assertIn("本次", out)

    def test_compact_display(self):
        growth_api.update_stance_history("A", "20260101-x", "跳槽", "走", 50)
        out = growth_api.get_compact_display("A")
        self.assertIn("立场履历", out)


# ============================================================ 备份/迁移
class BackupTests(IsolatedGrowthTest):

    def test_backup_creates_file(self):
        growth_api.upsert_role({"role_id": "A"})
        path = growth_api.backup_all()
        self.assertTrue(os.path.isfile(path))
        self.assertIn("growth_backups", path)

    def test_backup_preserves_roles(self):
        growth_api.upsert_role({"role_id": "A"})
        growth_api.upsert_role({"role_id": "B"})
        path = growth_api.backup_all()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["roles"]), 2)

    def test_evict_old_backups(self):
        backup_dir = os.path.join(self.growth_dir, "growth_backups")
        os.makedirs(backup_dir, exist_ok=True)
        # 造 5 个备份，max_keep=2
        for i in range(5):
            with open(os.path.join(backup_dir, "2020010%d-0000.json" % i), "w") as f:
                f.write("{}")
        growth_api._evict_old_backups(backup_dir, max_keep=2)
        remaining = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
        self.assertEqual(len(remaining), 2)
        # 保留最新的两个（编号 3、4）
        self.assertIn("20200103-0000.json", remaining)
        self.assertIn("20200104-0000.json", remaining)


class RestoreTests(IsolatedGrowthTest):

    def test_restore_from_backup(self):
        # 直接 upsert 一个带完整 level/exp 的角色作为快照（不经过
        # update_stance_history —— 它会按 EXP 重算 level，覆盖我们的设定）
        growth_api.upsert_role({"role_id": "A", "level": 5, "exp": 1000, "total_sessions": 5})
        roles_snapshot = growth_api._read_growth_record()

        # 手动把快照写到独立路径（不在 growth_backups/ 下），避开 restore_all
        # 内部救援备份与原备份在同一分钟生成、文件名相同而互相覆盖的问题
        backup_path = os.path.join(self._tmp, "manual_backup.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "roles": roles_snapshot}, f, ensure_ascii=False)

        # 清空当前数据
        growth_api._write_growth_record([])

        count = growth_api.restore_all(backup_path)
        self.assertEqual(count, 1)
        role = growth_api.get_role_growth("A")
        self.assertEqual(role["level"], 5)

    def test_restore_invalid_file_returns_none(self):
        self.assertIsNone(growth_api.restore_all("/no/such/file.json"))

    def test_restore_empty_roles(self):
        # 写一个 roles 为空的备份文件
        fp = os.path.join(self._tmp, "empty_backup.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "roles": []}, f)
        self.assertEqual(growth_api.restore_all(fp), 0)


class AutoBackupTests(IsolatedGrowthTest):

    def test_first_call_triggers_backup(self):
        growth_api.upsert_role({"role_id": "A"})
        path = growth_api.auto_backup_if_needed()
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isfile(path))

    def test_second_call_within_window_skipped(self):
        growth_api.upsert_role({"role_id": "A"})
        growth_api.auto_backup_if_needed()
        # 紧接着第二次（_last_backup_time 刚被设为 now）
        path2 = growth_api.auto_backup_if_needed()
        self.assertIsNone(path2)


class MigrateSchemaTests(IsolatedGrowthTest):

    def test_no_file_returns_unchanged(self):
        cur, tgt, count = growth_api.migrate_schema(target_version=2)
        self.assertEqual(count, 0)

    def test_migrate_v1_to_v2_adds_fields(self):
        # 写一个 v1 的角色，缺 career_events/achievements 等字段
        self.write_growth_record([{
            "role_id": "A", "version": 1, "total_sessions": 2,
            "stance_history": [{"session_id": "20260101-x", "topic": "跳槽", "stance": "走", "score": 50}],
        }])
        cur, tgt, count = growth_api.migrate_schema(target_version=2)
        self.assertEqual(tgt, 2)
        self.assertEqual(count, 1)
        role = growth_api.get_role_growth("A")
        self.assertIn("career_events", role)
        self.assertIn("achievements", role)
        self.assertIn("auto_tags", role)
        self.assertIn("manual_tags", role)
        self.assertEqual(role["version"], 2)
        # stance_history 应被补上 influence_weight
        self.assertIn("influence_weight", role["stance_history"][0])

    def test_migrate_idempotent(self):
        # 先把 schema_version 设为 2，再写入，确保文件内 version=2（否则
        # write 默认取 schema_version=1，会让迁移又跑一轮）
        growth_api._set_schema_version(2)
        self.write_growth_record([{"role_id": "A", "version": 2, "career_events": [], "achievements": [],
                                   "auto_tags": [], "manual_tags": [], "stance_history": []}])
        cur, tgt, count = growth_api.migrate_schema(target_version=2)
        self.assertEqual(count, 0)


# ============================================================ _is_local_role_name
class IsLocalRoleNameTests(IsolatedGrowthTest):
    """读真实 role-templates.md（只读）+ 隔离的空 growth_record。"""

    def test_unknown_returns_false(self):
        self.assertFalse(growth_api._is_local_role_name("Unknown"))

    def test_empty_returns_false(self):
        self.assertFalse(growth_api._is_local_role_name(""))

    def test_real_template_role_true(self):
        # 真实模板含 "赌徒"
        self.assertTrue(growth_api._is_local_role_name("赌徒"))

    def test_nonexistent_false(self):
        self.assertFalse(growth_api._is_local_role_name("完全不存在的XYZ"))

    def test_growth_record_lookup_hits_custom_role(self):
        # 回归用例（原锁定用例 test_growth_record_lookup_currently_inert）：
        # 修复 list.get 误用后，_read_growth_record 返回 list，_is_local_role_name
        # 直接遍历 data，growth_record 里的自定义角色名应被命中。
        self.write_growth_record([{"role_id": "自定义角色", "total_sessions": 1}])
        self.assertTrue(growth_api._is_local_role_name("自定义角色"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
