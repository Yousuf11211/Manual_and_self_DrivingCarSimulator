import pygame
import sys
import neat
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT, RADAR_MAX_LENGTH
from typing import List

WHITE = (255, 255, 255)
CONSTANT_SPEED = 5  # Constant speed for all cars


def get_sorted_map_files() -> List[str]:
    maps_folder = "maps"
    files = [f for f in os.listdir(maps_folder) if f.endswith('.png')]

    def sort_key(filename: str):
        base, _ = os.path.splitext(filename)
        if base == "map":
            return 0
        elif base.startswith("map"):
            try:
                return int(base[3:])
            except:
                return float('inf')
        else:
            return float('inf')

    return sorted(files, key=sort_key)


def select_map(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    selected_index = 0

    # Preview box dimensions and position (to the right of the list)
    preview_width = 300
    preview_height = 200
    preview_x = 250  # list is drawn starting at x=50; preview appears at x=250
    preview_y = 100

    selecting = True
    while selecting:
        screen.fill(WHITE)
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
        # Draw the selection list.
        for i, map_file in enumerate(map_files):
            base, _ = os.path.splitext(map_file)
            label = base.capitalize()  # e.g., "Map", "Map1", "Map2"
            color = (255, 0, 0) if i == selected_index else (0, 0, 0)
            text = font.render(label, True, color)
            screen.blit(text, (50, 100 + i * 30))

        # Draw preview box border.
        pygame.draw.rect(screen, (0, 0, 0), (preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10), 2)
        # Load and display preview image.
        try:
            preview_image = pygame.image.load(os.path.join(maps_folder, map_files[selected_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception as e:
            pass

        pygame.display.flip()
    return os.path.join(maps_folder, map_files[selected_index])


def draw_map_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """Draw a button that displays the current map's label in the top-right corner."""
    button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
    pygame.draw.rect(screen, (200, 200, 200), button_rect)
    maps_folder = "maps"
    map_files = get_sorted_map_files()
    if hasattr(run_car, "global_map_path") and run_car.global_map_path:
        current_map = os.path.basename(run_car.global_map_path)
    else:
        current_map = map_files[0]
    base, _ = os.path.splitext(current_map)
    label = base.capitalize()
    text = font.render(label, True, (0, 0, 0))
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
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)

    button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
    item_height = 30
    dropdown_rect = pygame.Rect(button_rect.left, button_rect.bottom, button_rect.width, item_height * len(map_files))

    # For dropdown, we want the preview to appear to the left of the dropdown list.
    preview_width = 300
    preview_height = 200
    preview_x = dropdown_rect.left - preview_width - 20  # preview on left side of list
    preview_y = dropdown_rect.top

    dropdown_active = True
    selected_map = None
    clock = pygame.time.Clock()
    while dropdown_active:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
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
        # Draw dropdown options.
        for i, map_file in enumerate(map_files):
            base, _ = os.path.splitext(map_file)
            label = base.capitalize()
            option_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.top + i * item_height, dropdown_rect.width,
                                      item_height)
            pygame.draw.rect(screen, (220, 220, 220), option_rect)
            text = font.render(label, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=option_rect.center))

        # Draw preview box to the left of the dropdown list.
        pygame.draw.rect(screen, (0, 0, 0), (preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10), 2)
        # Determine which option is hovered over for preview.
        mouse_pos = pygame.mouse.get_pos()
        selected_index = 0
        if dropdown_rect.collidepoint(mouse_pos):
            selected_index = (mouse_pos[1] - dropdown_rect.top) // item_height
            if selected_index >= len(map_files):
                selected_index = len(map_files) - 1
        try:
            preview_image = pygame.image.load(os.path.join(maps_folder, map_files[selected_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception as e:
            pass

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
        screen.fill(WHITE)
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

    for car in cars:
        car.update(display_map, collision_mask)

    run_car.generation += 1

    simulation_fps = 240  # Higher FPS for faster simulation
    offset_x, offset_y = 0, 0
    running = True
    while running:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        remaining_cars = 0
        for index, car in enumerate(cars):
            if car.get_alive():
                radar_data = car.get_data()  # 7 sensor distances + constant speed (1.0)
                output = nets[index].activate(radar_data)

                # --- Smooth Steering ---
                max_steering_change = 15
                if not hasattr(car, "angular_velocity"):
                    car.angular_velocity = 0
                desired_turn = output[0] * max_steering_change
                smoothing_turn_factor = 0.1
                car.angular_velocity += smoothing_turn_factor * (desired_turn - car.angular_velocity)
                car.angle += car.angular_velocity

                # --- Constant Speed ---
                car.speed = CONSTANT_SPEED

                car.update(display_map, collision_mask)

                # --- Enhanced Fitness Calculation ---
                fitness_boost = car.get_reward() + (car.distance * 0.05)
                if radar_data[0] > 50:
                    fitness_boost += 0.1
                if abs(car.angular_velocity) < 3:
                    fitness_boost += 0.2
                genomes[index][1].fitness += fitness_boost

                remaining_cars += 1

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

        manual_button_rect = draw_manual_mode_button(screen, info_font)
        map_button_rect = draw_map_button(screen, info_font)
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if manual_button_rect.collidepoint(mouse_pos):
                pygame.quit()
                os.system('python manual.py')
                sys.exit()
            elif map_button_rect.collidepoint(mouse_pos):
                new_map = dropdown_map_selection(screen, info_font)
                if new_map:
                    run_car.global_map_path = new_map
                    try:
                        display_map = pygame.image.load(new_map).convert_alpha()
                    except Exception as e:
                        print("Error loading map:", e)
                        sys.exit(1)
                    collision_map = pygame.image.load(new_map).convert_alpha()
                    collision_map.set_colorkey(WHITE)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    run_car.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask,
                                                                                display_map)
                    for car in cars:
                        car.pos = run_car.starting_position.copy()
                        car.center = [int(car.pos[0] + car.surface.get_width() / 2),
                                      int(car.pos[1] + car.surface.get_height() / 2)]

        if remaining_cars == 0:
            message = info_font.render("Generation Over", True, (0, 0, 0))
            screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 50))
            pygame.display.flip()
            pygame.time.wait(500)
            break

        pygame.display.flip()
        clock.tick(simulation_fps)
