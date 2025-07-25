
import shutil
import os
from datetime import datetime

def backup_database():
    """Create a timestamped backup of the SQLite database"""
    if os.path.exists('mwangaza.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backups/mwangaza_backup_{timestamp}.db'
        
        # Create backups directory if it doesn't exist
        os.makedirs('backups', exist_ok=True)
        
        # Copy the database file
        shutil.copy2('mwangaza.db', backup_filename)
        print(f"Database backed up to: {backup_filename}")
        
        # Keep only the last 10 backups
        cleanup_old_backups()
    else:
        print("Database file not found!")

def cleanup_old_backups():
    """Keep only the 10 most recent backups"""
    backup_dir = 'backups'
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('mwangaza_backup_')]
        backup_files.sort(reverse=True)
        
        # Remove old backups, keep only 10 most recent
        for old_backup in backup_files[10:]:
            os.remove(os.path.join(backup_dir, old_backup))
            print(f"Removed old backup: {old_backup}")

if __name__ == "__main__":
    backup_database()
