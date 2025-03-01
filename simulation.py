import pygame
import sys
import neat
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List

WHITE = (255, 255, 255)

def select_map(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = [f for f in os.listdir(maps_folder) if f.endswith('.png')]
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    selected_index = 0
    selecting = True
    while selecting:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(map_files)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(map_files)
                elif event.key == pygame.K_RETURN:
                    selecting = False
        title_text = font.render("Select a Map:", True, (0, 0, 0))
        screen.blit(title_text, (50, 50))
        for i, map_file in enumerate(map_files):
            color = (255, 0, 0) if i == selected_index else (0, 0, 0)
            text = font.render(map_file, True, color)
            screen.blit(text, (50, 100 + i * 30))
        pygame.display.flip()
    return os.path.join(maps_folder, map_files[selected_index])

def draw_map_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
    pygame.draw.rect(screen, (200, 200, 200), button_rect)
    text = font.render("Map", True, (0, 0, 0))
    screen.blit(text, text.get_rect(center=button_rect.center))
    return button_rect

def draw_manual_mode_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    button_rect = pygame.Rect(10, 10, 150, 40)
    pygame.draw.rect(screen, (200, 200, 200), button_rect)
    text = font.render("Manual Mode", True, (0, 0, 0))
    screen.blit(text, text.get_rect(center=button_rect.center))
    return button_rect

def dropdown_map_selection(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = [f for f in os.listdir(maps_folder) if f.endswith('.png')]
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
    item_height = 30
    dropdown_rect = pygame.Rect(button_rect.left, button_rect.bottom, button_rect.width, item_height * len(map_files))
    dropdown_active = True
    selected_map = None
    clock = pygame.time.Clock()
    while dropdown_active:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if dropdown_rect.collidepoint(mouse_pos):
                    index = (mouse_pos[1] - dropdown_rect.top) // item_height
                    if 0 <= index < len(map_files):
                        selected_map = os.path.join(maps_folder, map_files[index])
                        dropdown_active = False
                else:
                    dropdown_active = False
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((50, 50, 50))
        screen.blit(overlay, (0, 0))
        for i, map_file in enumerate(map_files):
            option_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.top + i * item_height, dropdown_rect.width, item_height)
            pygame.draw.rect(screen, (220, 220, 220), option_rect)
            text = font.render(map_file, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=option_rect.center))
        pygame.display.flip()
        clock.tick(60)
    return selected_map

def drag_and_drop_starting_position(screen: pygame.Surface, info_font: pygame.font.Font,
                                    collision_mask: pygame.mask.Mask, display_map: pygame.Surface) -> List[float]:
    drag_car = Car()
    initial_default_position = drag_car.pos.copy()
    dragging = False
    valid_drop = False
    message = ""
    clock = pygame.time.Clock()
    while not valid_drop:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                car_rect = pygame.Rect(drag_car.pos[0], drag_car.pos[1], 100, 100)
                if car_rect.collidepoint(mouse_pos):
                    dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                drag_car.update(display_map, collision_mask)
                if drag_car.get_alive() and drag_car.pos != initial_default_position:
                    valid_drop = True
                else:
                    message = "Please reposition the car on the track!"
            elif event.type == pygame.MOUSEMOTION and dragging:
                new_x = event.pos[0] - 50
                new_y = event.pos[1] - 50
                drag_car.pos[0] = new_x
                drag_car.pos[1] = new_y
                drag_car.center = [
                    int(new_x + drag_car.surface.get_width() / 2),
                    int(new_y + drag_car.surface.get_height() / 2)
                ]
        screen.blit(display_map, (0, 0))
        drag_car.draw(screen, info_font)
        if message:
            msg_text = info_font.render(message, True, (255, 0, 0))
            screen.blit(msg_text, (50, 50))
        pygame.display.flip()
        clock.tick(60)
    return drag_car.pos.copy()

def run_car(genomes, config) -> None:
    if not hasattr(run_car, "global_map_path"):
        run_car.global_map_path = None
    if not hasattr(run_car, "starting_position"):
        run_car.starting_position = None
    if not hasattr(run_car, "generation"):
        run_car.generation = 0

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 70)
    info_font = pygame.font.SysFont("Arial", 30)

    if run_car.global_map_path is None:
        run_car.global_map_path = select_map(screen, info_font)
    try:
        display_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    except Exception as e:
        print(f"Error loading map image: {e}")
        sys.exit(1)
    collision_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    collision_map.set_colorkey(WHITE)
    collision_mask = pygame.mask.from_surface(collision_map)

    if run_car.starting_position is None:
        run_car.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    nets = []
    cars = []
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0
        cars.append(Car(initial_pos=run_car.starting_position.copy()))

    run_car.generation += 1

    # Initialize camera offset variables.
    offset_x, offset_y = 0, 0

    running = True
    while running:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Update sensor data for each car.
        for car in cars:
            if car.get_alive():
                car.update(display_map, collision_mask)

        # Process neural network outputs with smoothing for both speed and turning.
        for index, car in enumerate(cars):
            if car.get_alive():
                output = nets[index].activate(car.get_data())
                max_steering_change = 10

                # Smoothing for turning:
                if not hasattr(car, "angular_velocity"):
                    car.angular_velocity = 0
                desired_turn = output[0] * max_steering_change
                smoothing_turn_factor = 0.1  # adjust for smoother turning (lower = smoother)
                car.angular_velocity += smoothing_turn_factor * (desired_turn - car.angular_velocity)
                car.angle += car.angular_velocity

                # Smoothing for speed:
                throttle_output = output[1]
                min_speed = 10
                max_speed = 15
                desired_speed = min_speed + ((throttle_output + 1) / 2) * (max_speed - min_speed)
                smoothing_speed_factor = 0.1  # adjust for smoother acceleration/deceleration
                car.speed += smoothing_speed_factor * (desired_speed - car.speed)

        remaining_cars = 0
        for i, car in enumerate(cars):
            if car.get_alive():
                remaining_cars += 1
                car.update(display_map, collision_mask)
                genomes[i][1].fitness += car.get_reward()

        if remaining_cars == 0:
            # When no car is alive, display only the map and a message for 500ms.
            end_time = pygame.time.get_ticks() + 500
            while pygame.time.get_ticks() < end_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                screen.fill((255, 255, 255))
                camera_rect = pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
                screen.blit(display_map, (0, 0), camera_rect)
                message = info_font.render("Generation Over", True, (0, 0, 0))
                screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 50))
                pygame.display.flip()
                clock.tick(60)
            running = False

        # Camera logic: center on the average position of alive cars.
        alive_cars = [car for car in cars if car.get_alive()]
        if alive_cars:
            avg_center_x = sum(car.center[0] for car in alive_cars) / len(alive_cars)
            avg_center_y = sum(car.center[1] for car in alive_cars) / len(alive_cars)
            offset_x = int(avg_center_x - SCREEN_WIDTH // 2)
            offset_y = int(avg_center_y - SCREEN_HEIGHT // 2)

        camera_rect = pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        screen.blit(display_map, (0, 0), camera_rect)

        for car in cars:
            if car.get_alive():
                car.draw(screen, info_font, offset=(offset_x, offset_y))

        pygame.display.flip()
        clock.tick(60)
