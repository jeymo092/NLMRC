
import shutil
import os
import sqlite3
from datetime import datetime

def backup_database():
    """Create a timestamped backup of the SQLite database"""
    db_path = 'mwangaza.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    if os.path.getsize(db_path) == 0:
        print("❌ Database file is empty!")
        return False
    
    try:
        # Test database connectivity first
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if not tables:
            print("❌ Database appears to be empty or corrupted!")
            return False
        
        table_names = [table[0] for table in tables]
        print(f"📋 Found tables: {', '.join(table_names)}")
        
        # Create backups directory if it doesn't exist
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'mwangaza_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Verify the backup
        backup_size = os.path.getsize(backup_path)
        original_size = os.path.getsize(db_path)
        
        if backup_size != original_size:
            print(f"⚠️ Backup size mismatch! Original: {original_size}, Backup: {backup_size}")
            return False
        
        # Test the backup by opening it
        try:
            test_conn = sqlite3.connect(backup_path)
            test_cursor = test_conn.cursor()
            test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            backup_tables = test_cursor.fetchall()
            test_conn.close()
            
            backup_table_names = [table[0] for table in backup_tables]
            
            if set(table_names) != set(backup_table_names):
                print("⚠️ Backup verification failed - table mismatch!")
                return False
                
        except sqlite3.Error as e:
            print(f"❌ Backup verification failed: {e}")
            return False
        
        print(f"✅ Database backed up successfully: {backup_path}")
        print(f"📊 Backup size: {backup_size:,} bytes")
        
        # Keep only the last 10 backups
        cleanup_old_backups(backup_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def cleanup_old_backups(backup_dir='backups'):
    """Keep only the 10 most recent backups"""
    try:
        if not os.path.exists(backup_dir):
            return
            
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('mwangaza_backup_') and f.endswith('.db')]
        
        if len(backup_files) <= 10:
            return
            
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)), reverse=True)
        
        # Remove old backups, keep only 10 most recent
        for old_backup in backup_files[10:]:
            old_backup_path = os.path.join(backup_dir, old_backup)
            os.remove(old_backup_path)
            print(f"🗑️ Removed old backup: {old_backup}")
            
        print(f"📦 Kept {min(len(backup_files), 10)} most recent backups")
        
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")

def restore_backup(backup_filename):
    """Restore database from a backup file"""
    backup_dir = 'backups'
    backup_path = os.path.join(backup_dir, backup_filename)
    db_path = 'mwangaza.db'
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    try:
        # Test the backup file first
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if not tables:
            print("❌ Backup file appears to be empty or corrupted!")
            return False
        
        # Create a backup of current database before restore
        if os.path.exists(db_path):
            current_backup = f'pre_restore_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            current_backup_path = os.path.join(backup_dir, current_backup)
            shutil.copy2(db_path, current_backup_path)
            print(f"📦 Created backup of current database: {current_backup}")
        
        # Restore the backup
        shutil.copy2(backup_path, db_path)
        
        print(f"✅ Database restored successfully from: {backup_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def list_backups():
    """List all available backup files"""
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        print("📁 No backup directory found")
        return []
    
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('mwangaza_backup_') and f.endswith('.db')]
    
    if not backup_files:
        print("📁 No backup files found")
        return []
    
    # Sort by modification time (newest first)
    backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)), reverse=True)
    
    print(f"📋 Found {len(backup_files)} backup files:")
    for i, backup_file in enumerate(backup_files, 1):
        backup_path = os.path.join(backup_dir, backup_file)
        size = os.path.getsize(backup_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
        print(f"  {i}. {backup_file} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    return backup_files

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'backup':
            backup_database()
        elif command == 'list':
            list_backups()
        elif command == 'restore' and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        elif command == 'cleanup':
            cleanup_old_backups()
        else:
            print("Usage:")
            print("  python backup_db.py backup    - Create a new backup")
            print("  python backup_db.py list      - List all backups")
            print("  python backup_db.py restore <filename> - Restore from backup")
            print("  python backup_db.py cleanup   - Clean up old backups")
    else:
        backup_database()
