import sqlite3
import hashlib

DB_PATH = "scores.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            security_question TEXT,
            security_answer TEXT
        )
    ''')

    # Create scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            map_name TEXT,
            time_taken REAL,
            collisions INTEGER,
            checkpoints INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def create_user(username, password=None, question=None, answer=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_pw = hash_text(password) if password else None
    hashed_ans = hash_text(answer) if answer else None
    try:
        cursor.execute(
            "INSERT INTO users (username, password, security_question, security_answer) VALUES (?, ?, ?, ?)",
            (username, hashed_pw, question, hashed_ans)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id



def get_user(username, password=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if password:
        hashed_pw = hash_text(password)  # Use the new general-purpose hasher
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    else:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def verify_security_answer(username, answer):
    hashed_ans = hash_text(answer)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username = ? AND security_answer = ?",
        (username, hashed_ans)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None



def insert_score(user_id, map_name, time_taken, collisions, checkpoints):
    print(">>> INSERTING SCORE INTO DB")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scores (user_id, map_name, time_taken, collisions, checkpoints)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, map_name, time_taken, collisions, checkpoints))
    conn.commit()
    conn.close()

def get_top_scores(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, COUNT(s.map_name) AS maps_cleared, SUM(s.time_taken) AS total_time
        FROM scores s
        JOIN users u ON s.user_id = u.id
        GROUP BY u.id
        ORDER BY maps_cleared DESC, total_time ASC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_user_scores(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT map_name, time_taken, collisions, checkpoints
        FROM scores
        WHERE user_id = ?
        ORDER BY time_taken ASC
    ''', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_user_question(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT security_question FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_user_password(username, new_password):
    hashed_pw = hash_text(new_password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
    conn.commit()
    conn.close()

