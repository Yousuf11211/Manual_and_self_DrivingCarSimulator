import pygame
import sys
import os
import json
import argparse
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import (
    load_map_metadata,
    select_map,
    dropdown_map_selection,
    drag_and_drop_starting_position,
    LightGreen, TRACK_WIDTH,
)
from changecar import change_car, get_car_images, car_scales, load_car

SCORES_DIR = "scores"
os.makedirs(SCORES_DIR, exist_ok=True)

car_images = get_car_images()
car_index = 0

def get_username(screen, font):
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 25, 300, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False
    scroll_offset = 0
    visible_rows = 3  # Show only top 3 by default

    def load_rankings():
        rankings = []
        scores_path = "scores"
        if os.path.exists(scores_path):
            for file in os.listdir(scores_path):
                if file.endswith(".json"):
                    name = os.path.splitext(file)[0]
                    with open(os.path.join(scores_path, file)) as f:
                        data = json.load(f)
                        maps_cleared = len(data)
                        total_time = sum(entry.get("time", 0) for entry in data.values())
                        rankings.append((name, maps_cleared, total_time))
            rankings.sort(key=lambda x: (-x[1], x[2]))
        return rankings

    rankings = load_rankings()

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
                if event.button == 4:  # Scroll up
                    scroll_offset = max(scroll_offset - 1, 0)
                elif event.button == 5:  # Scroll down
                    scroll_offset = min(scroll_offset + 1, max(0, len(rankings) - visible_rows))
            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN and text.strip():
                        return text.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
                if event.key == pygame.K_UP:
                    scroll_offset = max(scroll_offset - 1, 0)
                elif event.key == pygame.K_DOWN:
                    scroll_offset = min(scroll_offset + 1, max(0, len(rankings) - visible_rows))

        screen.fill((30, 30, 30))

        # Leaderboard layout
        board_width, board_height = 600, 150 + visible_rows * 30
        board_x = SCREEN_WIDTH // 2 - board_width // 2
        board_y = SCREEN_HEIGHT // 2 - 180
        leaderboard = pygame.Surface((board_width, board_height), pygame.SRCALPHA)
        leaderboard.fill((0, 0, 0, 180))
        screen.blit(leaderboard, (board_x, board_y))

        title = font.render("Leaderboard", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, board_y + 10))

        col_labels = ["Rank", "Name", "Maps", "Time"]
        col_x = [board_x + 20, board_x + 100, board_x + 320, board_x + 430]
        for i, label in enumerate(col_labels):
            label_surf = font.render(label, True, (200, 200, 200))
            screen.blit(label_surf, (col_x[i], board_y + 50))

        visible_entries = rankings[scroll_offset:scroll_offset + visible_rows]
        for idx, (name, maps, time) in enumerate(visible_entries):
            values = [str(scroll_offset + idx + 1), name, str(maps), f"{time:.2f}s"]
            for i, val in enumerate(values):
                val_surf = font.render(val, True, (255, 255, 255))
                screen.blit(val_surf, (col_x[i], board_y + 85 + idx * 30))

        # Move name input field below the leaderboard
        input_y = board_y + board_height + 40

        prompt = font.render("Enter your name and press Enter:", True, (255, 255, 255))
        screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, input_y))

        input_box.y = input_y + 40
        txt_surface = font.render(text, True, color)
        width = max(300, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 10))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()
        pygame.time.Clock().tick(30)




def save_score(username, map_name, time_taken, collisions, checkpoints):
    user_file = os.path.join(SCORES_DIR, f"{username}.json")

    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            user_scores = json.load(f)
    else:
        user_scores = {}

    map_key = os.path.basename(map_name)
    user_scores[map_key] = {
        "time": round(time_taken, 2),
        "collisions": collisions,
        "checkpoints": checkpoints
    }

    with open(user_file, "w") as f:
        json.dump(user_scores, f, indent=2)

