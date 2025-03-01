import pygame
import sys
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from simulation import (
    drag_and_drop_starting_position,
    draw_map_button,
    dropdown_map_selection,
    select_map
)

def draw_switch_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """Draws a button in the top-left corner to switch from manual to automatic mode."""
    button_rect = pygame.Rect(10, 10, 150, 40)
    pygame.draw.rect(screen, (200, 200, 200), button_rect)
    text = font.render("Auto Mode", True, (0, 0, 0))
    screen.blit(text, text.get_rect(center=button_rect.center))
    return button_rect

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Manual Car Control")
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    # Load map and create collision mask.
    global_map_path = select_map(screen, info_font)
    try:
        display_map = pygame.image.load(global_map_path).convert_alpha()
    except Exception as e:
        print("Error loading map image:", e)
        sys.exit(1)
    collision_map = pygame.image.load(global_map_path).convert_alpha()
    WHITE = (255, 255, 255)
    collision_map.set_colorkey(WHITE)
    collision_mask = pygame.mask.from_surface(collision_map)

    # Drag-and-drop starting position.
    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    # Create car.
    car = Car(initial_pos=starting_position.copy())
    car.speed = 0
    car.angle = 0

    # Control parameters.
    acceleration = 0.2
    brake_deceleration = 0.1
    friction = 0.01
    max_speed = 15
    max_reverse_speed = -10
    angular_velocity = 0.0
    turning_acceleration = 0.2
    turning_deceleration = 0.1
    max_turning_rate = 5

    running = True
    while running:
        # Clear screen.
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

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
        print(f"Car Position: {car.pos}, Speed: {car.speed}")
        if not car.get_alive():
            msg = info_font.render("Collision! Restarting...", True, (255, 0, 0))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1000)
            car = Car(initial_pos=starting_position.copy())
            car.speed = 0
            car.angle = 0
            angular_velocity = 0.0

        # Camera logic: center view on the car.
        offset_x = car.center[0] - SCREEN_WIDTH // 2
        offset_y = car.center[1] - SCREEN_HEIGHT // 2
        camera_rect = pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        # (No clamping—this way the camera exactly follows the car.)
        screen.blit(display_map, (0, 0), camera_rect)
        car.draw(screen, info_font, offset=(offset_x, offset_y))
        map_button_rect = draw_map_button(screen, info_font)
        switch_button_rect = draw_switch_button(screen, info_font)

        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if map_button_rect.collidepoint(mouse_pos):
                new_map = dropdown_map_selection(screen, info_font)
                if new_map:
                    global_map_path = new_map
                    try:
                        display_map = pygame.image.load(global_map_path).convert_alpha()
                    except Exception as e:
                        print("Error loading map image:", e)
                        sys.exit(1)
                    collision_map = pygame.image.load(global_map_path).convert_alpha()
                    collision_map.set_colorkey(WHITE)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                    car.pos = starting_position.copy()
                    car.center = [
                        int(car.pos[0] + car.surface.get_width() / 2),
                        int(car.pos[1] + car.surface.get_height() / 2)
                    ]
            if switch_button_rect.collidepoint(mouse_pos):
                pygame.quit()
                os.system('python main.py')
                sys.exit()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
