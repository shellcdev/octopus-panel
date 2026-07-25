#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_tool.py — 角色成长系统运维总入口（合并 growth_backup / growth_migrate /
growth_render 三 CLI 包装）

子命令（参数与原独立脚本一致）:
  backup   [--backup|--restore FILE|--list]     备份/还原/列出成长数据
  migrate  [--target N] [--dry-run]            成长数据 Schema 迁移
  render   <role_id>                           渲染完整成长卡片 (markdown)

说明: 业务逻辑全部复用 growth_api.py（同目录核心数据层），本文件仅做命令行分发。
"""
import os
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api


# ============================================================ cmd: backup
def cmd_backup(args):
    import glob
    import datetime

    def list_backups():
        growth_dir = growth_api._get_growth_dir()
        backup_dir = os.path.join(growth_dir, 'growth_backups')
        if not os.path.isdir(backup_dir):
            print('No backup directory found at: ' + backup_dir)
            return
        pattern = os.path.join(backup_dir, '20*.json')
        files = sorted(glob.glob(pattern), reverse=True)
        if not files:
            print('No backups found in: ' + backup_dir)
            return
        print('Available backups (newest first):\n')
        print('{:<20} {:<25} {:<10}'.format('File', 'Date', 'Size'))
        print('-' * 55)
        for fpath in files:
            fname = os.path.basename(fpath)
            size = os.path.getsize(fpath)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
            size_str = '{:.1f}KB'.format(size / 1024) if size > 1024 else '{}B'.format(size)
            print('{:<20} {:<25} {:<10}'.format(fname, mtime.strftime('%Y-%m-%d %H:%M'), size_str))

    if args.list:
        list_backups()
        return 0

    if args.backup:
        print('Creating backup...')
        filepath = growth_api.backup_all()
        if filepath:
            size = os.path.getsize(filepath)
            size_str = '{:.1f}KB'.format(size / 1024) if size > 1024 else '{}B'.format(size)
            print('Backup created: ' + filepath)
            print('Size: ' + size_str)
        else:
            print('Backup failed.')
        return 0

    if args.restore:
        restore_file = args.restore
        if not os.path.isfile(restore_file):
            print('Error: backup file not found: ' + restore_file)
            return 1
        print('Restoring from: ' + restore_file)
        print('(A rescue backup of current state will be created first.)')
        count = growth_api.restore_all(restore_file)
        if count is None:
            print('Restore failed: invalid backup file.')
        elif count == 0:
            print('Restore completed: no roles found in backup.')
        else:
            print('Restore completed: {} roles restored.'.format(count))
        return 0

    return None  # 无参数 -> 打印帮助


# ============================================================ cmd: migrate
def cmd_migrate(args):
    import json
    import datetime

    fp = growth_api._get_growth_filepath()
    if not os.path.isfile(fp):
        print('No growth_record.json found at: ' + str(fp))
        print('Nothing to migrate.')
        return 0

    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    current_ver = data.get('version', 1) if isinstance(data, dict) else 1
    roles = data.get('roles', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    print('Current schema version: {}'.format(current_ver))
    print('Roles count: {}'.format(len(roles)))

    if not args.target:
        print('\nNo --target specified. To migrate, run:')
        print('  python growth_tool.py migrate --target {}'.format(current_ver + 1))
        return 0

    if args.target <= current_ver:
        print('\nAlready at version {}. No migration needed.'.format(current_ver))
        return 0

    print('\nTarget version: {}'.format(args.target))
    print('Roles to migrate: {}'.format(len(roles)))

    if args.dry_run:
        print('\n[Dry run] Preview of changes:')
    else:
        print('\nExecuting migration...')

    ver = current_ver
    migrated = 0

    while ver < args.target:
        ver += 1
        for role in roles:
            if ver == 2:
                changes = []
                if 'career_events' not in role:
                    role['career_events'] = []
                    changes.append('+career_events')
                if 'achievements' not in role:
                    role['achievements'] = []
                    changes.append('+achievements')
                if 'auto_tags' not in role:
                    role['auto_tags'] = []
                    changes.append('+auto_tags')
                if 'manual_tags' not in role:
                    role['manual_tags'] = []
                    changes.append('+manual_tags')
                role['version'] = 2
                for s in role.get('stance_history', []):
                    if 'influence_weight' not in s:
                        s['influence_weight'] = growth_api.calc_influence_weight(s)
                        changes.append('+weight:{}'.format(s.get('session_id', '')[:8]))
                if changes:
                    migrated += 1
                    if args.dry_run:
                        print('  [v2] {}: {}'.format(role.get('role_id', '?'), ', '.join(changes[:5])))

    if not args.dry_run:
        growth_api._set_schema_version(ver)
        if isinstance(data, dict):
            data['version'] = ver
            data['updated_at'] = datetime.datetime.now().isoformat()
            data['roles'] = roles
        else:
            data = {
                'version': ver,
                'updated_at': datetime.datetime.now().isoformat(),
                'roles': roles,
            }
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        growth_api._set_schema_version(ver)
        print('\nMigration complete: version {} → {} ({} roles affected)'.format(
            current_ver, ver, migrated))
    else:
        print('\n[Dry run] Would affect {} roles. Run without --dry-run to apply.'.format(migrated))
    return 0


# ============================================================ cmd: render
def cmd_render(args):
    profile = render_full_profile(args.role_id)
    if not profile:
        print('No growth data found for role: ' + args.role_id)
        return 0
    print(profile)
    return 0


# ============================================================ render (inlined from growth_render)
def render_full_profile(role_id):
    """
    Render complete growth card for a role.
    Returns markdown-formatted string, or empty string if no data.
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
            period = _period_label(i, len(stance_history), stance)
            lines.append('  第{}场 —— {}："{}"'.format(i + 1, period, stance))
        lines.append('')

    # ─── Section 3.5: Career Events ───
    career_events = growth_data.get('career_events', [])
    if career_events:
        sorted_events = sorted(career_events, key=lambda e: e.get('occurred_at', ''), reverse=True)
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
    """
    if len(stance_history) < 2:
        return ''

    first = stance_history[0].get('stance', '')
    last = stance_history[-1].get('stance', '')

    if first == last:
        return ' — 从一而终，从未动摇'

    first_short = first[:12]
    last_short = last[:12]

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

    if index == 0:
        return '初登场期'

    if index == total - 1:
        if '条件' in stance or '但' in stance:
            return '条件反思期'
        return '最新立场期'

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

    topic_counts = {}
    for entry in stance_history:
        topic = entry.get('topic', '')
        if topic:
            cat = growth_api._classify_topic(topic)
            cat_cn = {'career': '职场决策', 'financial': '财务投资', 'family': '家庭感情',
                      'technical': '技术选型', 'general': '综合话题'}.get(cat, '综合话题')
            topic_counts[cat_cn] = topic_counts.get(cat_cn, 0) + 1

    if topic_counts:
        sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
        top3 = ' / '.join(['{}({}场)'.format(t, c) for t, c in sorted_topics[:3]])
        stats.append(('最爱讨论', top3))

    rel_lines = growth_data.get('relationship_lines', [])
    if rel_lines:
        strongest = max(rel_lines, key=lambda r: r.get('co_sessions', 0))
        cs = strongest.get('co_sessions', 0)
        target = strongest.get('target_id', '?')
        if cs >= 2:
            stats.append(('最常对抗', '{}（同场{}次）'.format(target, cs)))

    scores = [s.get('score') for s in stance_history if s.get('score') is not None]
    if scores:
        avg = sum(scores) / len(scores)
        stats.append(('平均讨论评分', '{:.0f}/100'.format(avg)))

    rang_count = sum(1 for s in stance_history
                     if '条件' in s.get('stance', '') or '但' in s.get('stance', ''))
    if rang_count > 0:
        stats.append(('[让] 次数', '{}次'.format(rang_count)))

    return stats


def render_guidance():
    """
    Render conditional guidance hint for relationship network.
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


# ============================================================ main
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Role Growth system ops (backup/migrate/render)')
    sub = parser.add_subparsers(dest='cmd')

    p_b = sub.add_parser('backup', help='备份/还原/列出成长数据')
    p_b.add_argument('--backup', action='store_true')
    p_b.add_argument('--restore', metavar='FILE')
    p_b.add_argument('--list', action='store_true')

    p_m = sub.add_parser('migrate', help='成长数据 Schema 迁移')
    p_m.add_argument('--target', type=int)
    p_m.add_argument('--dry-run', action='store_true')

    p_r = sub.add_parser('render', help='渲染完整成长卡片')
    p_r.add_argument('role_id')

    args = parser.parse_args()

    if args.cmd == 'backup':
        rc = cmd_backup(args)
        if rc is None:
            parser.parse_args(['backup', '--help'])
        return rc or 0
    if args.cmd == 'migrate':
        return cmd_migrate(args)
    if args.cmd == 'render':
        return cmd_render(args)
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
