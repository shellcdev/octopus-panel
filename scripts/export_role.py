# -*- coding: utf-8 -*-
"""
export_role.py - Export/import role growth data for the role marketplace

Usage:
    python export_role.py <role_id>                      # Export to stdout
    python export_role.py <role_id> --output <file.json>  # Export to file
    python export_role.py --import <file.json>             # Import a role

Export format:
    - Stance history: preserved as background story (topics stripped)
    - Career events: preserved as background story (discussion details stripped)
    - Achievements and tags: frozen as snapshot, recalculated in new env
    - Imported roles start at level 1, EXP 0
"""

import os
import sys
import json
import codecs
import argparse
import datetime

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api


def export_role(role_id):
    """
    Export role growth data as a shareable template.
    Sensitive discussion details are stripped, only role identity + achievements kept.
    """
    growth_data = growth_api.get_role_growth(role_id)
    if growth_data is None:
        return None

    # Sanitize: strip session_id and topics from stance_history
    sanitized_history = []
    for s in growth_data.get('stance_history', []):
        sanitized_history.append({
            'topic_category': growth_api._classify_topic(s.get('topic', '')),
            'stance': s.get('stance', ''),
            'score': s.get('score'),
        })

    # Sanitize career events: only keep event type, strip discussion context
    sanitized_events = []
    for e in growth_data.get('career_events', []):
        sanitized_events.append({
            'event': e.get('event', ''),
            'description': e.get('description', '')[:60],
        })

    export = {
        'version': growth_api._get_current_schema_version(),
        'exported_at': datetime.datetime.now().isoformat(),
        'role_id': role_id,
        'template_source': 'octopus-panel',
        'stats': {
            'total_sessions': growth_data.get('total_sessions', 0),
            'avg_score': _avg_score(growth_data),
            'achievements_count': len(growth_data.get('achievements', [])),
            'top_category': _top_category(growth_data),
        },
        'stance_history': sanitized_history,
        'career_events': sanitized_events,
        'achievements': growth_data.get('achievements', []),
        'auto_tags': growth_data.get('auto_tags', []),
    }
    return export


def _avg_score(growth_data):
    scores = [s.get('score') for s in growth_data.get('stance_history', []) if s.get('score')]
    return round(sum(scores) / len(scores), 1) if scores else 0


def _top_category(growth_data):
    counts = {}
    for s in growth_data.get('stance_history', []):
        cat = growth_api._classify_topic(s.get('topic', ''))
        counts[cat] = counts.get(cat, 0) + 1
    if not counts:
        return 'general'
    return max(counts, key=counts.get)


def import_role(export_data):
    """
    Import a role from an export dict.
    The role starts fresh (level 1, EXP 0) but preserves historical stances
    as background story. Tags and achievements are frozen as snapshot.
    """
    role_id = export_data.get('role_id', 'ImportedRole')
    growth_data = growth_api.get_role_growth(role_id)

    if growth_data is not None:
        print('Role "{}" already exists, skipping import.'.format(role_id))
        return False

    # Create role with import stamp
    new_role = {
        'version': growth_api._get_current_schema_version(),
        'role_id': role_id,
        'total_sessions': 0,
        'level': 1,
        'exp': 0,
        'stance_history': [],
        'career_events': [{
            'event': 'IMPORTED',
            'description': '从角色集市导入（来源：{}, {} 场经验）'.format(
                export_data.get('template_source', 'unknown'),
                export_data.get('stats', {}).get('total_sessions', 0)),
            'occurred_at': export_data.get('exported_at', ''),
        }],
        'achievements': [],
        'relationship_lines': [],
        'auto_tags': [],
        'manual_tags': [],
    }
    ok = growth_api.upsert_role(new_role)
    print('Imported role: {}'.format(role_id))
    return True


def main():
    parser = argparse.ArgumentParser(description='Export/import role growth data')
    parser.add_argument('role_id', nargs='?', help='Role ID to export')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--import-file', help='Import role from JSON file')
    args = parser.parse_args()

    if args.import_file:
        with codecs.open(args.import_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        import_role(data)
        return

    if not args.role_id:
        parser.print_help()
        print('\nQuick usage:')
        print('  python export_role.py 赌徒')
        print('  python export_role.py 赌徒 --output role_export.json')
        print('  python export_role.py --import-file role_export.json')
        return

    export = export_role(args.role_id)
    if export is None:
        print('Role not found: ' + args.role_id)
        return

    output = json.dumps(export, ensure_ascii=False, indent=2)
    if args.output:
        with codecs.open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print('Exported: {} → {}'.format(args.role_id, args.output))
    else:
        print(output)


if __name__ == '__main__':
    main()