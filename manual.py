import pygame
import sys
import os
import math
import argparse
import json
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from simulation import drag_and_drop_starting_position, draw_map_button, dropdown_map_selection, select_map
from button import Button


def load_map_metadata(map_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_dir = os.path.join(script_dir, "startfinish")
    base_name = os.path.splitext(os.path.basename(map_path))[0]
    metadata_filename = base_name + "_metadata.json"
    metadata_path = os.path.join(metadata_dir, metadata_filename)
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            return json.load(f)
    return None


def draw_switch_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    img = pygame.image.load("assets/simulate.png")
    scaled_img = pygame.transform.scale(img, (150, 40))
    pos = (10 + 150 // 2, 10 + 40 // 2)
    btn = Button(image=scaled_img, pos=pos, text_input="Auto Mode", font=font,
                 base_color="#d7fcd4", hovering_color="White")
    btn.update(screen)
    return btn.rect


def main():
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

    try:
        display_map = pygame.image.load(global_map_path).convert_alpha()
    except Exception as e:
        print("Error loading map image:", e)
        sys.exit(1)

    metadata = load_map_metadata(global_map_path)
    finish_point = metadata["finish"] if (metadata and "finish" in metadata) else None

    collision_map = pygame.image.load(global_map_path).convert_alpha()
    Lightgreen = (144, 238, 144)
    collision_map.set_colorkey(Lightgreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    # Use drag-and-drop to choose the starting position once.
    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
    initial_starting_position = starting_position.copy()

    car = Car(initial_pos=starting_position.copy())
    car.speed = 0
    car.angle = 0

    collision_count = 0
    start_time = pygame.time.get_ticks()

    acceleration = 0.2
    brake_deceleration = 0.1
    friction = 0.01
    max_speed = 15
    max_reverse_speed = -10
    angular_velocity = 0.0
    turning_acceleration = 0.2
    turning_deceleration = 0.1
    max_turning_rate = 5
    TRACK_WIDTH = 80  # For finish detection

    running = True
    while running:
        screen.fill(Lightgreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()

        # Car controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            car.speed += acceleration
            if car.speed > max_speed:
                car.speed = max_speed
        elif keys[pygame.K_s]:
            if car.speed > 0:
                car.speed -= brake_deceleration
            else:
                car.speed -= acceleration
            if car.speed < max_reverse_speed:
                car.speed = max_reverse_speed
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
        if angular_velocity > max_turning_rate:
            angular_velocity = max_turning_rate
        elif angular_velocity < -max_turning_rate:
            angular_velocity = -max_turning_rate

        car.angle += angular_velocity
        car.update(display_map, collision_mask)

        # Draw the car with radar lines disabled.
        offset_x = car.center[0] - SCREEN_WIDTH // 2
        offset_y = car.center[1] - SCREEN_HEIGHT // 2
        camera_rect = pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        screen.blit(display_map, (0, 0), camera_rect)
        car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        if not car.get_alive():
            collision_count += 1
            msg = info_font.render("Collision! Restarting...", True, (255, 0, 0))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1000)
            car = Car(initial_pos=initial_starting_position.copy())
            car.speed = 0
            car.angle = 0
            angular_velocity = 0.0

        map_button_rect = draw_map_button(screen, info_font)
        switch_button_rect = draw_switch_button(screen, info_font)

        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if map_button_rect.collidepoint(mouse_pos):
                new_map = dropdown_map_selection(screen, info_font)
                if new_map:
                    global_map_path = new_map
                    try:
                        display_map = pygame.image.load(new_map).convert_alpha()
                    except Exception as e:
                        print("Error loading map image:", e)
                        sys.exit(1)
                    collision_map = pygame.image.load(new_map).convert_alpha()
                    collision_map.set_colorkey(Lightgreen)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    metadata = load_map_metadata(new_map)
                    if metadata and "finish" in metadata:
                        finish_point = metadata["finish"]
                    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                    initial_starting_position = starting_position.copy()
                    car = Car(initial_pos=starting_position.copy())
                    car.speed = 0
                    car.angle = 0
                    angular_velocity = 0.0
                    collision_count = 0
                    start_time = pygame.time.get_ticks()
            if switch_button_rect.collidepoint(mouse_pos):
                pygame.quit();
                os.system('python main.py');
                sys.exit()

        if finish_point:
            finish_rect = pygame.Rect(
                finish_point[0] - TRACK_WIDTH // 2,
                finish_point[1] - TRACK_WIDTH // 2,
                TRACK_WIDTH,
                TRACK_WIDTH
            )
            finish_rect_screen = finish_rect.move(-offset_x, -offset_y)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect_screen, 2)
            if finish_rect.collidepoint(car.center):
                total_time = (pygame.time.get_ticks() - start_time) / 1000.0
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill((200, 200, 200))
                screen.blit(overlay, (0, 0))
                finish_msg = f"Finish reached in {total_time:.2f} sec with {collision_count} collisions"
                msg_surface = info_font.render(finish_msg, True, (0, 0, 255))
                screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                retry_img = pygame.image.load("assets/simulate.png")
                retry_img_scaled = pygame.transform.scale(retry_img, (100, 40))
                retry_button = Button(image=retry_img_scaled, pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50),
                                      text_input="Retry", font=info_font,
                                      base_color="#d7fcd4", hovering_color="White")
                retry_button.update(screen)
                map_button_rect = draw_map_button(screen, info_font)
                switch_button_rect = draw_switch_button(screen, info_font)
                pygame.display.flip()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit();
                            sys.exit()
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            pos = event.pos
                            if retry_button.rect.collidepoint(pos):
                                collision_count = 0
                                start_time = pygame.time.get_ticks()
                                car = Car(initial_pos=initial_starting_position.copy())
                                car.speed = 0
                                car.angle = 0
                                angular_velocity = 0.0
                                waiting = False
                            elif map_button_rect.collidepoint(pos):
                                new_map = dropdown_map_selection(screen, info_font)
                                if new_map:
                                    global_map_path = new_map
                                    try:
                                        display_map = pygame.image.load(new_map).convert_alpha()
                                    except Exception as e:
                                        print("Error loading map image:", e)
                                        sys.exit(1)
                                    collision_map = pygame.image.load(new_map).convert_alpha()
                                    collision_map.set_colorkey(Lightgreen)
                                    collision_mask = pygame.mask.from_surface(collision_map)
                                    metadata = load_map_metadata(new_map)
                                    if metadata and "finish" in metadata:
                                        finish_point = metadata["finish"]
                                    starting_position = drag_and_drop_starting_position(screen, info_font,
                                                                                        collision_mask, display_map)
                                    initial_starting_position = starting_position.copy()
                                    car = Car(initial_pos=starting_position.copy())
                                    car.speed = 0
                                    car.angle = 0
                                    angular_velocity = 0.0
                                    collision_count = 0
                                    start_time = pygame.time.get_ticks()
                                    waiting = False
                            elif switch_button_rect.collidepoint(pos):
                                pygame.quit();
                                os.system('python main.py');
                                sys.exit()
                    clock.tick(30)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
