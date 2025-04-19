import sqlite3

def show_all_users_and_scores():
    conn = sqlite3.connect("scores.db")
    cursor = conn.cursor()

    print("== USERS TABLE ==")
    cursor.execute("SELECT id, username, password, security_question, security_answer FROM users")
    users = cursor.fetchall()
    for user in users:
        user_id, username, password, question, answer = user
        print(f"ID: {user_id} | Username: {username} | Password: {password} | Question: {question} | Answer: {answer}")

    print("\n== SCORES TABLE ==")
    cursor.execute("SELECT id, user_id, map_name, time_taken, collisions, checkpoints FROM scores")
    scores = cursor.fetchall()
    for score in scores:
        print(score)

    conn.close()

if __name__ == "__main__":
    show_all_users_and_scores()
