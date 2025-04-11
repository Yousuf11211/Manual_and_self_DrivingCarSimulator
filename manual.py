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
from changecar import change_car, get_car_images, car_scales, load_car

car_images = get_car_images()
car_index = 0

def main(map_path=None, respawn_pos=None):
    global car_index, car_images

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Manual Car Control")
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

    # Top Buttons
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

        # Car Control
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
