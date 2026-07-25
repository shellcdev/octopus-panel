# -*- coding: utf-8 -*-
"""测试共享脚手架。

职责：
  1. 把同级的 ``../scripts`` 目录加入 ``sys.path``，让测试能直接 import 被测模块；
  2. 提供 :class:`IsolatedGrowthTest` 基类，把 ``growth_api`` 的文件 I/O 隔离到临时目录，
     避免污染真实的 growth_record.json / 备份目录；
  3. 在每个用例前后重置 ``growth_api`` 的模块级可变全局（CONFIG_CACHE /
     session override / last_backup_time），杜绝用例间相互污染；
  4. 暴露真实 skill 路径常量，供"只读集成测试"使用。
"""
import os
import sys
import shutil
import tempfile
import unittest

# ─── sys.path 注入：让 ``import growth_api`` 等直接生效 ──────────────────────
_THIS = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.normpath(os.path.join(_THIS, '..'))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

SKILL_ROOT = os.path.normpath(os.path.join(_THIS, '..', '..'))
SCRIPTS_DIR = _SCRIPTS
REFERENCES_DIR = os.path.join(SKILL_ROOT, 'references')
ROLE_TEMPLATES = os.path.join(REFERENCES_DIR, 'role-templates.md')

# 被测模块（import 触发模块顶层代码执行，需在 sys.path 就绪后导入）
import growth_api          # noqa: E402
import discussion_archive  # noqa: E402
import role_generate       # noqa: E402


def _make_isolated_config(tmp_growth, tmp_archive):
    """构造一份指向临时目录的最小 config，覆盖 growth_api 全部会被读取的键。"""
    return {
        'workspace_root': os.path.dirname(tmp_growth),
        'growth_dir': tmp_growth,
        'archive_dir': tmp_archive,
        'stance_history_max_entries': '10',
        'stance_history_skip_sessions': '',
        'relationship_network_enabled': 'false',
        'relationship_network_mode': 'auto',
        'role_source_mode': 'generate',
        'role_extract_merge': 'true',
        'pure_generated_handling': 'ask',
        'topic_slug_length': '6',
        'archive_keyword_count': '5',
        'backup_keep_count': '30',
        'deep_mode_inject_count': '3',
    }


class IsolatedGrowthTest(unittest.TestCase):
    """把 growth_api 数据层隔离到临时目录的测试基类。

    子类直接写用例即可，无需关心配置/全局状态/清理。每个用例拿到一份
    独立的空 growth 目录，互不影响。
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix='octopus_test_')
        self.growth_dir = os.path.join(self._tmp, 'growth')
        self.archive_dir = os.path.join(self._tmp, 'archive')
        os.makedirs(self.growth_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

        # 注入隔离配置 + 重置全局可变状态
        self._orig_config = growth_api._CONFIG_CACHE
        self._orig_override = growth_api._session_relationship_override
        self._orig_last_backup = growth_api._last_backup_time
        self._orig_diversity = discussion_archive._diversity_history

        growth_api._CONFIG_CACHE = _make_isolated_config(self.growth_dir, self.archive_dir)
        growth_api._session_relationship_override = None
        growth_api._last_backup_time = None
        discussion_archive._diversity_history = []

    def tearDown(self):
        growth_api._CONFIG_CACHE = self._orig_config
        growth_api._session_relationship_override = self._orig_override
        growth_api._last_backup_time = self._orig_last_backup
        discussion_archive._diversity_history = self._orig_diversity
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ─── 便捷写数据 helper ──────────────────────────────────────────────
    def write_growth_record(self, roles):
        """直接落一份 growth_record.json 到隔离目录（绕过 _write 的 version 封装，供测试造数）。"""
        import json
        fp = growth_api._get_growth_filepath()
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump({'version': growth_api._get_current_schema_version(),
                       'updated_at': 'test', 'roles': roles}, f, ensure_ascii=False, indent=2)

    def patch_config(self, **overrides):
        """临时覆盖某些 config 键（在原隔离配置基础上叠加）。"""
        cfg = dict(growth_api._CONFIG_CACHE)
        cfg.update({k: str(v) for k, v in overrides.items()})
        growth_api._CONFIG_CACHE = cfg

    def read_growth_record(self):
        """读回当前 growth_record.json（dict 形式）。"""
        import json
        fp = growth_api._get_growth_filepath()
        if not os.path.isfile(fp):
            return {'version': 1, 'roles': []}
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)


def read_text(path):
    """读 UTF-8 文本，文件不存在返回 None。"""
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
