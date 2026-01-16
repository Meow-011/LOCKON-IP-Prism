import sqlite3
from sqlite3 import Error
import os
from datetime import datetime

DB_FILE = "ip_prism.db"

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
    return conn

def setup_database():
    """ สร้างและอัปเดตตารางที่จำเป็น (Database Migration) """
    conn = create_connection()
    if conn is None: return
    
    try:
        cursor = conn.cursor()
        
        # --- FIX: Create tables FIRST, then alter them. ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_timestamp TEXT NOT NULL,
                file_name TEXT NOT NULL,
                description TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL UNIQUE,
                country TEXT,
                is_malicious BOOLEAN,
                fraud_score INTEGER,
                isp TEXT,
                organization TEXT,
                otx_pulses INTEGER,
                tags TEXT,
                notes TEXT,
                last_api_check TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_ip_link (
                batch_id INTEGER,
                ip_id INTEGER,
                PRIMARY KEY (batch_id, ip_id),
                FOREIGN KEY (batch_id) REFERENCES import_batches (id) ON DELETE CASCADE,
                FOREIGN KEY (ip_id) REFERENCES ip_records (id)
            );
        """)

        # --- Now, perform migrations on the existing tables ---
        cursor.execute("PRAGMA table_info(ip_records)")
        columns = [col['name'] for col in cursor.fetchall()]
        
        if 'abuse_score' in columns and 'fraud_score' not in columns:
            cursor.execute("ALTER TABLE ip_records RENAME COLUMN abuse_score TO fraud_score")
        if 'isp' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN isp TEXT")
        if 'organization' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN organization TEXT")
        if 'tags' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN tags TEXT")
        if 'notes' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN notes TEXT")
        if 'otx_pulses' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN otx_pulses INTEGER")
        if 'last_api_check' not in columns: cursor.execute("ALTER TABLE ip_records ADD COLUMN last_api_check TEXT")

        conn.commit()
    except Error as e:
        print(f"Database setup/migration error: {e}")
    finally:
        if conn:
            conn.close()

# ... (rest of the file is the same as the correct version) ...

def get_dashboard_stats():
    conn = create_connection()
    stats = {
        "total_ips": 0, "total_batches": 0, "top_country": "N/A", "last_analysis": "N/A"
    }
    if not conn: return stats
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) AS count FROM ip_records")
        total_ips_result = cursor.fetchone()
        if total_ips_result and total_ips_result['count'] is not None:
            stats["total_ips"] = total_ips_result['count']
        cursor.execute("SELECT COUNT(id) AS count FROM import_batches")
        total_batches_result = cursor.fetchone()
        if total_batches_result and total_batches_result['count'] is not None:
            stats["total_batches"] = total_batches_result['count']
        cursor.execute("""
            SELECT country FROM ip_records 
            WHERE is_malicious = 1 AND country IS NOT NULL AND country != 'N/A'
            GROUP BY country ORDER BY COUNT(id) DESC LIMIT 1
        """)
        top_country_result = cursor.fetchone()
        if top_country_result and top_country_result['country'] is not None:
            stats["top_country"] = top_country_result['country']
        cursor.execute("SELECT import_timestamp FROM import_batches ORDER BY id DESC LIMIT 1")
        last_analysis_result = cursor.fetchone()
        if last_analysis_result and last_analysis_result['import_timestamp']:
            stats["last_analysis"] = last_analysis_result['import_timestamp'].split('T')[0]
    except Error as e:
        print(f"Error getting dashboard stats: {e}")
    finally:
        if conn:
            conn.close()
    return stats

def add_import_batch(timestamp, file_name, description):
    conn = create_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO import_batches (import_timestamp, file_name, description) VALUES (?, ?, ?)", (timestamp, file_name, description))
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"Error adding import batch: {e}")
        return None
    finally:
        if conn:
            conn.close()

def find_ip_details(ip_address):
    conn = create_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ip_records WHERE ip_address = ?", (ip_address,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error finding IP details: {e}")
        return None
    finally:
        if conn:
            conn.close()

def find_ip_details_bulk(ip_addresses):
    if not ip_addresses:
        return []
    conn = create_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        placeholders = ',' . join('?' for _ in ip_addresses)
        query = f"SELECT * FROM ip_records WHERE ip_address IN ({placeholders})"
        cursor.execute(query, ip_addresses)
        return cursor.fetchall()
    except Error as e:
        print(f"Error finding IP details in bulk: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_ip_record(ip, country, malicious, score, isp, org, pulses):
    conn = create_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO ip_records (ip_address, country, is_malicious, fraud_score, isp, organization, otx_pulses, last_api_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ip, country, malicious, score, isp, org, pulses, current_time))
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        if "UNIQUE constraint failed" not in str(e): print(f"Error adding IP record for {ip}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_ip_record_details(ip_id, country, malicious, score, isp, org, pulses):
    conn = create_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute("""
            UPDATE ip_records 
            SET country = ?, is_malicious = ?, fraud_score = ?, isp = ?, organization = ?, otx_pulses = ?, last_api_check = ?
            WHERE id = ?
        """, (country, malicious, score, isp, org, pulses, current_time, ip_id))
        conn.commit()
    except Error as e:
        print(f"Error updating IP record for ip_id {ip_id}: {e}")
    finally:
        if conn:
            conn.close()

def link_ip_to_batch(ip_id, batch_id):
    conn = create_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO batch_ip_link (ip_id, batch_id) VALUES (?, ?)", (ip_id, batch_id))
        conn.commit()
    except Error as e:
        print(f"Error linking ip_id {ip_id} to batch_id {batch_id}: {e}")
    finally:
        if conn:
            conn.close()

def get_or_create_ip_id(ip_address):
    conn = create_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ip_records WHERE ip_address = ?", (ip_address,))
        result = cursor.fetchone()
        if result:
            return result['id']
        cursor.execute("INSERT INTO ip_records (ip_address) VALUES (?)", (ip_address,))
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        if "UNIQUE constraint failed" in str(e):
            try:
                conn.rollback()
                cursor.execute("SELECT id FROM ip_records WHERE ip_address = ?", (ip_address,))
                result = cursor.fetchone()
                if result:
                    return result['id']
            except Error as e2:
                print(f"Error in get_or_create_ip_id recovery for {ip_address}: {e2}")
                return None
        print(f"Error in get_or_create_ip_id for {ip_address}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_batches():
    conn = create_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, description, file_name FROM import_batches ORDER BY id DESC")
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting all batches: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_ips_by_batch_ids(batch_ids):
    conn = create_connection()
    if conn is None: return []
    if not batch_ids: 
        query = "SELECT * FROM ip_records ORDER BY fraud_score DESC, otx_pulses DESC"
        params = []
    else:
        placeholders = ','.join('?' for _ in batch_ids)
        query = f"""
            SELECT r.* FROM ip_records r
            JOIN batch_ip_link l ON r.id = l.ip_id
            WHERE l.batch_id IN ({placeholders})
            ORDER BY r.fraud_score DESC, r.otx_pulses DESC
        """
        params = batch_ids
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting IPs by batch IDs: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_ip_details(ip_id, tags, notes):
    conn = create_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE ip_records SET tags = ?, notes = ? WHERE id = ?", (tags, notes, ip_id))
        conn.commit()
    except Error as e:
        print(f"Error updating details for ip_id {ip_id}: {e}")
    finally:
        if conn:
            conn.close()