def main(map_path=None, respawn_pos=None):
    global car_index, car_images

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Manual Car Control")
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    username = get_username(screen, info_font)

    if map_path:
        global_map_path = map_path
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('--map_path', type=str, default=None)
        args = parser.parse_args()
        global_map_path = args.map_path if args.map_path else select_map(screen, info_font)

    display_map = pygame.image.load(global_map_path).convert_alpha()
    collision_map = display_map.copy()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)
    metadata = load_map_metadata(global_map_path)
    finish_point = metadata["finish"] if metadata and "finish" in metadata else None

    car_image_name = car_images[car_index]
    car_image_path = os.path.join("cars", car_image_name)
    surface = pygame.image.load(car_image_path).convert_alpha()
    surface = pygame.transform.scale(surface, car_scales.get(car_image_name, (75, 75)))
    selected_surface = surface

    drag_car = Car(initial_pos=[SCREEN_WIDTH//2, SCREEN_HEIGHT//2], surface=selected_surface)

    if respawn_pos:
        starting_position = respawn_pos.copy()
    else:
        starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map, drag_car)

    initial_dragged_position = starting_position.copy()
    current_checkpoint = starting_position.copy()

    car = Car(initial_pos=starting_position.copy(), surface=selected_surface)
    car.update(display_map, collision_mask)
    angular_velocity = 0.0
    collision_count = 0
    checkpoint_used_count = 0
    car_finished = False
    show_retry_button = False
    show_finish_message = False
    finish_msg_surface = None
    start_time = pygame.time.get_ticks()

    button_width, button_height = 160, 40
    spacing, top_margin = 20, 20
    main_menu_btn = pygame.Rect(spacing, top_margin, button_width, button_height)
    modes_btn = pygame.Rect(main_menu_btn.right + spacing, top_margin, button_width, button_height)
    map_btn = pygame.Rect(modes_btn.right + spacing, top_margin, button_width, button_height)
    quit_btn = pygame.Rect(SCREEN_WIDTH - button_width - spacing, top_margin, button_width, button_height)
    change_car_btn = pygame.Rect(quit_btn.left - button_width - spacing, top_margin, button_width, button_height)
    add_checkpoint_btn = pygame.Rect(change_car_btn.left - button_width - spacing, top_margin, button_width, button_height)
    retry_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 20, 140, 40)

    show_modes_dropdown = False
    running = True

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = info_font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    while running:
        screen.fill(LightGreen)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                if main_menu_btn.collidepoint(mx, my):
                    pygame.quit(); os.system("python main.py"); sys.exit()

                elif modes_btn.collidepoint(mx, my):
                    show_modes_dropdown = not show_modes_dropdown

                elif map_btn.collidepoint(mx, my):
                    new_map = dropdown_map_selection(screen, info_font)
                    if new_map:
                        return main(map_path=new_map)

                elif quit_btn.collidepoint(mx, my):
                    pygame.quit(); sys.exit()

                elif change_car_btn.collidepoint(mx, my):
                    car, car_index = change_car(car_images, car_index, current_checkpoint)
                    selected_surface = car.surface
                    angular_velocity = 0.0
                    collision_count = 0
                    start_time = pygame.time.get_ticks()

                elif add_checkpoint_btn.collidepoint(mx, my):
                    current_checkpoint = car.pos.copy()
                    checkpoint_used_count += 1

                elif show_retry_button and retry_btn.collidepoint(mx, my):
                    return main(map_path=global_map_path, respawn_pos=initial_dragged_position)

                elif show_modes_dropdown:
                    dropdown_y = modes_btn.bottom
                    for i, (label, script) in enumerate([
                        ("Self-Driving", "selfdriving.py"),
                        ("Manual", "manual.py"),
                        ("Race", "race.py")
                    ]):
                        rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                        if rect.collidepoint(mx, my):
                            pygame.quit(); os.system(f"python {script}"); sys.exit()
                    show_modes_dropdown = False

        if not car_finished:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                car.speed = min(car.speed + 0.2, 15)
            elif keys[pygame.K_s]:
                car.speed = max(car.speed - 0.2, -10)
            else:
                car.speed -= 0.01 if car.speed > 0 else -0.01 if car.speed < 0 else 0

            if keys[pygame.K_a]:
                angular_velocity += 0.2
            elif keys[pygame.K_d]:
                angular_velocity -= 0.2
            else:
                angular_velocity = max(angular_velocity - 0.1, 0) if angular_velocity > 0 else min(angular_velocity + 0.1, 0)

            angular_velocity = max(-5, min(5, angular_velocity))
            car.angle += angular_velocity

        car.update(display_map, collision_mask)
        offset_x = car.center[0] - SCREEN_WIDTH // 2
        offset_y = car.center[1] - SCREEN_HEIGHT // 2
        screen.blit(display_map, (0, 0), pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))
        car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        if not car.get_alive():
            if not car_finished:
                collision_count += 1
                msg = info_font.render("Collision! Restarting...", True, (255, 0, 0))
                screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(1000)
                car = Car(initial_pos=current_checkpoint.copy(), surface=selected_surface)
                car.speed = 0
                car.angle = 0
                angular_velocity = 0.0
                car.update(display_map, collision_mask)
            else:
                car.speed = 0
                angular_velocity = 0

        if finish_point:
            finish_rect = pygame.Rect(finish_point[0] - TRACK_WIDTH // 2, finish_point[1] - TRACK_WIDTH // 2, TRACK_WIDTH, TRACK_WIDTH)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect.move(-offset_x, -offset_y), 2)
            if not car_finished and finish_rect.collidepoint(car.center):
                total_time = (pygame.time.get_ticks() - start_time) / 1000.0
                car_finished = True
                car.speed = 0
                angular_velocity = 0
                show_finish_message = True
                show_retry_button = True

                save_score(username, global_map_path, total_time, collision_count, checkpoint_used_count)

                msg = f"Finished in {total_time:.2f}s | Collisions: {collision_count} | Checkpoints: {checkpoint_used_count}"
                finish_msg_surface = info_font.render(msg, True, (0, 0, 255))

        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))
        draw_button(change_car_btn, "Cars", change_car_btn.collidepoint(*mouse_pos))
        draw_button(add_checkpoint_btn, "Checkpoint", add_checkpoint_btn.collidepoint(*mouse_pos))
        if show_retry_button:
            draw_button(retry_btn, "Retry", retry_btn.collidepoint(*mouse_pos))

        if show_modes_dropdown:
            dropdown_y = modes_btn.bottom
            for i, mode in enumerate(["Self-Driving", "Manual", "Race"]):
                rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                draw_button(rect, mode, rect.collidepoint(*mouse_pos))

        if show_finish_message and finish_msg_surface:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((200, 200, 200))
            screen.blit(overlay, (0, 0))
            screen.blit(finish_msg_surface, (SCREEN_WIDTH // 2 - finish_msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
