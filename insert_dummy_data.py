import random
from db import init_db, create_user, get_user, insert_score

# Step 1: Initialize the database
init_db()

# Step 2: Define dummy maps you want to use
maps = [
    "maps/map.png", "maps/map1.png", "maps/map2.png", "maps/map3.png",
    "maps/map4.png"
]

# Step 3: Create 30 users and insert random scores
for i in range(1, 20):  # From DummyUser1 to DummyUser30
    username = f"DummyUser{i}"
    password = f"pass{i}"  # Simple passwords
    question = "Pet's name?"
    answer = f"Fluffy{i}"

    # Create user
    create_user(username, password, question, answer)

    # Get user ID
    user_id = get_user(username, password)

    if user_id:
        # Each user plays 2 to 5 random maps
        num_scores = random.randint(2, 5)

        for _ in range(num_scores):
            map_name = random.choice(maps)
            time_taken = round(random.uniform(5.0, 50.0), 3)  # Random time between 5 and 50 seconds
            collisions = random.randint(0, 10)  # Random collisions between 0 and 3
            checkpoints = random.randint(0, 15)  # Random checkpoint use between 0 and 2

            insert_score(user_id, map_name, time_taken, collisions, checkpoints)

print("✅ 30 Dummy users and their scores added successfully!")
