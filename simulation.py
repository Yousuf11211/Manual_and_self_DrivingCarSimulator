import pygame
import sys
import neat
import os
import json
import math
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT, RADAR_MAX_LENGTH
from typing import List
from button import Button

LightGreen = (144, 238, 144)
Black = (0, 0, 0)
Red = (255, 0, 0)
White = (255, 255, 255)
CONSTANT_SPEED = 5
TRACK_WIDTH = 80  # Track width, used for finish area


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
        return float('inf')

    return sorted(files, key=sort_key)


def load_map_metadata(map_path: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_dir = os.path.join(script_dir, "startfinish")
    base = os.path.splitext(os.path.basename(map_path))[0]
    metadata_filename = base + "_metadata.json"
    metadata_path = os.path.join(metadata_dir, metadata_filename)
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            return json.load(f)
    return None


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
    option_width = 200
    option_height = 35
    option_x = 50
    option_y = 120
    option_spacing = 10
    preview_width = 300
    preview_height = 200
    preview_x = option_x + option_width + 50
    preview_y = option_y
    clock = pygame.time.Clock()
    selecting = True
    while selecting:
        screen.fill(LightGreen)
        title_text = font.render("Select a Map:", True, (0, 0, 0))
        screen.blit(title_text, (option_x, option_y - 50))
        mouse_pos = pygame.mouse.get_pos()
        for i, file in enumerate(get_sorted_map_files()):
            base, _ = os.path.splitext(file)
            label = base.capitalize()
            rect = pygame.Rect(option_x, option_y + i * (option_height + option_spacing), option_width, option_height)
            if rect.collidepoint(mouse_pos):
                selected_index = i
            color = (255, 0, 0) if i == selected_index else (240, 240, 240)
            text_color = White if i == selected_index else Black
            pygame.draw.rect(screen, color, rect, border_radius=8)
            text = font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))
        pygame.draw.rect(screen, Black, (preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10), 2)
        try:
            preview_image = pygame.image.load(
                os.path.join("maps", get_sorted_map_files()[selected_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception:
            pass
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(get_sorted_map_files())
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(get_sorted_map_files())
                elif event.key == pygame.K_RETURN:
                    selecting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(get_sorted_map_files())):
                    rect = pygame.Rect(option_x, option_y + i * (option_height + option_spacing), option_width,
                                       option_height)
                    if rect.collidepoint(event.pos):
                        selected_index = i
                        selecting = False
                        break
        clock.tick(60)
    return os.path.join("maps", get_sorted_map_files()[selected_index])


def draw_map_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    maps_folder = "maps"
    map_files = get_sorted_map_files()
    if hasattr(run_car, "global_map_path") and run_car.global_map_path:
        current_map = os.path.basename(run_car.global_map_path)
    else:
        current_map = map_files[0]
    base, _ = os.path.splitext(current_map)
    label = base.capitalize()
    img = pygame.image.load("assets/simulate.png")
    img = pygame.transform.scale(img, (100, 40))
    btn = Button(image=img, pos=(SCREEN_WIDTH - 60, 30),
                 text_input=label, font=font, base_color="#d7fcd4", hovering_color="White")
    btn.update(screen)
    return btn.rect


def draw_manual_mode_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    img = pygame.image.load("assets/simulate.png")
    img = pygame.transform.scale(img, (150, 40))
    pos = (10 + 150 // 2, 10 + 40 // 2)
    btn = Button(image=img, pos=pos, text_input="Manual Mode",
                 font=font, base_color="#d7fcd4", hovering_color="White")
    btn.update(screen)
    return btn.rect


def dropdown_map_selection(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.");
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.");
        sys.exit(1)
    selected_index = 0
    popup_width = 250
    popup_height = 30 * len(map_files) + 20
    popup_x = SCREEN_WIDTH - popup_width - 20
    popup_y = 60
    option_width = popup_width - 20
    option_height = 30
    option_start_x = popup_x + 10
    option_start_y = popup_y + 10
    preview_width = 300
    preview_height = 200
    preview_x = popup_x - preview_width - 20
    preview_y = popup_y
    clock = pygame.time.Clock()
    active = True
    while active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(screen, (240, 240, 240), popup_rect, border_radius=8)
        pygame.draw.rect(screen, Black, popup_rect, 2, border_radius=8)
        mouse_pos = pygame.mouse.get_pos()
        for i, file in enumerate(map_files):
            base, _ = os.path.splitext(file)
            label = base.capitalize()
            rect = pygame.Rect(option_start_x, option_start_y + i * option_height, option_width, option_height)
            if rect.collidepoint(mouse_pos):
                selected_index = i
            color = (255, 0, 0) if i == selected_index else (240, 240, 240)
            text_color = White if i == selected_index else Black
            pygame.draw.rect(screen, color, rect, border_radius=8)
            text = font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))
        preview_box = pygame.Rect(preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10)
        pygame.draw.rect(screen, Black, preview_box, 2)
        try:
            preview = pygame.image.load(os.path.join(maps_folder, map_files[selected_index])).convert_alpha()
            preview = pygame.transform.scale(preview, (preview_width, preview_height))
            screen.blit(preview, (preview_x, preview_y))
        except:
            pass
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(map_files)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(map_files)
                elif event.key == pygame.K_RETURN:
                    active = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(map_files)):
                    rect = pygame.Rect(option_start_x, option_start_y + i * option_height, option_width, option_height)
                    if rect.collidepoint(event.pos):
                        selected_index = i
                        active = False
                        break
                if not popup_rect.collidepoint(event.pos):
                    active = False
        clock.tick(60)
    return os.path.join(maps_folder, map_files[selected_index])


def drag_and_drop_starting_position(screen: pygame.Surface, info_font: pygame.font.Font,
                                    collision_mask: pygame.mask.Mask, display_map: pygame.Surface) -> List[float]:
    drag_car = Car()
    initial_default = drag_car.pos.copy()
    dragging = False
    valid = False
    message = ""
    clock = pygame.time.Clock()
    while not valid:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                car_rect = pygame.Rect(drag_car.pos[0], drag_car.pos[1], 100, 100)
                if car_rect.collidepoint(mouse_pos):
                    dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                drag_car.update(display_map, collision_mask)
                if drag_car.get_alive() and drag_car.pos != initial_default:
                    valid = True
                else:
                    message = "Please reposition the car on the track!"
            elif event.type == pygame.MOUSEMOTION and dragging:
                new_x = event.pos[0] - 50
                new_y = event.pos[1] - 50
                drag_car.pos[0] = new_x
                drag_car.pos[1] = new_y
                drag_car.center = [int(new_x + drag_car.surface.get_width() / 2),
                                   int(new_y + drag_car.surface.get_height() / 2)]
        screen.blit(display_map, (0, 0))
        drag_car.draw(screen, info_font, draw_radars=False)
        if message:
            msg = info_font.render(message, True, (255, 0, 0))
            screen.blit(msg, (50, 50))
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
    info_font = pygame.font.SysFont("Arial", 30)

    if run_car.global_map_path is None:
        run_car.global_map_path = select_map(screen, info_font)
    try:
        display_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    except Exception as e:
        print(f"Error loading map image: {e}")
        sys.exit(1)
    collision_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    metadata = load_map_metadata(run_car.global_map_path)
    if metadata:
        print("Metadata loaded:", metadata)
    else:
        print("No metadata found.")

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

    generation_start_time = pygame.time.get_ticks()
    simulation_fps = 240
    offset_x, offset_y = 0, 0
    running = True
    finish_reached = False

    while running:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
        remaining_cars = 0
        for index, car in enumerate(cars):
            if car.get_alive():
                radar_data = car.get_data()
                output = nets[index].activate(radar_data)
                max_steering_change = 15
                if not hasattr(car, "angular_velocity"):
                    car.angular_velocity = 0
                desired_turn = output[0] * max_steering_change
                smoothing_turn_factor = 0.1
                car.angular_velocity += smoothing_turn_factor * (desired_turn - car.angular_velocity)
                car.angle += car.angular_velocity
                car.speed = CONSTANT_SPEED
                car.update(display_map, collision_mask)
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
                # In autonomous mode, sensor lines are drawn.
                car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=True)

        manual_button_rect = draw_manual_mode_button(screen, info_font)
        map_button_rect = draw_map_button(screen, info_font)
        mouse_pos = pygame.mouse.get_pos()  # Ensure mouse_pos is always defined.
        if pygame.mouse.get_pressed()[0]:
            if manual_button_rect.collidepoint(mouse_pos):
                pygame.quit();
                os.system('python manual.py');
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
                    collision_map.set_colorkey(LightGreen)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    metadata = load_map_metadata(new_map)
                    if metadata and "finish" in metadata:
                        finish_point = metadata["finish"]
                    run_car.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask,
                                                                                display_map)
                    for car in cars:
                        car.pos = run_car.starting_position.copy()
                        car.center = [int(car.pos[0] + car.surface.get_width() / 2),
                                      int(car.pos[1] + car.surface.get_height() / 2)]
                    remaining_cars = 0
                    generation_start_time = pygame.time.get_ticks()
                    run_car.generation = 0  # Reset generation number on map change.
        if manual_button_rect.collidepoint(mouse_pos):
            pygame.quit();
            os.system('python manual.py');
            sys.exit()

        # Finish detection: draw a blue rectangle at the finish point.
        if metadata and "finish" in metadata:
            finish_point = metadata["finish"]
            finish_rect = pygame.Rect(
                finish_point[0] - TRACK_WIDTH // 2,
                finish_point[1] - TRACK_WIDTH // 2,
                TRACK_WIDTH,
                TRACK_WIDTH
            )
            finish_rect_screen = finish_rect.move(-offset_x, -offset_y)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect_screen, 2)
            for car in cars:
                if car.get_alive() and finish_rect.collidepoint(car.center):
                    finish_time = (pygame.time.get_ticks() - generation_start_time) / 1000.0
                    finish_reached = True
                    running = False
                    break

        if remaining_cars == 0:
            msg = info_font.render("Generation Over", True, (0, 0, 0))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 50))
            pygame.display.flip()
            pygame.time.wait(500)
            break

        pygame.display.flip()
        clock.tick(simulation_fps)

    if finish_reached:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((200, 200, 200))
        screen.blit(overlay, (0, 0))
        message_text = f"Finish reached in Generation {run_car.generation} in {finish_time:.2f} sec"
        msg_surface = info_font.render(message_text, True, (0, 0, 255))
        screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        cont_surface = info_font.render("Click Map button to change map/mode and continue", True, (0, 0, 0))
        screen.blit(cont_surface, (SCREEN_WIDTH // 2 - cont_surface.get_width() // 2, SCREEN_HEIGHT // 2))
        manual_button_rect = draw_manual_mode_button(screen, info_font)
        map_button_rect = draw_map_button(screen, info_font)
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            clock.tick(30)


if __name__ == "__main__":
    run_car()
