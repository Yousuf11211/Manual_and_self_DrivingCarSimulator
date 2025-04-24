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

    print("\n== SCORES TABLE (All Runs) ==")
    cursor.execute("SELECT id, user_id, map_name, time_taken, collisions, checkpoints FROM scores")
    scores = cursor.fetchall()
    for score in scores:
        print(f"ScoreID: {score[0]} | UserID: {score[1]} | Map: {score[2]} | Time: {score[3]}s | Collisions: {score[4]} | Checkpoints: {score[5]}")

    print("\n== USER MAP STATS (Personal Leaderboard) ==")
    cursor.execute("SELECT user_id, map_name, times_played, total_collisions, total_time FROM user_map_stats")
    stats = cursor.fetchall()
    for stat in stats:
        print(f"UserID: {stat[0]} | Map: {stat[1]} | Times Played: {stat[2]} | Collisions: {stat[3]} | Total Time: {stat[4]}s")

    print("\n== BEST MAP SCORES (Complete Leaderboard) ==")
    cursor.execute("SELECT user_id, map_name, time_taken FROM user_best_map_scores")
    best = cursor.fetchall()
    for entry in best:
        print(f"UserID: {entry[0]} | Map: {entry[1]} | Best Time: {entry[2]}s")

    conn.close()

if __name__ == "__main__":
    show_all_users_and_scores()
