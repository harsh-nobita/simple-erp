import os
import shutil
from datetime import datetime


def backup_sqlite(db_path, out_dir='backups'):
    """Create a timestamped copy of the SQLite database file.

    Returns the path to the backup file.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB file not found: {db_path}")

    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    base = os.path.basename(db_path)
    dest = os.path.join(out_dir, f"{base}.{ts}.bak")
    shutil.copy2(db_path, dest)
    return dest


def restore_sqlite(backup_path, db_path):
    """Restore a SQLite DB from a backup file. Overwrites db_path."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    shutil.copy2(backup_path, db_path)
    return db_path
