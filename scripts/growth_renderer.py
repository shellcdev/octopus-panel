# -*- coding: utf-8 -*-
"""
growth_renderer.py - Full profile renderer for role growth (Phase 3)

Generates markdown text for the complete role growth card display.
Called when user requests "完整档" (full profile) for a role.

Sections:
  1. Header: level, sessions, exp
  2. Stance History Tree with narrative summary
  3. Achievement Wall
  4. Relationship Network (text version, future force-directed graph)
  5. Statistics Dashboard
  6. Tag Wall (auto + manual with confidence)

Dependencies: growth_api.py (must be in same directory)
"""

import os
import sys
import io

# UTF-8 重包装：中文 Windows (cp936) 下 print CJK 可能 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api


def render_full_profile(role_id):
    """
    Render complete growth card for a role.
    Returns markdown-formatted string, or empty string if no data.

    Format:
    📊 角色成长卡 — [emoji] [role_id]
    等级：Lv.X  |  场次：N场  |  经验：XXX

    🏆 成就墙
      ✅ ...

    🌿 成长树 — 心路总结
      ...

    🔗 关系网络
      ...

    📊 数据统计
      ...

    🏷️ 标签
      ...
    """
    growth_data = growth_api.get_role_growth(role_id)
    if growth_data is None:
        return ''

    lines = []

    # ─── Section 1: Header ───
    lines.append('📊 角色成长卡 — {}'.format(role_id))
    lines.append('')
    level = growth_data.get('level', 1)
    total = growth_data.get('total_sessions', 0)
    exp = growth_data.get('exp', 0)
    lines.append('等级：Lv.{}  |  场次：{}场  |  经验：{}'.format(level, total, exp))
    lines.append('')

    # ─── Section 2: Achievement Wall ───
    achievements = growth_data.get('achievements', [])
    if achievements:
        lines.append('🏆 成就墙')
        lines.append('')
        for a in achievements:
            name = a.get('name', '?')
            desc = a.get('description', '')
            lines.append('  ✅ {} — {}'.format(name, desc))
        lines.append('')

    # ─── Section 3: Growth Tree with narrative ───
    stance_history = growth_data.get('stance_history', [])
    if stance_history:
        lines.append('🌿 成长树{}'.format(_build_narrative_summary(stance_history, role_id)))
        lines.append('')
        for i, entry in enumerate(stance_history):
            topic = entry.get('topic', '?')[:10]
            stance = entry.get('stance', '?')[:30]
            # Generate a simple period label
            period = _period_label(i, len(stance_history), stance)
            lines.append('  第{}场 —— {}："{}"'.format(i + 1, period, stance))
        lines.append('')

    # ─── Section 3.5: Career Events ───
    career_events = growth_data.get('career_events', [])
    if career_events:
        # Reverse chronological order (newest first)
        sorted_events = sorted(career_events, key=lambda e: e.get('occurred_at', ''), reverse=True)
        # Limit to 5 most recent for display
        recent_events = sorted_events[:5]

        lines.append('🎉 生涯事件')
        lines.append('')
        for ev in recent_events:
            desc = ev.get('description', '?')
            aid = ev.get('event', '')
            icon = '🎉' if 'MILESTONE' in aid or 'FIRST' in aid else '📌'
            lines.append('  {} {}'.format(icon, desc))
        lines.append('')

    # ─── Section 4: Relationship Network ───
    rel_lines = growth_data.get('relationship_lines', [])
    if rel_lines and growth_api.is_relationship_enabled():
        lines.append('🔗 关系网络')
        lines.append('')
        for rel in rel_lines:
            target = rel.get('target_id', '?')
            status = rel.get('status', '一面之缘')
            cs = rel.get('co_sessions', 1)
            rtype = rel.get('relation_type', 'neutral')
            type_icon = _relation_type_icon(rtype)
            lines.append('  {} {} —— {}（同场{}次）'.format(type_icon, target, status, cs))
        lines.append('')

    # ─── Section 5: Statistics Dashboard ───
    stats = _compute_stats(growth_data)
    if stats:
        lines.append('📊 数据统计')
        lines.append('')
        for label, val in stats:
            lines.append('  {}：{}'.format(label, val))
        lines.append('')

    # ─── Section 6: Tag Wall ───
    auto_tags = growth_data.get('auto_tags', [])
    manual_tags = growth_data.get('manual_tags', [])
    if auto_tags or manual_tags:
        lines.append('🏷️ 标签')
        lines.append('')
        for mt in manual_tags:
            tag = mt.get('tag', '?') if isinstance(mt, dict) else mt
            lines.append('  🔖 {} [手动]'.format(tag))
        for at in auto_tags:
            lines.append('  🔖 {} [自动]'.format(at))
        lines.append('')

    return '\n'.join(lines).strip()


