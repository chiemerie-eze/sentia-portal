import sqlite3
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "history.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# PASSWORD SECURITY
# =========================
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    if not stored_password:
        return False

    # Backward compatibility for old plaintext test accounts
    if not stored_password.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(stored_password, provided_password)

    try:
        _, iterations, salt_hex, hash_hex = stored_password.split("$", 3)
        iterations = int(iterations)
        salt = bytes.fromhex(salt_hex)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            provided_password.encode("utf-8"),
            salt,
            iterations
        ).hex()

        return hmac.compare_digest(new_hash, hash_hex)
    except Exception:
        return False


# =========================
# DATABASE INIT / MIGRATION
# =========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_time TEXT,
            original_filename TEXT,
            saved_result_path TEXT,
            benign_count INTEGER,
            suspicious_count INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            is_verified INTEGER DEFAULT 0,
            verification_code TEXT,
            reset_code TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT,
            email TEXT,
            event_type TEXT,
            status TEXT,
            reason TEXT,
            source_ip TEXT
        )
    """)

    # Safe schema migration for older DBs
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "reset_code" not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_code TEXT")

    conn.commit()
    conn.close()


# =========================
# SCAN HISTORY
# =========================
def save_scan_record(original_filename, saved_result_path, benign_count, suspicious_count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scan_history (
            scan_time,
            original_filename,
            saved_result_path,
            benign_count,
            suspicious_count
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        original_filename,
        str(saved_result_path),
        int(benign_count),
        int(suspicious_count)
    ))
    conn.commit()
    conn.close()


def get_scan_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, scan_time, original_filename, saved_result_path, benign_count, suspicious_count
        FROM scan_history
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# =========================
# AUTH AUDIT LOG
# =========================
def log_auth_event(email, event_type, status, reason="", source_ip="local_streamlit"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO auth_audit_log (
            event_time,
            email,
            event_type,
            status,
            reason,
            source_ip
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        email,
        event_type,
        status,
        reason,
        source_ip
    ))
    conn.commit()
    conn.close()


def get_auth_audit_log(limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, event_time, email, event_type, status, reason, source_ip
        FROM auth_audit_log
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def count_recent_failed_logins(email, window_minutes=10):
    conn = get_connection()
    cursor = conn.cursor()

    since_time = (datetime.now() - timedelta(minutes=window_minutes)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT COUNT(*)
        FROM auth_audit_log
        WHERE email = ?
          AND event_type = 'login'
          AND status = 'failed'
          AND event_time >= ?
    """, (email, since_time))

    count = cursor.fetchone()[0]
    conn.close()
    return count


def is_account_locked(email, threshold=5, window_minutes=10):
    failed_count = count_recent_failed_logins(email, window_minutes)
    return failed_count >= threshold, failed_count


# =========================
# USERS
# =========================
def create_user(full_name, email, password, verification_code):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO users (full_name, email, password, verification_code, is_verified, reset_code)
            VALUES (?, ?, ?, ?, 0, NULL)
        """, (full_name, email, hashed_password, verification_code))
        conn.commit()
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def verify_user(email, code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ? AND verification_code = ? AND is_verified = 0
    """, (email, code))
    user = cursor.fetchone()

    if user:
        cursor.execute("""
            UPDATE users
            SET is_verified = 1,
                verification_code = NULL
            WHERE email = ?
        """, (email,))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def update_verification_code(email, verification_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET verification_code = ?
        WHERE email = ? AND is_verified = 0
    """, (verification_code, email))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0


def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, email, password
        FROM users
        WHERE email = ? AND is_verified = 1
    """, (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    user_id, full_name, user_email, stored_password = user

    if verify_password(stored_password, password):
        # Upgrade old plaintext test accounts to hashed passwords on successful login
        if not stored_password.startswith("pbkdf2_sha256$"):
            new_hash = hash_password(password)
            cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (new_hash, user_id))
            conn.commit()

        conn.close()
        return (user_id, full_name, user_email)

    conn.close()
    return None


def user_exists_unverified(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email
        FROM users
        WHERE email = ? AND is_verified = 0
    """, (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def user_exists_verified(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email
        FROM users
        WHERE email = ? AND is_verified = 1
    """, (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def get_user_full_name_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name
        FROM users
        WHERE email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Customer"


def set_reset_code(email, reset_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET reset_code = ?
        WHERE email = ? AND is_verified = 1
    """, (reset_code, email))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0


def verify_reset_code(email, code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ? AND reset_code = ? AND is_verified = 1
    """, (email, code))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def update_password(email, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    new_hashed_password = hash_password(new_password)

    cursor.execute("""
        UPDATE users
        SET password = ?, reset_code = NULL
        WHERE email = ? AND is_verified = 1
    """, (new_hashed_password, email))

    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0