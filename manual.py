from db import init_db, insert_score
import pygame
import sys
import os
import argparse
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import (
    load_map_metadata,
    select_map,
    dropdown_map_selection,
    drag_and_drop_starting_position,
    LightGreen, TRACK_WIDTH,
)
from changecar import change_car, get_car_images, car_scales
from db import get_top_scores, get_user_map_stats


car_images = get_car_images()
car_index = 0

def save_score(user_id, map_name, time_taken, collisions, checkpoints):
    if user_id:
        insert_score(user_id, map_name, time_taken, collisions, checkpoints)

def main(map_path=None, respawn_pos=None, user_id=None, username="Guest", is_admin=False):
    init_db()
    global car_index, car_images
    print(">>> USER ID:", user_id, "USERNAME:", username)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    admin_status = "Admin" if is_admin else "Not Admin"
    pygame.display.set_caption(f"Manual Car Control | User: {username} | {admin_status}")

    background = pygame.image.load("assets/login.png").convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_x, bg_y = 0, 0

    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

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

    drag_car = Car(initial_pos=[SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2], surface=selected_surface)

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
    logout_btn = pygame.Rect(change_car_btn.left - button_width - spacing, top_margin, button_width, button_height)
    add_checkpoint_btn = pygame.Rect(logout_btn.left - button_width - spacing, top_margin, button_width, button_height)
    retry_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 20, 140, 40)

    show_modes_dropdown = False
    show_logout_prompt = False
    running = True
    leaderboard_button = pygame.Rect(add_checkpoint_btn.left - button_width - spacing, top_margin, button_width,
                                     button_height)
    show_leaderboard_dropdown = False
    show_leaderboard = False
    leaderboard_mode = "complete"  # or "personal"
    personal_scores = get_user_map_stats(user_id) if user_id else []

    leaderboard_data = get_top_scores(limit=100)
    if user_id:
        personal_scores = get_user_map_stats(user_id)

    scroll_offset = 0

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = info_font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_close_button(rect, hover=False):
        color = (200, 0, 0) if hover else (150, 0, 0)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        x_font = pygame.font.SysFont("Arial", 28, bold=True)
        label = x_font.render("X", True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_leaderboard(screen, data, scroll_offset):
        box_width = 600
        rows_visible = min(5, len(data))
        spacing_y = 30
        header_height = 90
        box_height = header_height + rows_visible * spacing_y + 20
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        box = pygame.Rect(box_x, box_y, box_width, box_height)

        # Draw rounded shadow
        shadow = pygame.Surface((box_width + 10, box_height + 10), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 0))  # Transparent background
        pygame.draw.rect(shadow, (0, 0, 0, 100), shadow.get_rect(), border_radius=15)
        screen.blit(shadow, (box_x - 5, box_y - 5))

        # Translucent background
        overlay = pygame.Surface((box_width, box_height))
        overlay.set_alpha(180)
        overlay.fill((240, 240, 240))
        screen.blit(overlay, (box_x, box_y))

        pygame.draw.rect(screen, (0, 0, 0), box, 2, border_radius=10)
        close_btn = pygame.Rect(box.right - 40, box.y + 10, 30, 30)
        draw_close_button(close_btn, close_btn.collidepoint(mouse_pos))

        # Title
        title = info_font.render("Leaderboard", True, (0, 0, 0))
        screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 10))

        # Table headers
        headers = ["Rank", "Name", "Maps", "Time"]
        col_widths = [80, 200, 100, 100]
        col_x = [box.x + 20, box.x + 100, box.x + 330, box.x + 450]
        header_y = box.y + 50

        for i, header in enumerate(headers):
            header_text = info_font.render(header, True, (0, 0, 0))
            screen.blit(header_text, (col_x[i], header_y))

        spacing_y = 35  # instead of 30
        start_y = header_y + 40
        end_index = min(len(data), scroll_offset + 5)

        for i, entry in enumerate(data[scroll_offset:end_index], start=scroll_offset):
            row_y = start_y + (i - scroll_offset) * spacing_y
            row_rect = pygame.Rect(box.x + 10, row_y - 5, box_width - 20, spacing_y)

            # Draw highlight
            if entry["rank"] == 1:
                color_bg = (255, 215, 0, 100)
            elif entry["rank"] == 2:
                color_bg = (173, 216, 230, 200)
            elif entry["rank"] == 3:
                color_bg = (205, 127, 50, 100)
            else:
                color_bg = None

            if color_bg:
                highlight = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                highlight.fill(color_bg)
                screen.blit(highlight, (row_rect.x, row_rect.y))

        for i, entry in enumerate(data[scroll_offset:end_index], start=scroll_offset):
            row_y = start_y + (i - scroll_offset) * spacing_y
            row_rect = pygame.Rect(box.x + 10, row_y - 5, box_width - 20, spacing_y)

            color = (0, 0, 0)
            if entry["username"] == username:
                color = (0, 102, 204)

            font_height = info_font.get_height()
            center_y = row_rect.centery - font_height // 2

            screen.blit(info_font.render(f"{entry['rank']}", True, color), (col_x[0], center_y))
            screen.blit(info_font.render(f"{entry['username']}", True, color), (col_x[1], center_y))
            screen.blit(info_font.render(f"{entry['maps_cleared']}", True, color), (col_x[2], center_y))
            screen.blit(info_font.render(f"{entry['total_time']}s", True, color), (col_x[3], center_y))

    def draw_personal_leaderboard(screen, data, scroll_offset):
        box_width = 700
        rows_visible = min(5, len(data))
        spacing_y = 30
        header_height = 90
        box_height = header_height + rows_visible * spacing_y + 20
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        box = pygame.Rect(box_x, box_y, box_width, box_height)

        # --- Step 1: Shadow behind box ---
        shadow = pygame.Surface((box_width + 10, box_height + 10), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 0))  # Transparent background
        pygame.draw.rect(shadow, (0, 0, 0, 100), shadow.get_rect(), border_radius=15)
        screen.blit(shadow, (box_x - 5, box_y - 5))

        # --- Step 2: Translucent rounded background ---
        overlay = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        overlay.fill((240, 240, 240, 180))  # Light gray translucent
        pygame.draw.rect(overlay, (240, 240, 240, 180), overlay.get_rect(), border_radius=10)
        screen.blit(overlay, (box_x, box_y))

        # --- Step 3: Rounded black border ---
        pygame.draw.rect(screen, (0, 0, 0), box, 2, border_radius=10)

        # --- Step 4: Close button ---
        close_btn = pygame.Rect(box.right - 40, box.y + 10, 30, 30)
        draw_close_button(close_btn, close_btn.collidepoint(mouse_pos))

        # --- Step 5: Title ---
        title = info_font.render("Personal Stats", True, (0, 0, 0))
        screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 10))

        # --- Step 6: Table headers ---
        headers = ["Map", "Times", "Collisions", "Total Time"]
        col_x = [box.x + 20, box.x + 250, box.x + 400, box.x + 560]
        header_y = box.y + 50

        for i, header in enumerate(headers):
            header_text = info_font.render(header, True, (0, 0, 0))
            screen.blit(header_text, (col_x[i], header_y))

        # --- Step 7: Row backgrounds ---
        start_y = header_y + 40
        end_index = min(len(data), scroll_offset + 5)

        for i, entry in enumerate(data[scroll_offset:end_index], start=scroll_offset):
            row_y = start_y + (i - scroll_offset) * spacing_y
            row_rect = pygame.Rect(box.x + 10, row_y - 5, box_width - 20, spacing_y)

            highlight = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            highlight.fill((220, 220, 220, 100))  # Light gray transparent
            screen.blit(highlight, (row_rect.x, row_rect.y))

        # --- Step 8: Row text ---
        for i, entry in enumerate(data[scroll_offset:end_index], start=scroll_offset):
            row_y = start_y + (i - scroll_offset) * spacing_y

            text_offset_y = 5  # small adjustment for perfect vertical centering

            map_name_clean = entry["map_name"].replace("maps/", "").replace("maps\\", "").replace(".png", "")
            screen.blit(info_font.render(map_name_clean, True, (0, 0, 0)), (col_x[0], row_y + text_offset_y))
            screen.blit(info_font.render(str(entry["times_played"]), True, (0, 0, 0)),
                        (col_x[1], row_y + text_offset_y))
            screen.blit(info_font.render(str(entry["total_collisions"]), True, (0, 0, 0)),
                        (col_x[2], row_y + text_offset_y))
            screen.blit(info_font.render(f"{entry['total_time']}s", True, (0, 0, 0)),
                        (col_x[3], row_y + text_offset_y))

    while running:
        screen.fill(LightGreen)
        mouse_pos = pygame.mouse.get_pos()
        yes_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 10, 100, 40)
        no_btn = pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 10, 100, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle scrolling with keyboard arrows
            if event.type == pygame.KEYDOWN and show_leaderboard:
                if leaderboard_mode == "complete":
                    data_length = len(leaderboard_data)
                elif leaderboard_mode == "personal":
                    data_length = len(personal_scores)
                else:
                    data_length = 0

                if event.key == pygame.K_UP:
                    scroll_offset = max(scroll_offset - 1, 0)
                elif event.key == pygame.K_DOWN:
                    scroll_offset = min(scroll_offset + 1, max(0, data_length - 5))

            # Handle scrolling with mouse wheel
            if event.type == pygame.MOUSEWHEEL and show_leaderboard:
                if leaderboard_mode == "complete":
                    data_length = len(leaderboard_data)
                elif leaderboard_mode == "personal":
                    data_length = len(personal_scores)
                else:
                    data_length = 0

                if event.y > 0:  # Scrolling up
                    scroll_offset = max(scroll_offset - 1, 0)
                elif event.y < 0:  # Scrolling down
                    scroll_offset = min(scroll_offset + 1, max(0, data_length - 5))

            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # Handle leaderboard close button
                if show_leaderboard:
                    if leaderboard_mode == "complete":
                        box_width = 600
                        rows_visible = min(5, len(leaderboard_data))
                    elif leaderboard_mode == "personal":
                        box_width = 700
                        rows_visible = min(5, len(personal_scores))
                    spacing_y = 30
                    header_height = 90
                    box_height = header_height + rows_visible * spacing_y + 20
                    box_x = (SCREEN_WIDTH - box_width) // 2
                    box_y = (SCREEN_HEIGHT - box_height) // 2

                    close_btn = pygame.Rect(box_x + box_width - 40, box_y + 10, 30, 30)

                    if close_btn.collidepoint(mx, my):
                        show_leaderboard = False
                        continue

                # Handle logout confirmation
                if show_logout_prompt:
                    yes_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 10, 100, 40)
                    no_rect = pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 10, 100, 40)

                    if yes_rect.collidepoint(mx, my):
                        pygame.quit()
                        os.system("python main.py")
                        return
                    elif no_rect.collidepoint(mx, my):
                        show_logout_prompt = False
                    continue

                # Handle top buttons
                if main_menu_btn.collidepoint(mx, my):
                    pygame.quit()
                    from main import main_menu
                    main_menu(user_id=user_id, username=username, is_admin=is_admin)

                elif modes_btn.collidepoint(mx, my):
                    show_modes_dropdown = not show_modes_dropdown

                elif leaderboard_button.collidepoint(mx, my):
                    show_leaderboard_dropdown = not show_leaderboard_dropdown
                    print("Clicked leaderboard, show_leaderboard_dropdown:", show_leaderboard_dropdown)

                elif map_btn.collidepoint(mx, my):
                    new_map = dropdown_map_selection(screen, info_font)
                    if new_map:
                        # Reload map
                        global_map_path = new_map
                        display_map = pygame.image.load(global_map_path).convert_alpha()
                        collision_map = display_map.copy()
                        collision_map.set_colorkey(LightGreen)
                        collision_mask = pygame.mask.from_surface(collision_map)
                        metadata = load_map_metadata(global_map_path)
                        finish_point = metadata["finish"] if metadata and "finish" in metadata else None
                        drag_car = Car(initial_pos=[SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2], surface=selected_surface)
                        starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask,
                                                                            display_map, drag_car)
                        current_checkpoint = starting_position.copy()
                        initial_dragged_position = starting_position.copy()
                        car = Car(initial_pos=starting_position.copy(), surface=selected_surface)
                        car.update(display_map, collision_mask)
                        collision_count = 0
                        checkpoint_used_count = 0
                        car_finished = False
                        show_retry_button = False
                        show_finish_message = False
                        finish_msg_surface = None
                        start_time = pygame.time.get_ticks()

                elif quit_btn.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

                elif logout_btn.collidepoint(mx, my):
                    show_logout_prompt = True

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
                    car = Car(initial_pos=initial_dragged_position.copy(), surface=selected_surface)
                    car.update(display_map, collision_mask)
                    current_checkpoint = initial_dragged_position.copy()
                    start_time = pygame.time.get_ticks()
                    collision_count = 0
                    checkpoint_used_count = 0
                    car_finished = False
                    show_retry_button = False
                    show_finish_message = False

                elif show_modes_dropdown:
                    dropdown_y = modes_btn.bottom
                    for i, label in enumerate(["Self-Driving", "Manual", "Race"]):
                        rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                        if rect.collidepoint(mx, my):
                            pygame.display.quit()
                            import main
                            if label == "Self-Driving":
                                main.run_selected_mode("auto", user_id=user_id, username=username, is_admin=is_admin)
                            elif label == "Manual":
                                main.run_selected_mode("manual", user_id=user_id, username=username, is_admin=is_admin)
                            elif label == "Race":
                                main.run_selected_mode("race", user_id=user_id, username=username, is_admin=is_admin)
                            return
                    show_modes_dropdown = False

                if show_leaderboard_dropdown:
                    for rect, label in dropdown_rects:
                        if rect.collidepoint(mx, my):
                            leaderboard_mode = label.lower()
                            scroll_offset = 0  # Reset scroll
                            show_leaderboard = True
                            show_leaderboard_dropdown = False

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
                angular_velocity = max(angular_velocity - 0.1, 0) if angular_velocity > 0 else min(
                    angular_velocity + 0.1, 0)

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
            finish_rect = pygame.Rect(finish_point[0] - TRACK_WIDTH // 2, finish_point[1] - TRACK_WIDTH // 2,
                                      TRACK_WIDTH, TRACK_WIDTH)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect.move(-offset_x, -offset_y), 2)
            if not car_finished and finish_rect.collidepoint(car.center):
                total_time = (pygame.time.get_ticks() - start_time) / 1000.0
                car_finished = True
                car.speed = 0
                angular_velocity = 0
                show_finish_message = True
                show_retry_button = True
                print(">>> Saving score for user_id:", user_id)
                save_score(user_id, global_map_path, total_time, collision_count, checkpoint_used_count)

                # Refresh leaderboards
                leaderboard_data = get_top_scores(limit=100)
                if user_id:
                    personal_scores = get_user_map_stats(user_id)  # ⭐ ADD THIS ⭐

                msg = f"Finished in {total_time:.2f}s | Collisions: {collision_count} | Checkpoints: {checkpoint_used_count}"
                finish_msg_surface = info_font.render(msg, True, (0, 0, 255))

        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(leaderboard_button, "Leaderboard", leaderboard_button.collidepoint(*mouse_pos))
        draw_button(logout_btn, "Logout", logout_btn.collidepoint(*mouse_pos))
        draw_button(change_car_btn, "Cars", change_car_btn.collidepoint(*mouse_pos))
        draw_button(add_checkpoint_btn, "Checkpoint", add_checkpoint_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))
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
            screen.blit(finish_msg_surface,
                        (SCREEN_WIDTH // 2 - finish_msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        # DRAWING dropdown buttons and saving them for click detection
        dropdown_rects = []  # Clear dropdown rect list every frame

        if show_leaderboard_dropdown:
            dropdown_y = leaderboard_button.bottom
            button_spacing = 5  # Optional spacing
            for i, label in enumerate(["Complete", "Personal"]):
                rect = pygame.Rect(
                    leaderboard_button.left,
                    dropdown_y + i * (button_height + button_spacing),
                    button_width,
                    button_height
                )
                draw_button(rect, label, rect.collidepoint(mouse_pos))
                dropdown_rects.append((rect, label))  # Save rect + label for use during event handling

        if show_logout_prompt:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            confirm_box = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 180)
            pygame.draw.rect(screen, (255, 255, 255), confirm_box)
            pygame.draw.rect(screen, (0, 0, 0), confirm_box, 2)
            prompt_text = info_font.render("Are you sure you want to logout?", True, (0, 0, 0))
            screen.blit(prompt_text, (confirm_box.centerx - prompt_text.get_width() // 2, confirm_box.y + 30))
            draw_button(yes_btn, "Yes", yes_btn.collidepoint(*mouse_pos))
            draw_button(no_btn, "No", no_btn.collidepoint(*mouse_pos))

        if show_leaderboard:
            if leaderboard_mode == "complete":
                draw_leaderboard(screen, leaderboard_data, scroll_offset)
            elif leaderboard_mode == "personal":
                personal_scores = sorted(personal_scores, key=lambda x: x["map_name"])  # ⭐ Sort here
                draw_personal_leaderboard(screen, personal_scores, scroll_offset)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def run_manual(map_path=None, respawn_pos=None, user_id=None, username="Guest", is_admin=False):
    main(map_path, respawn_pos, user_id, username, is_admin)