def _build_narrative_summary(stance_history, role_id):
    """
    Auto-generate a one-line narrative summary ("心路总结").
    Compares first and last stance text to detect change arc.

    Returns string like: ' — 从"梭了"到"条件梭了"，开始看对手下注了'
    Or empty if only one entry.
    """
    if len(stance_history) < 2:
        return ''

    first = stance_history[0].get('stance', '')
    last = stance_history[-1].get('stance', '')

    if first == last:
        return ' — 从一而终，从未动摇'

    # Detect change direction
    first_short = first[:12]
    last_short = last[:12]

    # Check for 条件/但 (conditional shift)
    has_condition = '条件' in last or '但' in last

    narrative = ''
    if has_condition:
        narrative = '学会了加条件——不再是无脑坚持了'
    elif len(last) > len(first):
        narrative = '表达越来越丰富了'
    else:
        narrative = '观点有了变化——开始换角度看问题了'

    return ' — 从"{}"到"{}"，{}'.format(first_short, last_short, narrative)


def _period_label(index, total, stance):
    """Generate a descriptive period label for the growth tree."""
    if total <= 1:
        return '初登场'

    # First entry
    if index == 0:
        return '初登场期'

    # Last entry
    if index == total - 1:
        if '条件' in stance or '但' in stance:
            return '条件反思期'
        return '最新立场期'

    # Middle entries
    ratio = index / total
    if ratio < 0.3:
        return '早期立场期'
    elif ratio < 0.6:
        return '中期演化期'
    else:
        return '近期调整期'


def _relation_type_icon(rel_type):
    """Map relation type to emoji icon."""
    mapping = {
        '欠人情': '🤝',
        '合作': '🤝',
        '对抗': '⚔️',
        '中立': '➖',
        'neutral': '➖',
        'friendly': '👍',
        'hostile': '👎',
    }
    return mapping.get(rel_type, '➖')


def _compute_stats(growth_data):
    """
    Compute interesting statistics for the stats dashboard.
    Returns list of (label, value) tuples.
    """
    stats = []
    stance_history = growth_data.get('stance_history', [])

    # Topic category counts
    topic_counts = {}
    for entry in stance_history:
        topic = entry.get('topic', '')
        if topic:
            cat = growth_api._classify_topic(topic)
            # Map category to Chinese
            cat_cn = {'career': '职场决策', 'financial': '财务投资', 'family': '家庭感情',
                      'technical': '技术选型', 'general': '综合话题'}.get(cat, '综合话题')
            topic_counts[cat_cn] = topic_counts.get(cat_cn, 0) + 1

    if topic_counts:
        sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
        top3 = ' / '.join(['{}({}场)'.format(t, c) for t, c in sorted_topics[:3]])
        stats.append(('最爱讨论', top3))

    # Relationship: most frequent co-participant
    rel_lines = growth_data.get('relationship_lines', [])
    if rel_lines:
        strongest = max(rel_lines, key=lambda r: r.get('co_sessions', 0))
        cs = strongest.get('co_sessions', 0)
        target = strongest.get('target_id', '?')
        if cs >= 2:
            stats.append(('最常对抗', '{}（同场{}次）'.format(target, cs)))

    # Average stance score
    scores = [s.get('score') for s in stance_history if s.get('score') is not None]
    if scores:
        avg = sum(scores) / len(scores)
        stats.append(('平均讨论评分', '{:.0f}/100'.format(avg)))

    # [让] count (estimated)
    rang_count = sum(1 for s in stance_history
                     if '条件' in s.get('stance', '') or '但' in s.get('stance', ''))
    if rang_count > 0:
        stats.append(('[让] 次数', '{}次'.format(rang_count)))

    return stats


def render_guidance():
    """
    Render conditional guidance hint for relationship network.
    Called when relationship_network_enabled is False and mode is 'auto',
    and at least one role has relationship_lines >= 1.

    Returns markdown hint string, or empty string if no guidance needed.
    """
    if not growth_api._is_guidance_needed():
        return ''

    lines = []
    lines.append('')
    lines.append('💡 有些角色之间开始建立关系了。说"开启关系网络"解锁。🔗')
    lines.append('')
    return '\n'.join(lines)


def render_session_override_notice(override_value):
    """
    Render confirmation notice when user sets session override.
    override_value: True = restored, False = disabled
    """
    if override_value is False:
        return ('好的。这场讨论临时关闭关系网络——\n'
                '角色之间的关系信息不会被注入讨论，对抗位不受关系影响。\n'
                '下一场自动恢复。\n'
                '说"这轮恢复关系"可以提前恢复。')
    else:
        return '好的，这场讨论的关系网络已恢复。'


# ─── Standalone entry point ───

def main():
    """CLI: render full profile for a role."""
    import argparse
    parser = argparse.ArgumentParser(description='Render full growth profile for a role')
    parser.add_argument('role_id', help='Role name/ID to render')
    args = parser.parse_args()

    profile = render_full_profile(args.role_id)
    if not profile:
        print('No growth data found for role: ' + args.role_id)
        return

    print(profile)


if __name__ == '__main__':
    main()