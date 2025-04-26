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

    # Table for personal stats (accumulates all plays)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_map_stats (
            user_id INTEGER,
            map_name TEXT,
            times_played INTEGER DEFAULT 0,
            total_collisions INTEGER DEFAULT 0,
            total_time REAL DEFAULT 0.0,
            PRIMARY KEY (user_id, map_name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Table for full score history
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

    # Table for best score per user per map (used in complete leaderboard)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_best_map_scores (
            user_id INTEGER,
            map_name TEXT,
            time_taken REAL,
            PRIMARY KEY (user_id, map_name),
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

    # Insert into scores table (all runs)
    cursor.execute('''
        INSERT INTO scores (user_id, map_name, time_taken, collisions, checkpoints)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, map_name, time_taken, collisions, checkpoints))

    # Update or insert into user_map_stats (for personal leaderboard)
    cursor.execute('''
        INSERT INTO user_map_stats (user_id, map_name, times_played, total_collisions, total_time)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(user_id, map_name) DO UPDATE SET
            times_played = times_played + 1,
            total_collisions = total_collisions + ?,
            total_time = total_time + ?
    ''', (user_id, map_name, collisions, time_taken, collisions, time_taken))

    # Update or insert best score for complete leaderboard
    cursor.execute('''
        SELECT time_taken FROM user_best_map_scores
        WHERE user_id = ? AND map_name = ?
    ''', (user_id, map_name))
    existing = cursor.fetchone()

    if existing is None:
        # No entry yet → insert new best time
        cursor.execute('''
            INSERT INTO user_best_map_scores (user_id, map_name, time_taken)
            VALUES (?, ?, ?)
        ''', (user_id, map_name, time_taken))
    elif time_taken < existing[0]:
        # Better time → update
        cursor.execute('''
            UPDATE user_best_map_scores
            SET time_taken = ?
            WHERE user_id = ? AND map_name = ?
        ''', (time_taken, user_id, map_name))

    conn.commit()
    conn.close()

def get_user_map_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT map_name, times_played, total_collisions, total_time
        FROM user_map_stats
        WHERE user_id = ?
        ORDER BY total_time ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [{
        "map_name": row[0],
        "times_played": row[1],
        "total_collisions": row[2],
        "total_time": round(row[3], 2)
    } for row in rows]


def get_top_scores(limit=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, COUNT(b.map_name) AS maps_cleared, SUM(b.time_taken) AS total_time
        FROM user_best_map_scores b
        JOIN users u ON b.user_id = u.id
        GROUP BY b.user_id
        ORDER BY maps_cleared DESC, total_time ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()

    # Return as list of dictionaries
    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        leaderboard.append({
            "rank": rank,
            "username": row[0],
            "maps_cleared": row[1],
            "total_time": round(row[2], 2)
        })
    return leaderboard

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

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def delete_user_by_username(username):
    if username == "Yousuf":
        print("Cannot delete Admin user.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
        cursor.execute("DELETE FROM scores WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM user_map_stats WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM user_best_map_scores WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

