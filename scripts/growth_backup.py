# -*- coding: utf-8 -*-
"""
growth_backup.py - Growth data backup and restore

Usage:
    python growth_backup.py --backup              # Create backup
    python growth_backup.py --restore <file>       # Restore from backup
    python growth_backup.py --list                 # List available backups
"""

import os
import sys
import glob
import argparse
import datetime

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api


def list_backups():
    """List all available backups sorted by date (newest first)."""
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


def main():
    parser = argparse.ArgumentParser(description='Growth data backup and restore')
    parser.add_argument('--backup', action='store_true', help='Create a new backup')
    parser.add_argument('--restore', metavar='FILE', help='Restore from backup file')
    parser.add_argument('--list', action='store_true', help='List available backups')
    args = parser.parse_args()

    if args.list:
        list_backups()
        return

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
        return

    if args.restore:
        restore_file = args.restore
        if not os.path.isfile(restore_file):
            print('Error: backup file not found: ' + restore_file)
            return

        print('Restoring from: ' + restore_file)
        print('(A rescue backup of current state will be created first.)')

        count = growth_api.restore_all(restore_file)
        if count is None:
            print('Restore failed: invalid backup file.')
        elif count == 0:
            print('Restore completed: no roles found in backup.')
        else:
            print('Restore completed: {} roles restored.'.format(count))
        return

    # No args: show help
    parser.print_help()
    print('\nQuick usage:')
    print('  python growth_backup.py --backup')
    print('  python growth_backup.py --list')
    print('  python growth_backup.py --restore growth_backups/20260609-1200.json')


if __name__ == '__main__':
    main()