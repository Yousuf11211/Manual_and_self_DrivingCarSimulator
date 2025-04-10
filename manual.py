import pygame
import sys
import os
import argparse
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from button import Button
from utils import (
    load_map_metadata,
    select_map,
    dropdown_map_selection,
    drag_and_drop_starting_position,
    LightGreen, Black, Red, White, CONSTANT_SPEED, TRACK_WIDTH,
)
from changecar import change_car, get_car_images, car_scales, load_car

# Car image and scaling configuration
car_images = get_car_images()
car_index = 0

def main():
    global car_index, car_images

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Manual Car Control")
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    parser = argparse.ArgumentParser(description="Manual Car Simulation")
    parser.add_argument('--map_path', type=str, default=None, help="Path to the map file")
    args = parser.parse_args()

    if args.map_path:
        global_map_path = args.map_path
    else:
        global_map_path = select_map(screen, info_font)

    display_map = pygame.image.load(global_map_path).convert_alpha()
    metadata = load_map_metadata(global_map_path)
    finish_point = metadata["finish"] if metadata and "finish" in metadata else None

    collision_map = pygame.image.load(global_map_path).convert_alpha()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    # Load initial car surface (first selected car)
    car_image_name = car_images[car_index]
    car_image_path = os.path.join("cars", car_image_name)
    surface = pygame.image.load(car_image_path).convert_alpha()
    scale_size = car_scales.get(car_image_name, (75, 75))
    surface = pygame.transform.scale(surface, scale_size)
    selected_surface = surface  # persist globally

    # Use selected car for drag preview
    drag_car = Car(initial_pos=[SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT // 2 - 30], surface=surface)
    drag_car.center = [int(drag_car.pos[0] + drag_car.surface.get_width() / 2),
                       int(drag_car.pos[1] + drag_car.surface.get_height() / 2)]

    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map, drag_car)
    initial_starting_position = starting_position.copy()

    car = Car(initial_pos=starting_position.copy(), surface=selected_surface)
    car.speed = 0
    car.angle = 0
    angular_velocity = 0.0

    collision_count = 0
    start_time = pygame.time.get_ticks()

    # motion parameters
    acceleration = 0.2
    brake_deceleration = 0.1
    friction = 0.01
    max_speed = 15
    max_reverse_speed = -10
    turning_acceleration = 0.2
    turning_deceleration = 0.1
    max_turning_rate = 5

    # top buttons
    button_width, button_height = 140, 40
    spacing = 20
    top_margin = 20

    main_menu_btn = pygame.Rect(spacing, top_margin, button_width, button_height)
    modes_btn = pygame.Rect(main_menu_btn.right + spacing, top_margin, button_width, button_height)
    map_btn = pygame.Rect(modes_btn.right + spacing, top_margin, button_width, button_height)
    quit_btn = pygame.Rect(SCREEN_WIDTH - button_width - spacing, top_margin, button_width, button_height)
    change_car_btn = pygame.Rect(quit_btn.left - button_width - spacing, top_margin, button_width, button_height)

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
                        global_map_path = new_map
                        display_map = pygame.image.load(new_map).convert_alpha()
                        collision_map = pygame.image.load(new_map).convert_alpha()
                        collision_map.set_colorkey(LightGreen)
                        collision_mask = pygame.mask.from_surface(collision_map)
                        metadata = load_map_metadata(new_map)
                        if metadata and "finish" in metadata:
                            finish_point = metadata["finish"]

                        # Reload current car surface
                        car_image_name = car_images[car_index]
                        car_image_path = os.path.join("cars", car_image_name)
                        surface = pygame.image.load(car_image_path).convert_alpha()
                        scale_size = car_scales.get(car_image_name, (75, 75))
                        surface = pygame.transform.scale(surface, scale_size)
                        selected_surface = surface  # update globally

                        drag_car = Car(initial_pos=[SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT // 2 - 30], surface=surface)
                        drag_car.center = [int(drag_car.pos[0] + drag_car.surface.get_width() / 2),
                                           int(drag_car.pos[1] + drag_car.surface.get_height() / 2)]

                        starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask,
                                                                            display_map, drag_car)
                        initial_starting_position = starting_position.copy()

                        car = Car(initial_pos=starting_position.copy(), surface=selected_surface)
                        car.speed = 0
                        car.angle = 0
                        angular_velocity = 0.0
                        collision_count = 0
                        start_time = pygame.time.get_ticks()

                elif quit_btn.collidepoint(mx, my):
                    pygame.quit(); sys.exit()

                elif change_car_btn.collidepoint(mx, my):
                    car, car_index = change_car(car_images, car_index, starting_position)
                    selected_surface = car.surface  #  update selected_surface to the newly changed car
                    angular_velocity = 0.0
                    collision_count = 0
                    start_time = pygame.time.get_ticks()

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

        # car movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            car.speed = min(car.speed + acceleration, max_speed)
        elif keys[pygame.K_s]:
            if car.speed > 0:
                car.speed -= brake_deceleration
            else:
                car.speed -= acceleration
            car.speed = max(car.speed, max_reverse_speed)
        else:
            if car.speed > 0:
                car.speed = max(car.speed - friction, 0)
            elif car.speed < 0:
                car.speed = min(car.speed + friction, 0)

        if keys[pygame.K_a]:
            angular_velocity += turning_acceleration
        elif keys[pygame.K_d]:
            angular_velocity -= turning_acceleration
        else:
            if angular_velocity > 0:
                angular_velocity = max(angular_velocity - turning_deceleration, 0)
            elif angular_velocity < 0:
                angular_velocity = min(angular_velocity + turning_deceleration, 0)
        angular_velocity = max(-max_turning_rate, min(max_turning_rate, angular_velocity))

        car.angle += angular_velocity
        car.update(display_map, collision_mask)

        offset_x = car.center[0] - SCREEN_WIDTH // 2
        offset_y = car.center[1] - SCREEN_HEIGHT // 2
        screen.blit(display_map, (0, 0), pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))
        car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        # crash and reset
        if not car.get_alive():
            collision_count += 1
            msg = info_font.render("Collision! Restarting...", True, (255, 0, 0))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1000)
            car = Car(initial_pos=initial_starting_position.copy(), surface=selected_surface)
            car.speed = 0
            car.angle = 0
            angular_velocity = 0.0

        # draw UI
        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))
        draw_button(change_car_btn, "Change Car", change_car_btn.collidepoint(*mouse_pos))

        if show_modes_dropdown:
            dropdown_y = modes_btn.bottom
            for i, mode in enumerate(["Self-Driving", "Manual", "Race"]):
                rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                draw_button(rect, mode, rect.collidepoint(*mouse_pos))

        # finish line check
        if finish_point:
            finish_rect = pygame.Rect(
                finish_point[0] - TRACK_WIDTH // 2,
                finish_point[1] - TRACK_WIDTH // 2,
                TRACK_WIDTH, TRACK_WIDTH
            )
            pygame.draw.rect(screen, (0, 0, 255), finish_rect.move(-offset_x, -offset_y), 2)
            if finish_rect.collidepoint(car.center):
                total_time = (pygame.time.get_ticks() - start_time) / 1000.0
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill((200, 200, 200))
                screen.blit(overlay, (0, 0))
                finish_msg = f"Finish reached in {total_time:.2f} sec with {collision_count} collisions"
                msg_surface = info_font.render(finish_msg, True, (0, 0, 255))
                screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
