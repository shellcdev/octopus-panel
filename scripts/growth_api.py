# -*- coding: utf-8 -*-
"""
growth_api.py - Role Growth System API (Phase 0)

Central interface for all growth_record read/write operations.
Other modules (discussion_archive.py, growth_render.py, etc.) MUST
go through this API instead of accessing growth_record directly.

Lifecycle:
  - Data is stored as a single JSON file: {growth_dir}/growth_record.json
  - Each discussion archive triggers update_stance_history() and update_relationship()
  - check_achievements() and update_auto_tags() run after each update
  - get_spawn_inject() is called by the spawning system to inject history context

Relationship network modes:
  auto    = collect always, show only when condition triggered (default)
  always  = collect always, show always
  never   = do not collect, do not show

Session override:
  Use set_session_override(False) for "this round, no relationships".
  Automatically cleared after discussion ends.
"""

import os
import re
import json
import codecs
import datetime
import shutil
from copy import deepcopy

# ─── Config (lazy-loaded from config.md) ───

_CONFIG_CACHE = None

def _load_config():
    """Parse config.md and return a dict of key-value pairs."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.md')
    cfg = {}
    try:
        with codecs.open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '|' in line and line.count('|') >= 3:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4 and parts[1] and parts[2] and parts[1] != '键':
                        # 配置表键/值单元格被反引号包裹（如 `workspace_root`），需剥除反引号
                        # 否则 key 带反引号导致跨键引用替换失败、默认值覆盖，换机器改 config 无效
                        key = parts[1].strip('`')
                        val = parts[2].strip('`')
                        # Resolve {CLAW_ROOT} env placeholder first
                        _claw_root = os.environ.get('CLAW_ROOT', '')
                        if '{CLAW_ROOT}' in val and _claw_root:
                            val = val.replace('{CLAW_ROOT}', _claw_root)
                        # Resolve {workspace_root} references
                        if '{workspace_root}' in val and 'workspace_root' in cfg:
                            val = val.replace('{workspace_root}', cfg['workspace_root'])
                        if '{octopus_dir}' in val and 'octopus_dir' in cfg:
                            val = val.replace('{octopus_dir}', cfg['octopus_dir'])
                        cfg[key] = val
    except FileNotFoundError:
        pass

    # Apply defaults for keys that may not be in config.md yet
    defaults = {
        'workspace_root': os.path.expanduser('~/.qclaw/workspace'),
        'growth_dir': os.path.join(os.path.expanduser('~/.qclaw/workspace'), 'memory', 'octopus', 'growth'),
        'archive_dir': os.path.join(os.path.expanduser('~/.qclaw/workspace'), 'memory', 'octopus', 'archive'),
        'stance_history_max_entries': '10',
        'stance_history_skip_sessions': '',
        'relationship_network_enabled': 'false',
        'relationship_network_mode': 'auto',
    }
    for k, v in defaults.items():
        if k not in cfg or not cfg[k]:
            cfg[k] = v

    _CONFIG_CACHE = cfg
    return cfg


def _get_config(key, default=''):
    cfg = _load_config()
    return cfg.get(key, default)


def _get_growth_dir():
    return _get_config('growth_dir')


def _is_local_role_name(role_name):
    """判断角色名是否属于本地库（role-templates.md 有模板 或 growth_record.json 有成长记录）。
    统一实现，供 generate_roles / archive_discussion 共用，消除重复解析。"""
    if not role_name or role_name == 'Unknown':
        return False
    # 1) 成长记录已有该角色
    try:
        data = _read_growth_record()
        for r in data.get('roles', []):
            if r.get('role_id') == role_name:
                return True
    except Exception:
        pass
    # 2) 模板库有该角色全名（括号前部分）
    tmpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'references', 'role-templates.md')
    try:
        with codecs.open(tmpl_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        for m in re.finditer(r'^###\s+\S+\s+([^\n（(]+)', txt, re.M):
            if m.group(1).strip() == role_name:
                return True
    except FileNotFoundError:
        pass
    return False


def _get_growth_filepath():
    return os.path.join(_get_growth_dir(), 'growth_record.json')


def _get_schema_version_filepath():
    return os.path.join(_get_growth_dir(), 'schema_version.txt')


# ─── Data I/O ───

def _ensure_dir():
    """Create growth data directory if it doesn't exist."""
    d = _get_growth_dir()
    os.makedirs(d, exist_ok=True)


