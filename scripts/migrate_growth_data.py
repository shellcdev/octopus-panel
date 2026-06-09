# -*- coding: utf-8 -*-
"""
migrate_growth_data.py - Data schema migration for growth_record

Usage:
    python migrate_growth_data.py                        # Show current version
    python migrate_growth_data.py --target 2              # Migrate to version 2
    python migrate_growth_data.py --target 2 --dry-run    # Preview without writing

Migration history:
    version 1 → 2: Add career_events, achievements, auto_tags, manual_tags fields.
                   Calculate influence_weight for existing stance_history entries.
"""

import os
import sys
import json
import argparse

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api


def main():
    parser = argparse.ArgumentParser(description='Migrate growth_record to target schema version')
    parser.add_argument('--target', type=int, help='Target schema version (e.g. 2)')
    parser.add_argument('--dry-run', action='store_true', help='Preview migration without writing')
    args = parser.parse_args()

    # Show current version
    fp = growth_api._get_growth_filepath()
    if not os.path.isfile(fp):
        print('No growth_record.json found at: ' + str(fp))
        print('Nothing to migrate.')
        return

    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    current_ver = data.get('version', 1) if isinstance(data, dict) else 1
    roles = data.get('roles', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    print('Current schema version: {}'.format(current_ver))
    print('Roles count: {}'.format(len(roles)))

    if not args.target:
        print('\nNo --target specified. To migrate, run:')
        print('  python migrate_growth_data.py --target {}'.format(current_ver + 1))
        return

    if args.target <= current_ver:
        print('\nAlready at version {}. No migration needed.'.format(current_ver))
        return

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

                # Calculate influence_weight for existing stance entries
                for s in role.get('stance_history', []):
                    if 'influence_weight' not in s:
                        s['influence_weight'] = growth_api.calc_influence_weight(s)
                        changes.append('+weight:{}'.format(s.get('session_id','')[:8]))

                if changes:
                    migrated += 1
                    if args.dry_run:
                        print('  [v2] {}: {}'.format(role.get('role_id', '?'), ', '.join(changes[:5])))
            # Future migrations:
            # if ver == 3:
            #     ...

    if not args.dry_run:
        # Write migrated data
        growth_api._set_schema_version(ver)

        # Write via growth_api (handles atomic write)
        if isinstance(data, dict):
            data['version'] = ver
            data['updated_at'] = __import__('datetime').datetime.now().isoformat()
            data['roles'] = roles
        else:
            data = {
                'version': ver,
                'updated_at': __import__('datetime').datetime.now().isoformat(),
                'roles': roles,
            }

        # Need direct write since _write_growth_record re-reads from disk
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        growth_api._set_schema_version(ver)
        print('\nMigration complete: version {} → {} ({} roles affected)'.format(
            current_ver, ver, migrated))
    else:
        print('\n[Dry run] Would affect {} roles. Run without --dry-run to apply.'.format(migrated))


if __name__ == '__main__':
    main()