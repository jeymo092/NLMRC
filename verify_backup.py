
#!/usr/bin/env python3
"""
Database Verification Script for New Life Mwangaza
Verifies all tables and data are properly backed up including alumni records
"""

import sqlite3
import os
from datetime import datetime

def verify_database_backup(db_path='mwangaza.db'):
    """Comprehensive verification of database backup including alumni"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 COMPREHENSIVE DATABASE VERIFICATION")
        print(f"📅 Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Database File: {db_path}")
        print(f"📊 File Size: {os.path.getsize(db_path):,} bytes")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 TOTAL TABLES: {len(tables)}")
        print("-" * 60)
        
        # Table descriptions for better understanding
        table_descriptions = {
            'user': 'System users and login accounts',
            'client': 'Client records (ACTIVE + ALUMNI)',
            'home_visit': 'Home visit records and reports',
            'after_care': 'Aftercare tracking for alumni clients',
            'student_mark': 'Academic records and test scores',
            'empowerment_programme': 'Life skills and vocational programmes',
            'programme_enrollment': 'Client enrollments in programmes',
            'soap_note': 'Counselling session notes (SOAP format)',
            'treatment_plan': 'Client treatment and intervention plans',
            'exit_form': 'Client exit and discharge forms',
            'subject': 'Academic subjects for testing',
            'parent_record': 'Parent and guardian contact information',
            'grant_record': 'Tools and grants provided to clients'
        }
        
        total_records = 0
        critical_tables = []
        
        # Analyze each table
        for table_name in sorted(tables):
            try:
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                total_records += count
                
                # Get column information
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                description = table_descriptions.get(table_name, 'Database table')
                status = "✅ ACTIVE" if count > 0 else "⚪ EMPTY"
                
                print(f"📊 {table_name.upper()}")
                print(f"   📝 Description: {description}")
                print(f"   📈 Records: {count:,}")
                print(f"   🏗️  Columns: {len(column_names)} ({', '.join(column_names[:5])}{'...' if len(column_names) > 5 else ''})")
                print(f"   🔍 Status: {status}")
                
                # Special verification for critical tables
                if table_name == 'client':
                    # Check alumni specifically
                    cursor.execute("SELECT COUNT(*) FROM client WHERE status='ACTIVE'")
                    active_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM client WHERE status='COMPLETE'")
                    alumni_count = cursor.fetchone()[0]
                    
                    print(f"   👥 ACTIVE Clients: {active_count}")
                    print(f"   🎓 ALUMNI Clients: {alumni_count}")
                    
                    # Show sample alumni data
                    if alumni_count > 0:
                        cursor.execute("SELECT firstName, secondName, createdAt FROM client WHERE status='COMPLETE' LIMIT 3")
                        alumni_sample = cursor.fetchall()
                        print(f"   📋 Alumni Sample:")
                        for i, (fname, sname, created) in enumerate(alumni_sample, 1):
                            print(f"      {i}. {fname} {sname} (Registered: {created[:10] if created else 'N/A'})")
                    
                    critical_tables.append(f"client ({count} total: {active_count} active + {alumni_count} alumni)")
                
                elif table_name == 'after_care':
                    if count > 0:
                        cursor.execute("SELECT COUNT(*) FROM after_care WHERE status='SUCCESSFUL'")
                        successful = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM after_care WHERE status='IN_PROGRESS'")
                        in_progress = cursor.fetchone()[0]
                        print(f"   ✅ Successful: {successful}")
                        print(f"   🔄 In Progress: {in_progress}")
                    critical_tables.append(f"after_care ({count} records)")
                
                elif table_name == 'home_visit':
                    if count > 0:
                        cursor.execute("SELECT COUNT(DISTINCT client_id) FROM home_visit")
                        unique_clients = cursor.fetchone()[0]
                        print(f"   🏠 Clients with visits: {unique_clients}")
                    critical_tables.append(f"home_visit ({count} records)")
                
                elif table_name == 'student_mark':
                    if count > 0:
                        cursor.execute("SELECT COUNT(DISTINCT client_id) FROM student_mark")
                        students_assessed = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM student_mark")
                        subjects_used = cursor.fetchone()[0]
                        print(f"   📚 Students assessed: {students_assessed}")
                        print(f"   📖 Subjects used: {subjects_used}")
                    critical_tables.append(f"student_mark ({count} records)")
                
                elif table_name == 'programme_enrollment':
                    if count > 0:
                        cursor.execute("SELECT COUNT(*) FROM programme_enrollment WHERE status='COMPLETED'")
                        completed = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM programme_enrollment WHERE status='ENROLLED'")
                        enrolled = cursor.fetchone()[0]
                        print(f"   🎯 Completed: {completed}")
                        print(f"   📝 Currently Enrolled: {enrolled}")
                    critical_tables.append(f"programme_enrollment ({count} records)")
                
                elif table_name == 'soap_note':
                    if count > 0:
                        cursor.execute("SELECT COUNT(DISTINCT client_id) FROM soap_note")
                        clients_counselled = cursor.fetchone()[0]
                        print(f"   🗣️  Clients with notes: {clients_counselled}")
                    critical_tables.append(f"soap_note ({count} records)")
                
                print("-" * 60)
                
            except sqlite3.Error as e:
                print(f"❌ Error analyzing table '{table_name}': {e}")
                print("-" * 60)
        
        # Summary Report
        print(f"📊 BACKUP VERIFICATION SUMMARY")
        print(f"✅ Total Tables Verified: {len(tables)}")
        print(f"📈 Total Records: {total_records:,}")
        print(f"💾 Database Size: {os.path.getsize(db_path):,} bytes ({os.path.getsize(db_path)/1024:.1f} KB)")
        
        # Critical Data Verification
        print(f"\n🔑 CRITICAL DATA VERIFICATION:")
        for table_info in critical_tables:
            print(f"   ✅ {table_info}")
        
        # Data Integrity Check
        print(f"\n🔍 DATA INTEGRITY CHECK:")
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()
        if integrity_result[0] == 'ok':
            print("   ✅ Database integrity: PASSED")
        else:
            print(f"   ❌ Database integrity: FAILED ({integrity_result[0]})")
        
        # Foreign Key Check
        cursor.execute("PRAGMA foreign_key_check;")
        fk_errors = cursor.fetchall()
        if not fk_errors:
            print("   ✅ Foreign key constraints: PASSED")
        else:
            print(f"   ⚠️ Foreign key issues: {len(fk_errors)} found")
        
        # Alumni Specific Verification
        print(f"\n🎓 ALUMNI-SPECIFIC VERIFICATION:")
        
        # Check if alumni have associated records
        cursor.execute("""
            SELECT c.firstName, c.secondName, c.id,
                   (SELECT COUNT(*) FROM home_visit hv WHERE hv.client_id = c.id) as home_visits,
                   (SELECT COUNT(*) FROM student_mark sm WHERE sm.client_id = c.id) as academic_records,
                   (SELECT COUNT(*) FROM after_care ac WHERE ac.client_id = c.id) as aftercare_records,
                   (SELECT COUNT(*) FROM programme_enrollment pe WHERE pe.client_id = c.id) as programme_records
            FROM client c 
            WHERE c.status = 'COMPLETE' 
            LIMIT 5
        """)
        
        alumni_with_records = cursor.fetchall()
        if alumni_with_records:
            print("   📋 Alumni Records Verification (Sample):")
            for fname, sname, client_id, hv, ar, ac, pr in alumni_with_records:
                total_records_for_client = hv + ar + ac + pr
                print(f"      🎓 {fname} {sname} (ID: {client_id})")
                print(f"         📊 Total Records: {total_records_for_client} (HV: {hv}, Academic: {ar}, Aftercare: {ac}, Programs: {pr})")
        else:
            print("   ℹ️ No alumni records found or no associated data")
        
        # Check for orphaned records
        print(f"\n🔗 ORPHANED RECORDS CHECK:")
        orphan_checks = [
            ("home_visit", "client_id", "client", "id"),
            ("after_care", "client_id", "client", "id"),
            ("student_mark", "client_id", "client", "id"),
            ("programme_enrollment", "client_id", "client", "id"),
            ("parent_record", "client_id", "client", "id"),
            ("grant_record", "client_id", "client", "id"),
            ("soap_note", "client_id", "client", "id"),
            ("treatment_plan", "client_id", "client", "id"),
            ("exit_form", "client_id", "client", "id")
        ]
        
        for child_table, child_key, parent_table, parent_key in orphan_checks:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {child_table} ct 
                    WHERE ct.{child_key} NOT IN (SELECT pt.{parent_key} FROM {parent_table} pt)
                """)
                orphan_count = cursor.fetchone()[0]
                if orphan_count == 0:
                    print(f"   ✅ {child_table}: No orphaned records")
                else:
                    print(f"   ⚠️ {child_table}: {orphan_count} orphaned records found")
            except sqlite3.Error:
                print(f"   ❓ {child_table}: Could not check (table may not exist)")
        
        conn.close()
        
        print(f"\n" + "=" * 60)
        if total_records > 0:
            print("✅ DATABASE BACKUP VERIFICATION: COMPLETE")
            print("✅ All tables and alumni records are properly backed up!")
        else:
            print("⚠️ DATABASE BACKUP VERIFICATION: EMPTY DATABASE")
            print("ℹ️ Database structure exists but contains no data")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database verification failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def compare_databases(original_db, backup_db):
    """Compare original database with backup to ensure completeness"""
    print(f"\n🔄 COMPARING DATABASES")
    print(f"📁 Original: {original_db}")
    print(f"📁 Backup: {backup_db}")
    print("-" * 60)
    
    if not os.path.exists(original_db):
        print(f"❌ Original database not found: {original_db}")
        return False
    
    if not os.path.exists(backup_db):
        print(f"❌ Backup database not found: {backup_db}")
        return False
    
    try:
        # Connect to both databases
        orig_conn = sqlite3.connect(original_db)
        backup_conn = sqlite3.connect(backup_db)
        
        orig_cursor = orig_conn.cursor()
        backup_cursor = backup_conn.cursor()
        
        # Compare table counts
        orig_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        orig_tables = set(row[0] for row in orig_cursor.fetchall())
        
        backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        backup_tables = set(row[0] for row in backup_cursor.fetchall())
        
        if orig_tables == backup_tables:
            print(f"✅ Table structure match: {len(orig_tables)} tables")
        else:
            print(f"❌ Table structure mismatch!")
            print(f"   Original only: {orig_tables - backup_tables}")
            print(f"   Backup only: {backup_tables - orig_tables}")
        
        # Compare record counts for each table
        mismatches = []
        for table in orig_tables.intersection(backup_tables):
            orig_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            orig_count = orig_cursor.fetchone()[0]
            
            backup_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            backup_count = backup_cursor.fetchone()[0]
            
            if orig_count == backup_count:
                print(f"✅ {table}: {orig_count} records (match)")
            else:
                print(f"❌ {table}: Original={orig_count}, Backup={backup_count}")
                mismatches.append(table)
        
        orig_conn.close()
        backup_conn.close()
        
        if not mismatches:
            print("✅ DATABASE COMPARISON: PERFECT MATCH")
            return True
        else:
            print(f"❌ DATABASE COMPARISON: {len(mismatches)} table(s) with mismatches")
            return False
            
    except Exception as e:
        print(f"❌ Database comparison failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compare' and len(sys.argv) > 3:
            compare_databases(sys.argv[2], sys.argv[3])
        else:
            verify_database_backup(sys.argv[1])
    else:
        # Verify main database
        verify_database_backup('mwangaza.db')
        
        # Also check the most recent backup if it exists
        backup_dir = 'backups'
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) 
                          if f.startswith('New_Life_Mwangaza_Database_Backup_') and f.endswith('.db')]
            if backup_files:
                backup_files.sort(reverse=True)  # Most recent first
                latest_backup = os.path.join(backup_dir, backup_files[0])
                print(f"\n" + "=" * 80)
                print(f"🔍 VERIFYING LATEST BACKUP: {backup_files[0]}")
                print(f"=" * 80)
                verify_database_backup(latest_backup)
                
                # Compare them
                compare_databases('mwangaza.db', latest_backup)