def _read_growth_record():
    """Read full growth_record from disk. Returns list of role dicts."""
    fp = _get_growth_filepath()
    if not os.path.isfile(fp):
        return []
    try:
        with codecs.open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Support both list and dict-with-version wrapper
        if isinstance(data, dict):
            return data.get('roles', [])
        return data
    except (json.JSONDecodeError, ValueError):
        # 损坏救援：先保留现场再返回空，避免 _write 清空后无备份可恢复
        try:
            _bak = fp + '.corrupt-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            shutil.copy2(fp, _bak)
        except Exception:
            pass
        return []


def _write_growth_record(roles):
    """Write full growth_record to disk. Handles version and atomic write."""
    _ensure_dir()
    fp = _get_growth_filepath()
    data = {
        'version': _get_current_schema_version(),
        'updated_at': datetime.datetime.now().isoformat(),
        'roles': roles,
    }
    # Atomic write: write to tmp, then rename
    tmp_fp = fp + '.tmp'
    with codecs.open(tmp_fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.isfile(fp):
        os.remove(fp)
    os.rename(tmp_fp, fp)


def _get_current_schema_version():
    """Read current schema version from schema_version.txt, default 1."""
    fp = _get_schema_version_filepath()
    if os.path.isfile(fp):
        with codecs.open(fp, 'r', encoding='utf-8') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 1
    return 1


def _set_schema_version(version):
    """Write schema version to file."""
    _ensure_dir()
    fp = _get_schema_version_filepath()
    with codecs.open(fp, 'w', encoding='utf-8') as f:
        f.write(str(version))


def _find_role(roles, role_id):
    """Find role by ID in the roles list. Returns (index, dict) or (None, None)."""
    for i, r in enumerate(roles):
        if r.get('role_id') == role_id:
            return i, r
    return None, None


# ─── Session-level override (temporary per-discussion) ───

_session_relationship_override = None
# None = follow global config
# False = "this round, no relationships"
# True  = "this round, restore relationships"


def set_session_override(value):
    """Set temporary relationship override for current discussion."""
    global _session_relationship_override
    _session_relationship_override = value


def clear_session_override():
    """Clear session override (call after discussion ends)."""
    global _session_relationship_override
    _session_relationship_override = None


# ─── Core Public API (7 functions) ───

def get_role_growth(role_id):
    """
    Get growth_record for a specific role.
    Returns dict (with defaults for missing fields) or None if role not found.
    """
    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return None
    return role


def update_stance_history(role_id, session_id, topic, stance, score):
    """
    Append a stance history entry. Automatically evicts oldest entries
    when exceeding stance_history_max_entries.
    """
    roles = _read_growth_record()
    idx, role = _find_role(roles, role_id)

    if role is None:
        # First appearance: create new growth_record
        role = {
            'version': _get_current_schema_version(),
            'role_id': role_id,
            'total_sessions': 0,
            'level': 1,
            'exp': 0,
            'stance_history': [],
            'career_events': [],
            'achievements': [],
            'relationship_lines': [],
            'auto_tags': [],
            'manual_tags': [],
        }
        roles.append(role)
        idx = len(roles) - 1

    # Increment session count
    role['total_sessions'] = role.get('total_sessions', 0) + 1

    # Append stance entry
    entry = {
        'session_id': session_id,
        'topic': topic,
        'stance': stance,
        'score': score,
        'influence_weight': None,  # calculated later by calc_influence_weight()
    }
    stance_history = role.get('stance_history', [])
    stance_history.append(entry)

    # Evict old entries
    max_entries = int(_get_config('stance_history_max_entries', '10'))
    if len(stance_history) > max_entries:
        stance_history = stance_history[-max_entries:]

    role['stance_history'] = stance_history

    # ─── EXP calculation & level update ───
    if score is not None:
        # Decay coefficient: max(0.6, 1.0 - (total_sessions - 1) × 0.02)
        decay = max(0.6, 1.0 - (role['total_sessions'] - 1) * 0.02)
        # EXP gained = score × decay (character contribution estimated from score itself)
        exp_gained = int(score * decay)
        role['exp'] = role.get('exp', 0) + exp_gained
        # Level: floor(exp / 200) + 1
        role['level'] = role['exp'] // 200 + 1

    _write_growth_record(roles)
    return role


def update_relationship(role_id, co_role_id, relation_type='neutral'):
    """
    Update relationship line between two roles.
    - Increments co_sessions count
    - Sets relation_type on first encounter
    - Updates status based on co_sessions count
    - If relationship_network_mode is 'never', skips entirely (no collection)

    Returns True if updated, False if skipped (never mode).
    """
    mode = _get_config('relationship_network_mode', 'auto')
    if mode == 'never':
        return False

    roles = _read_growth_record()
    idx, role = _find_role(roles, role_id)

    # Ensure role exists in growth_record
    if role is None:
        role = {
            'version': _get_current_schema_version(),
            'role_id': role_id,
            'total_sessions': 0,
            'level': 1,
            'exp': 0,
            'stance_history': [],
            'career_events': [],
            'achievements': [],
            'relationship_lines': [],
            'auto_tags': [],
            'manual_tags': [],
        }
        roles.append(role)
        idx = len(roles) - 1

    rel_lines = role.get('relationship_lines', [])
    found = False
    for rel in rel_lines:
        if rel.get('target_id') == co_role_id:
            rel['co_sessions'] = rel.get('co_sessions', 0) + 1
            # Upgrade status based on co_sessions count
            cs = rel['co_sessions']
            if cs >= 5:
                rel['status'] = '老对手/deep'
            elif cs >= 3:
                rel['status'] = '老对手'
            elif cs >= 2:
                rel['status'] = '同场熟人'
            else:
                rel['status'] = '一面之缘'
            found = True
            break

    if not found:
        rel_lines.append({
            'target_id': co_role_id,
            'co_sessions': 1,
            'relation_type': relation_type,
            'status': '一面之缘',
        })

    role['relationship_lines'] = rel_lines
    _write_growth_record(roles)
    return True


def check_achievements(role_id, session_context=None):
    """
    Check and unlock new achievements for a role.
    session_context: dict with optional keys (conflict_density, evolution_efficiency,
                     convergence_quality, consensus_jump, session_id)
    Returns list of newly unlocked achievement IDs.
    """
    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return []

    existing = {a['id'] for a in role.get('achievements', [])}
    new_ones = []
    ctx = session_context or {}

    # CHANGED_THE_WIND: speech caused consensus jump >= 20%
    if 'CHANGED_THE_WIND' not in existing:
        if ctx.get('consensus_jump', 0) >= 20:
            new_ones.append({
                'id': 'CHANGED_THE_WIND',
                'name': '改变过风向',
                'description': '发言后共识拐点≥20%',
                'unlock_at': ctx.get('session_id', ''),
            })

    # THREE_SESSION_VETERAN: total_sessions >= 3
    if 'THREE_SESSION_VETERAN' not in existing:
        if role.get('total_sessions', 0) >= 3:
            new_ones.append({
                'id': 'THREE_SESSION_VETERAN',
                'name': '三朝元老',
                'description': '累计出场≥3场',
                'unlock_at': ctx.get('session_id', ''),
            })

    # TEN_SESSION_VETERAN: total_sessions >= 10
    if 'TEN_SESSION_VETERAN' not in existing:
        if role.get('total_sessions', 0) >= 10:
            new_ones.append({
                'id': 'TEN_SESSION_VETERAN',
                'name': '十朝元老',
                'description': '累计出场≥10场',
                'unlock_at': ctx.get('session_id', ''),
            })

    # FIRST_STANCE_SHIFT: first time stance changed during session
    if 'FIRST_STANCE_SHIFT' not in existing:
        if ctx.get('stance_shifted'):
            new_ones.append({
                'id': 'FIRST_STANCE_SHIFT',
                'name': '首次立场变化',
                'description': '在一场讨论中改变了立场',
                'unlock_at': ctx.get('session_id', ''),
            })

    # HIGHEST_SCORE: session score exceeds previous highest
    if 'HIGHEST_SCORE' not in existing:
        session_score = ctx.get('session_score')
        if session_score:
            prev_scores = [s.get('score', 0) or 0 for s in role.get('stance_history', [])[:-1]]
            prev_highest = max(prev_scores) if prev_scores else 0
            if session_score > prev_highest:
                new_ones.append({
                    'id': 'HIGHEST_SCORE',
                    'name': '生涯最高分',
                    'description': '单场评分达 {} 分，刷新个人纪录'.format(session_score),
                    'unlock_at': ctx.get('session_id', ''),
                })

    # LOWEST_SCORE: session score below previous lowest
    if 'LOWEST_SCORE' not in existing:
        session_score = ctx.get('session_score')
        if session_score:
            prev_scores = [s.get('score', 0) or 0 for s in role.get('stance_history', [])[:-1]]
            prev_lowest = min(prev_scores) if prev_scores else 100
            if session_score < prev_lowest:
                new_ones.append({
                    'id': 'LOWEST_SCORE',
                    'name': '生涯最低分',
                    'description': '单场评分仅 {} 分，低于预期'.format(session_score),
                    'unlock_at': ctx.get('session_id', ''),
                })

    # FIRST_CONSENSUS: first simultaneous [让] with another role
    if 'FIRST_CONSENSUS' not in existing:
        if ctx.get('mutual_rang'):
            new_ones.append({
                'id': 'FIRST_CONSENSUS',
                'name': '首次默契',
                'description': '首次与另一角色同时[让]，达成共识',
                'unlock_at': ctx.get('session_id', ''),
            })

    if new_ones:
        role['achievements'] = role.get('achievements', []) + new_ones
        role['career_events'] = role.get('career_events', []) + [
            {
                'event': a['id'],
                'description': '解锁成就：' + a['name'],
                'occurred_at': a['unlock_at'],
            }
            for a in new_ones
        ]
        _write_growth_record(roles)

    return [a['id'] for a in new_ones]


def _check_milestones(role_id, session_id=''):
    """
    Check for career milestone events (session count milestones).
    Called separately from check_achievements, after stance history update.

    Returns list of new milestone event dicts.
    """
    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return []

    total = role.get('total_sessions', 0)
    existing_events = {e['event'] for e in role.get('career_events', [])}
    milestones = []

    milestones_config = [
        (5, 'FIVE_SESSION_MILESTONE', '初出茅庐', '累计参与 5 场讨论'),
        (10, 'TEN_SESSION_MILESTONE', '讨论老手', '累计参与 10 场讨论'),
        (20, 'TWENTY_SESSION_MILESTONE', '资深辩手', '累计参与 20 场讨论'),
        (50, 'FIFTY_SESSION_MILESTONE', '八爪元老', '累计参与 50 场讨论'),
    ]

    for threshold, event_id, title, desc in milestones_config:
        if event_id not in existing_events and total >= threshold:
            milestones.append({
                'event': event_id,
                'description': '里程碑：{}——{}'.format(title, desc),
                'occurred_at': session_id,
            })

    if milestones:
        role['career_events'] = role.get('career_events', []) + milestones
        _write_growth_record(roles)

    return milestones


def update_auto_tags(role_id):
    """
    Recalculate all auto_tags for a role.
    Tags with confidence < 60% are stored but not included in the returned list.
    Returns list of auto_tags dicts with confidence.
    """
    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return []

    tags = []
    sh = role.get('stance_history', [])
    total_sessions = role.get('total_sessions', 0)
    rel_lines = role.get('relationship_lines', [])
    achievements = role.get('achievements', [])

    # DU_WANG: conflict density >= 80% for 3 consecutive sessions
    high_conflict_sessions = sum(
        1 for s in sh if s.get('score') and s['score'] >= 80
    )
    if total_sessions >= 3 and high_conflict_sessions >= 3:
        confidence = min(100, int(high_conflict_sessions / total_sessions * 100))
        tags.append({'tag': '怼王候选', 'confidence': confidence})

    # STANCE_STABLE: stance change rate < 30% (N >= 3 sessions)
    if len(sh) >= 3:
        stances = set(s.get('stance', '') for s in sh)
        if len(stances) <= 2:
            stability = max(0, 100 - (len(stances) - 1) * 35)
            tags.append({'tag': '立场稳定', 'confidence': stability})

    # SILENT_PARTNER: low contribution in 2+ consecutive sessions
    low_contrib = sum(1 for s in sh if s.get('score') and s['score'] < 40)
    if total_sessions >= 3 and low_contrib >= 2:
        confidence = min(100, int(low_contrib / total_sessions * 100))
        tags.append({'tag': '沉默搭档', 'confidence': confidence})

    # CONSENSUS_CATALYST: had CHANGED_THE_WIND achievement
    if any(a['id'] == 'CHANGED_THE_WIND' for a in achievements):
        tags.append({'tag': '共识催化剂', 'confidence': 85})

    # GREEN_IDEA_DRIVER: [绿] references across sessions
    green_ref_count = sum(1 for s in sh if '🟢' in s.get('topic', '') or '绿' in s.get('stance', ''))
    if green_ref_count >= 2:
        confidence = min(100, green_ref_count * 20)
        tags.append({'tag': '绿帽思路推动', 'confidence': confidence})

    # STANCE_SHIFT: in-session stance changes (from career_events)
    ce = role.get('career_events', [])
    shift_count = sum(1 for e in ce if e.get('event') == 'FIRST_STANCE_SHIFT')
    if shift_count >= 1:
        confidence = min(100, shift_count * 40)
        tags.append({'tag': '立场漂移', 'confidence': confidence})

    # RANG_MASTER: [让] count (estimated from stance text containing '条件'/'但')
    rang_count = sum(1 for s in sh if '条件' in s.get('stance', '') or '但' in s.get('stance', ''))
    if rang_count >= 2:
        confidence = min(100, rang_count * 15)
        tags.append({'tag': '让步大师', 'confidence': confidence})
    lv_count = sum(1 for s in sh if '🟢' in s.get('topic', '') or '绿' in s.get('stance', ''))
    if lv_count >= 1:
        confidence = min(100, 50 + lv_count * 15)
        tags.append({'tag': '绿帽骑士', 'confidence': confidence})

    # Filter low-confidence tags
    filtered = [t for t in tags if t['confidence'] >= 60]

    # Store as formatted strings
    role['auto_tags'] = ['{}({}%)'.format(t['tag'], t['confidence']) for t in filtered]
    _write_growth_record(roles)
    return filtered


def upsert_role(role_dict):
    """
    Add a new role to growth_record.
    If role_id already exists, do NOT overwrite — return False (caller handles skip).
    Returns True if added.
    """
    roles = _read_growth_record()
    _, existing = _find_role(roles, role_dict.get('role_id'))
    if existing is not None:
        return False
    roles.append(role_dict)
    _write_growth_record(roles)
    return True


# ─── Topic classification (shared with discussion_archive.py) ───

def _classify_topic(topic):
    """Classify a topic string into a category for relevance matching.

    类别集须与 role-templates.md 的角色分组对齐（8 组）：
    financial / career / family / technical / legal / medical / education / general
    """
    if not topic:
        return 'general'
    t = topic.lower()
    if any(w in t for w in ['买房', '租房', '投资', '理财', '股票', '基金', '房价']):
        return 'financial'
    if any(w in t for w in ['辞职', '创业', '工作', '跳槽', '加薪', '面试', '升职', '转行']):
        return 'career'
    if any(w in t for w in ['技术', '架构', '选型', '框架', '代码', '开发', '部署', '上线']):
        return 'technical'
    # 法务 / 知识产权（对齐 role-templates 法律风控组）
    if any(w in t for w in ['版权', '著作', '专利', '商标', '合同', '法律', '合规',
                            '诉讼', '法务', '侵权', '隐私', '数据合规', '维权的', '仲裁']):
        return 'legal'
    # 医疗 / 健康（对齐 role-templates 医疗决策组）
    if any(w in t for w in ['病', '医', '健康', '医保', '诊断', '治疗', '药', '疫苗',
                            '养生', '心理', '体检', '手术', '门诊']):
        return 'medical'
    # 教育 / 升学（对齐 role-templates 教育规划组）
    # 须放在 family 之前：'孩子升学/择校' 同时含 '孩子'(family) 与 '升学'(education)，
    # 教育意图更强，应优先归 education。
    if any(w in t for w in ['教育', '升学', '留学', '考试', '择校', '辅导', '培训',
                            '考研', '高考', '学区', '孩子学习']):
        return 'education'
    if any(w in t for w in ['结婚', '离婚', '出轨', '育儿', '孩子', '父母', '家庭', '生子', '感情']):
        return 'family'
    return 'general'


# Category relevance matrix: how relevant an old topic category is to the current one.
# Used by _influence_weight() as the primary "which stance is worth injecting" signal.
_CATEGORY_MATRIX = {
    'career':    {'career': 1.0, 'financial': 0.7, 'family': 0.3, 'technical': 0.3, 'legal': 0.3, 'medical': 0.2, 'education': 0.3, 'general': 0.5},
    'financial': {'financial': 1.0, 'career': 0.7, 'family': 0.3, 'technical': 0.3, 'legal': 0.5, 'medical': 0.2, 'education': 0.2, 'general': 0.5},
    'family':    {'family': 1.0, 'career': 0.3, 'financial': 0.3, 'general': 0.5, 'technical': 0.1, 'legal': 0.3, 'medical': 0.4, 'education': 0.5},
    'technical': {'technical': 1.0, 'career': 0.3, 'financial': 0.3, 'general': 0.5, 'family': 0.1, 'legal': 0.2, 'medical': 0.1, 'education': 0.2},
    'legal':     {'legal': 1.0, 'financial': 0.5, 'family': 0.3, 'career': 0.3, 'technical': 0.2, 'medical': 0.4, 'education': 0.3, 'general': 0.5},
    'medical':   {'medical': 1.0, 'family': 0.4, 'legal': 0.4, 'financial': 0.2, 'career': 0.2, 'technical': 0.1, 'education': 0.3, 'general': 0.5},
    'education': {'education': 1.0, 'family': 0.5, 'career': 0.3, 'legal': 0.3, 'financial': 0.2, 'technical': 0.2, 'medical': 0.3, 'general': 0.5},
    'general':   {'general': 0.5, 'career': 0.5, 'financial': 0.5, 'family': 0.5, 'technical': 0.5, 'legal': 0.5, 'medical': 0.5, 'education': 0.5},
}


def _influence_weight(entry, current_category=''):
    """
    SINGLE SOURCE OF TRUTH for stance-history influence weight (0.0-1.0).

    Used at spawn time to rank which past stances are most worth injecting into
    the current discussion. Higher = more worth surfacing.

    Formula (synthesized: F1 relevance skeleton + rescued stance-shift penalty):
        w  = 0.3                              # base
           + relevance * 0.35                 # topic relevance — PRIMARY ranking signal
           + (score / 100) * 0.2              # debate score contribution
           + recency_bonus                    # +0.15 if <=1d, +0.08 if <=7d
        w *= 0.8  if stance is hedged ('但'/'条件')   # stance-shift penalty (hedged ranks lower)
        w  = round(min(w, 1.0), 2)
    """
    weight = 0.3  # base
    # Topic relevance — primary signal deciding which stance is worth injecting
    entry_cat = _classify_topic(entry.get('topic', ''))
    rel_score = _CATEGORY_MATRIX.get(current_category, {}).get(entry_cat, 0.3)
    weight += rel_score * 0.35
    # Debate score contribution
    score = entry.get('score')
    if score:
        weight += (score / 100) * 0.2
    # Recency bonus (additive, capped)
    sid = entry.get('session_id', '')
    if sid:
        try:
            dt = datetime.datetime.strptime(sid[:8], '%Y%m%d')
            days_ago = (datetime.datetime.now() - dt).days
            if days_ago <= 1:
                weight += 0.15
            elif days_ago <= 7:
                weight += 0.08
        except ValueError:
            pass
    # Stance-shift penalty (rescued from the old divergent formula): hedged stances rank lower
    stance = entry.get('stance', '')
    if '条件' in stance or '但' in stance:
        weight *= 0.8
    return round(min(weight, 1.0), 2)


def get_spawn_inject(role_id, current_topic='', current_category='', round_n=1, mode='light'):
    """
    Generate spawn prompt injection text for a role, based on:
    1. Topic relevance (same category = higher priority)
    2. Influence weight (recent high-scoring sessions)
    3. Skip list (stance_history_skip_sessions)
    4. Relationship network (if enabled)

    mode='light': inject 1 top entry (for first-round quick context)
    mode='deep':  inject top 3 entries + relationship context (for full depth)

    Returns markdown-formatted string to inject into spawn prompt.
    Use round_n=1 for first round injection, round_n>=2 will return empty
    to avoid repeating content already seen in discussion.
    """
    if round_n >= 2:
        return ''  # Skip injection for round 2+ (already in discussion context)

    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return ''

    sh = role.get('stance_history', [])
    if not sh:
        return ''

    # Parse skip list
    skip_raw = _get_config('stance_history_skip_sessions', '')
    skip_ids = set(s.strip() for s in skip_raw.split(',') if s.strip())

    # Filter out skipped sessions
    eligible = [s for s in sh if s.get('session_id') not in skip_ids]
    if not eligible:
        return ''

    # Count how many were skipped for display
    skipped_count = sum(1 for s in sh if s.get('session_id') in skip_ids)

    # Calculate influence weight for each eligible entry via the single source of truth
    for entry in eligible:
        entry['_weight'] = _influence_weight(entry, current_category)

    eligible.sort(key=lambda e: e.get('_weight', 0), reverse=True)
    rel_enabled = is_relationship_enabled()

    lines = []
    lines.append('📜 你之前说过：')

    if mode == 'deep' and len(eligible) >= 2:
        # Deep inject: top N entries (configurable)
        top_n = min(int(_get_config('deep_mode_inject_count', '3')), len(eligible))
        for i in range(top_n):
            e = eligible[i]
            w = e.get('_weight', 0)
            star = ' ⭐' if w >= 0.7 else ''
            lines.append('  - {}（{}）："{}"{}'.format(
                '上次' if i == 0 else '第{}次'.format(i + 1),
                e.get('topic', '?'), e.get('stance', '?'), star))
        if skipped_count > 0:
            lines.append('  （已跳过 {} 场历史，不注入）'.format(skipped_count))
        lines.append('')
        lines.append('这次议题是[{}]，你还坚持吗？'.format(current_topic or '当前议题'))
        # Check if previous stances were contradictory
        stances = [e.get('stance', '') for e in eligible[:top_n]]
        unique_stances = len(set(stances))
        if unique_stances <= 1:
            lines.append('注：你之前每次立场都很一致——这次会改变吗？')
        else:
            lines.append('注：你之前立场有变化——这次会延续还是转向？')
    else:
        # Light inject: 1 top entry (original behavior)
        top = eligible[0]
        lines.append('  - 上次（{}）："{}"'.format(top.get('topic', '?'), top.get('stance', '?')))
        if skipped_count > 0:
            lines.append('  （已跳过 {} 场历史）'.format(skipped_count))
        lines.append('这次议题是[{}]，你还坚持吗？'.format(current_topic or '当前议题'))

    # Relationship context (if enabled)
    if rel_enabled:
        rel_lines = role.get('relationship_lines', [])
        if rel_lines:
            strongest = max(rel_lines, key=lambda r: r.get('co_sessions', 0))
            if strongest.get('co_sessions', 0) >= 2:
                lines.append('')
                lines.append('🔗 关系提醒：你和{}已经是{}了（同场{}次）'.format(
                    strongest.get('target_id', '?'),
                    strongest.get('status', '熟人'),
                    strongest.get('co_sessions', 0),
                ))

    return '\n'.join(lines)


def get_compact_history(role_id):
    """
    Get compact one-line stance history for role card display.
    Format: 📜 履历: 议题(立场) → 议题(立场) → 本次？

    Returns markdown string, or empty string if no history.
    """
    roles = _read_growth_record()
    _, role = _find_role(roles, role_id)
    if role is None:
        return ''

    sh = role.get('stance_history', [])
    if not sh:
        return ''

    # Take most recent 3 entries for compact display
    recent = sh[-3:]
    parts = []
    for entry in recent:
        topic = entry.get('topic', '?')[:6]
        stance = entry.get('stance', '?')[:8]
        parts.append('{}({})'.format(topic, stance))

    parts.append('本次？')
    return '📜 履历: ' + ' → '.join(parts)


def get_compact_display(role_id):
    """
    Full compact display block for role card bottom.
    Includes compact history + expand icon if history exists.

    Returns markdown string, or empty string if no history.
    """
    compact = get_compact_history(role_id)
    if not compact:
        return ''

    lines = []
    lines.append('')
    lines.append('**立场履历**：')
    lines.append(compact + '  📈')
    return '\n'.join(lines)


def is_relationship_enabled():
    """
    Determine if relationship network should be active for current session.

    Priority (highest first):
      1. mode=='never'     → always False (dead switch)
      2. mode=='always'   → always True  (bypasses enabled flag)
      3. session_override  → override value (temporary)
      4. enabled flag      → auto mode gate
    """
    mode = _get_config('relationship_network_mode', 'auto')
    if mode == 'never':
        return False
    if mode == 'always':
        return True
    if _session_relationship_override is not None:
        return _session_relationship_override
    enabled = _get_config('relationship_network_enabled', 'false')
    return enabled.lower() == 'true'


def _is_guidance_needed():
    """
    Check if relationship network guidance hint should be shown.
    Conditions: mode=auto, not enabled, and at least one role has relationships.

    Returns True if guidance should be rendered.
    """
    mode = _get_config('relationship_network_mode', 'auto')
    if mode != 'auto':
        return False
    if _session_relationship_override is not None:
        return False
    enabled = _get_config('relationship_network_enabled', 'false')
    if enabled.lower() == 'true':
        return False

    # Check if any role has relationship data
    roles = _read_growth_record()
    for role in roles:
        rel_lines = role.get('relationship_lines', [])
        if len(rel_lines) >= 1:
            return True
    return False


def backup_all(backup_dir=None):
    """
    Full backup of all roles' growth_record.
    Saves to {growth_dir}/growth_backups/YYYYMMDD-HHMM.json
    Keeps max 30 backups, auto-evicts oldest.

    Returns backup filepath, or None on failure.
    """
    growth_dir = _get_growth_dir()
    roles = _read_growth_record()

    if backup_dir is None:
        backup_dir = os.path.join(growth_dir, 'growth_backups')

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now()
    filename = timestamp.strftime('%Y%m%d-%H%M.json')
    filepath = os.path.join(backup_dir, filename)

    data = {
        'version': _get_current_schema_version(),
        'backup_at': timestamp.isoformat(),
        'roles': roles,
    }

    with codecs.open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Auto-evict: keep max N backups (configurable)
    _evict_old_backups(backup_dir, max_keep=int(_get_config('backup_keep_count', '30')))

    return filepath


def restore_all(backup_file):
    """
    Restore all roles' growth_record from a backup file.
    Before restoring, automatically creates a backup of current state (rescue backup).

    Returns number of roles restored, or None on failure.
    """
    if not os.path.isfile(backup_file):
        return None

    # Rescue backup
    backup_all()

    with codecs.open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    roles = data.get('roles', [])
    if isinstance(data, list):
        roles = data

    if not roles:
        return 0

    # Restore schema version
    ver = data.get('version', 1)
    _set_schema_version(ver)

    _write_growth_record(roles)
    return len(roles)


def _evict_old_backups(backup_dir, max_keep=30):
    """Remove oldest backups exceeding max_keep count."""
    if not os.path.isdir(backup_dir):
        return
    files = sorted([
        f for f in os.listdir(backup_dir)
        if f.endswith('.json') and f.startswith('20')
    ])
    while len(files) > max_keep:
        oldest = files.pop(0)
        try:
            os.remove(os.path.join(backup_dir, oldest))
        except OSError:
            pass


# ─── Utility: stance history weight calculation ───

def calc_influence_weight(stance_entry, current_category=''):
    """
    Backward-compatible wrapper — delegates to the single source of truth
    _influence_weight(). Kept for migrate_schema() backfill and any external callers.

    NOTE: historically this held a divergent THIRD formula (base 0.5, no relevance
    term, multiplicative time decay) that never entered the runtime and disagreed with
    both the docs and get_spawn_inject. It is now unified — no separate formula remains.
    """
    return _influence_weight(stance_entry, current_category)


# ─── Auto-backup trigger ───

_last_backup_time = None


def auto_backup_if_needed():
    """
    Check if auto-backup is needed (≥24h since last backup).
    Called by discussion_archive.py after each archive.
    """
    global _last_backup_time
    now = datetime.datetime.now()
    if _last_backup_time is None:
        # Try to find latest existing backup
        backup_dir = os.path.join(_get_growth_dir(), 'growth_backups')
        if os.path.isdir(backup_dir):
            existing = sorted([
                f for f in os.listdir(backup_dir)
                if f.endswith('.json') and f.startswith('20')
            ])
            if existing:
                last_fname = existing[-1]
                try:
                    ts_str = last_fname.replace('.json', '')
                    _last_backup_time = datetime.datetime.strptime(ts_str, '%Y%m%d-%H%M')
                except ValueError:
                    pass

    if _last_backup_time is None or (now - _last_backup_time).total_seconds() >= 86400:
        path = backup_all()
        _last_backup_time = now
        return path
    return None


# ─── Maintenance: migrate data schema ───

def migrate_schema(target_version=None):
    """
    Migrate growth_record to target schema version.
    Called by growth_migrate.py.

    Returns (current_version, target_version, migrated_count).
    """
    fp = _get_growth_filepath()
    if not os.path.isfile(fp):
        return (_get_current_schema_version(), target_version, 0)

    data = None
    with codecs.open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    current_ver = data.get('version', 1) if isinstance(data, dict) else 1
    if target_version is None:
        target_version = current_ver

    roles = data.get('roles', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    migrated = 0
    ver = current_ver

    while ver < target_version:
        ver += 1
        for role in roles:
            # version 1→2: ensure all fields exist
            if ver == 2:
                role.setdefault('career_events', [])
                role.setdefault('achievements', [])
                role.setdefault('auto_tags', [])
                role.setdefault('manual_tags', [])
                role.setdefault('version', 1)
                role['version'] = 2
                # Ensure stance_history entries have influence_weight
                for s in role.get('stance_history', []):
                    if 'influence_weight' not in s:
                        s['influence_weight'] = calc_influence_weight(s)
                migrated += 1
            # version 2→3: future migration
            # if ver == 3:
            #     ...

    _set_schema_version(ver)
    _write_growth_record(roles)
    return (current_ver, ver, migrated)