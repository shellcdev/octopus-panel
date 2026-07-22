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
    from growth_render import render_full_profile  # 复用渲染逻辑模块
    profile = render_full_profile(args.role_id)
    if not profile:
        print('No growth data found for role: ' + args.role_id)
        return 0
    print(profile)
    return 0


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
