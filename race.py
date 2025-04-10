import pygame
import sys
import os
import neat
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import (
    LightGreen,
    CONSTANT_SPEED,
    TRACK_WIDTH,
    select_map,
    load_map_metadata,
    drag_and_drop_starting_position,
    dropdown_map_selection
)

def load_map_and_mask(map_path):
    map_surface = pygame.image.load(map_path).convert_alpha()
    collision_surface = map_surface.copy()
    collision_surface.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_surface)
    return map_surface, collision_mask

def restart_manual_car(pos):
    car = Car(initial_pos=pos.copy())
    car.speed = 0
    car.angle = 0
    return car

def run_ai_generation(genomes, config, display_map, collision_mask, start_pos):
    nets = []
    cars = []
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0
        cars.append(Car(initial_pos=start_pos.copy()))
    for car in cars:
        car.update(display_map, collision_mask)
    return nets, cars

manual_total_distance = 0

def race():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Race: Manual vs Evolving AI")
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    button_width, button_height = 140, 40
    spacing = 20
    top_margin = 20

    main_menu_btn = pygame.Rect(spacing, top_margin, button_width, button_height)
    modes_btn = pygame.Rect(main_menu_btn.right + spacing, top_margin, button_width, button_height)
    map_btn = pygame.Rect(modes_btn.right + spacing, top_margin, button_width, button_height)
    quit_btn = pygame.Rect(SCREEN_WIDTH - button_width - spacing, top_margin, button_width, button_height)

    show_modes_dropdown = False

    map_path = select_map(screen, info_font)
    display_map, collision_mask = load_map_and_mask(map_path)
    metadata = load_map_metadata(map_path)

    start_pos = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
    manual_car = restart_manual_car(start_pos)
    manual_checkpoint_pos = start_pos.copy()
    manual_angular_velocity = 0.0
    manual_finished = False

    config_path = os.path.join(os.path.dirname(__file__), "config.txt")
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())

    genomes = []
    nets, cars = [], []
    ai_respawn_timer_start = None
    respawning_ai = False
    best_car_finished = False
    best_index = -1

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = info_font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    def start_new_generation():
        nonlocal genomes, nets, cars, ai_respawn_timer_start, respawning_ai
        nonlocal best_car_finished, best_index, manual_checkpoint_pos

        genomes = [(i, genome) for i, genome in enumerate(population.population.values())]
        nets, cars = run_ai_generation(genomes, config, display_map, collision_mask, start_pos)
        ai_respawn_timer_start = None
        respawning_ai = False
        best_car_finished = False
        best_index = -1
        manual_checkpoint_pos = manual_car.pos.copy()

    start_new_generation()

    while True:
        clock.tick(60)
        screen.fill(LightGreen)
        mouse_pos = pygame.mouse.get_pos()

        # --- Events ---
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
                        map_path = new_map
                        display_map, collision_mask = load_map_and_mask(map_path)
                        metadata = load_map_metadata(map_path)
                        start_pos = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                        manual_car = restart_manual_car(start_pos)
                        manual_checkpoint_pos = start_pos.copy()
                        manual_angular_velocity = 0.0
                        manual_finished = False
                        start_new_generation()
                elif quit_btn.collidepoint(mx, my):
                    pygame.quit(); sys.exit()
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

        # --- Manual Car Movement ---
        if not manual_finished:
            keys = pygame.key.get_pressed()
            accel = 0.2
            friction = 0.01
            max_speed = 15
            max_reverse = -10
            turn_accel = 0.2
            turn_decel = 0.1
            max_turn = 5

            if keys[pygame.K_w]:
                manual_car.speed = min(manual_car.speed + accel, max_speed)
            elif keys[pygame.K_s]:
                manual_car.speed = max(manual_car.speed - accel, max_reverse)
            else:
                if manual_car.speed > 0:
                    manual_car.speed -= friction
                elif manual_car.speed < 0:
                    manual_car.speed += friction

            if keys[pygame.K_a]:
                manual_angular_velocity += turn_accel
            elif keys[pygame.K_d]:
                manual_angular_velocity -= turn_accel
            else:
                manual_angular_velocity = max(manual_angular_velocity - turn_decel, 0) if manual_angular_velocity > 0 else min(manual_angular_velocity + turn_decel, 0)

            manual_angular_velocity = max(-max_turn, min(max_turn, manual_angular_velocity))
            manual_car.angle += manual_angular_velocity
            manual_car.update(display_map, collision_mask)

            if not manual_car.get_alive():
                manual_car = restart_manual_car(manual_checkpoint_pos)
                manual_angular_velocity = 0.0

        # --- AI Car Logic ---
        alive_count = 0
        best_fitness = float('-inf')
        for i, car in enumerate(cars):
            if car.get_alive():
                radar_data = car.get_data()
                output = nets[i].activate(radar_data)
                if not hasattr(car, "angular_velocity"):
                    car.angular_velocity = 0
                desired = output[0] * 15
                car.angular_velocity += 0.1 * (desired - car.angular_velocity)
                car.angle += car.angular_velocity
                if not best_car_finished:
                    car.speed = CONSTANT_SPEED
                car.update(display_map, collision_mask)

                reward = car.get_reward() + car.distance * 0.05
                if radar_data[0] > 0.2:
                    reward += 0.1
                if abs(car.angular_velocity) < 3:
                    reward += 0.2
                genomes[i][1].fitness += reward

                if genomes[i][1].fitness > best_fitness:
                    best_fitness = genomes[i][1].fitness
                    best_index = i

                alive_count += 1

        if alive_count == 0 and not respawning_ai:
            ai_respawn_timer_start = pygame.time.get_ticks()
            respawning_ai = True

        if respawning_ai and pygame.time.get_ticks() - ai_respawn_timer_start >= 3000:
            population.run(lambda g, c: None, 1)  # advance NEAT generation
            start_new_generation()

        # --- Camera ---
        offset_x = manual_car.center[0] - SCREEN_WIDTH // 2
        offset_y = manual_car.center[1] - SCREEN_HEIGHT // 2
        screen.blit(display_map, (0, 0), pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))

        manual_car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)
        best_car = None
        if best_index != -1 and cars[best_index].get_alive():
            best_car = cars[best_index]
            best_car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        # --- Finish Line ---
        if metadata and "finish" in metadata:
            fx, fy = metadata["finish"]
            finish_rect = pygame.Rect(fx - TRACK_WIDTH // 2, fy - TRACK_WIDTH // 2, TRACK_WIDTH, TRACK_WIDTH)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect.move(-offset_x, -offset_y), 2)

            if not manual_finished and finish_rect.collidepoint(manual_car.center):
                manual_finished = True
                manual_car.speed = 0

            if best_car and not best_car_finished and finish_rect.collidepoint(best_car.center):
                best_car_finished = True
                best_car.speed = 0

        # --- Leaderboard ---
        leaderboard = []
        if best_car or respawning_ai:
            label = "AI Car"
            if best_car_finished:
                label += " (Finished)"
            elif respawning_ai:
                seconds_left = 3 - ((pygame.time.get_ticks() - ai_respawn_timer_start) // 1000)
                label += f" (Respawning in {seconds_left}s)"
            leaderboard.append((label, best_car.distance if best_car else 0))
        label = "Manual Car (Finished)" if manual_finished else "Manual Car"
        leaderboard.append((label, manual_car.distance))
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        line_height = 40
        box_width = 300
        box_height = line_height * len(leaderboard) + 20
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = 15
        pygame.draw.rect(screen, (0, 0, 0), (box_x - 10, box_y - 10, box_width + 20, box_height), border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), (box_x - 8, box_y - 8, box_width + 16, box_height - 4), border_radius=8)

        for i, (label, distance) in enumerate(leaderboard):
            text = info_font.render(f"{i + 1}. {label} - {distance:.0f} px", True, (0, 0, 0))
            screen.blit(text, (box_x, box_y + i * line_height))

        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))

        if show_modes_dropdown:
            dropdown_y = modes_btn.bottom
            for i, mode in enumerate(["Self-Driving", "Manual", "Race"]):
                rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                draw_button(rect, mode, rect.collidepoint(*mouse_pos))

        pygame.display.flip()

if __name__ == "__main__":
    race()
