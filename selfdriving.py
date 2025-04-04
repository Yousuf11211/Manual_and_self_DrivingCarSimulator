import pygame
import sys
import neat
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT, RADAR_MAX_LENGTH
from utils import (
    load_map_metadata,
    select_map,
    draw_map_button,
    draw_manual_mode_button,
    dropdown_map_selection,
    drag_and_drop_starting_position,
    LightGreen, Black, CONSTANT_SPEED, TRACK_WIDTH
)

def run_auto_mode(genomes, config) -> None:
    # Set global variables to allow map changes between generations.
    if not hasattr(run_auto_mode, "global_map_path"):
        run_auto_mode.global_map_path = None
    if not hasattr(run_auto_mode, "starting_position"):
        run_auto_mode.starting_position = None
    if not hasattr(run_auto_mode, "generation"):
        run_auto_mode.generation = 0

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    # Select a map if one hasn’t been chosen yet.
    if run_auto_mode.global_map_path is None:
        run_auto_mode.global_map_path = select_map(screen, info_font)
    try:
        display_map = pygame.image.load(run_auto_mode.global_map_path).convert_alpha()
    except Exception as e:
        print(f"Error loading map image: {e}")
        sys.exit(1)
    collision_map = pygame.image.load(run_auto_mode.global_map_path).convert_alpha()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    metadata = load_map_metadata(run_auto_mode.global_map_path)
    if metadata:
        print("Metadata loaded:", metadata)
    else:
        print("No metadata found.")

    if run_auto_mode.starting_position is None:
        run_auto_mode.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    nets = []
    cars = []
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0
        cars.append(Car(initial_pos=run_auto_mode.starting_position.copy()))
    for car in cars:
        car.update(display_map, collision_mask)
    run_auto_mode.generation += 1

    generation_start_time = pygame.time.get_ticks()
    simulation_fps = 240
    offset_x, offset_y = 0, 0
    running = True
    finish_reached = False

    while running:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

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
                car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=True)

        manual_button_rect = draw_manual_mode_button(screen, info_font)
        map_button_rect = draw_map_button(screen, info_font)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if manual_button_rect.collidepoint(mouse_pos):
                pygame.quit()
                os.system('python manual.py')
                sys.exit()
            elif map_button_rect.collidepoint(mouse_pos):
                new_map = dropdown_map_selection(screen, info_font)
                if new_map:
                    run_auto_mode.global_map_path = new_map
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
                    run_auto_mode.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                    for car in cars:
                        car.pos = run_auto_mode.starting_position.copy()
                        car.center = [int(car.pos[0] + car.surface.get_width() / 2),
                                      int(car.pos[1] + car.surface.get_height() / 2)]
                    remaining_cars = 0
                    generation_start_time = pygame.time.get_ticks()
                    run_auto_mode.generation = 0  # Reset generation count on map change.

        if manual_button_rect.collidepoint(mouse_pos):
            pygame.quit()
            os.system('python manual.py')
            sys.exit()

        # Draw finish detection if metadata is available.
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
            msg = info_font.render("Generation Over", True, Black)
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
        message_text = f"Finish reached in Generation {run_auto_mode.generation} in {finish_time:.2f} sec"
        msg_surface = info_font.render(message_text, True, (0, 0, 255))
        screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        cont_surface = info_font.render("Click Map button to change map/mode and continue", True, Black)
        screen.blit(cont_surface, (SCREEN_WIDTH // 2 - cont_surface.get_width() // 2, SCREEN_HEIGHT // 2))
        manual_button_rect = draw_manual_mode_button(screen, info_font)
        map_button_rect = draw_map_button(screen, info_font)
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            clock.tick(30)

if __name__ == "__main__":
    # NEAT configuration and population setup.
    import argparse
    parser = argparse.ArgumentParser(description="NEAT Self-Driving Car Simulation")
    parser.add_argument('--generations', type=int, default=1000, help="Number of generations to run")
    args = parser.parse_args()

    project_folder = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_folder, 'config.txt')
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)

    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # Run the NEAT algorithm using the autonomous simulation mode.
    population.run(run_auto_mode, args.generations)
