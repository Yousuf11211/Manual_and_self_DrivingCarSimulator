import pygame
import sys
import neat
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import (
    load_map_metadata,
    select_map,
    dropdown_map_selection,
    drag_and_drop_starting_position,
    LightGreen, Black, CONSTANT_SPEED, TRACK_WIDTH
)

# this function runs each generation of NEAT
def run_auto_mode(genomes, config):
    # store map and start position across generations
    if not hasattr(run_auto_mode, "global_map_path"):
        run_auto_mode.global_map_path = None
    if not hasattr(run_auto_mode, "starting_position"):
        run_auto_mode.starting_position = None
    if not hasattr(run_auto_mode, "generation"):
        run_auto_mode.generation = 0
    if not hasattr(run_auto_mode, "last_gen_crashed"):
        run_auto_mode.last_gen_crashed = False

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Self-Driving Mode")
    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    # Show transition screen if last generation crashed
    if run_auto_mode.last_gen_crashed:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(LightGreen)
        screen.blit(overlay, (0, 0))
        msg = info_font.render("All cars crashed. Starting next generation...", True, (0, 0, 0))
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        pygame.display.flip()
        pygame.time.wait(1500)
        run_auto_mode.last_gen_crashed = False

    # buttons at the top
    button_width, button_height = 140, 40
    spacing = 20
    top_margin = 20
    main_menu_btn = pygame.Rect(spacing, top_margin, button_width, button_height)
    modes_btn = pygame.Rect(main_menu_btn.right + spacing, top_margin, button_width, button_height)
    map_btn = pygame.Rect(modes_btn.right + spacing, top_margin, button_width, button_height)
    quit_btn = pygame.Rect(SCREEN_WIDTH - button_width - spacing, top_margin, button_width, button_height)

    show_modes_dropdown = False
    simulation_paused = False

    # load map if not already chosen
    if run_auto_mode.global_map_path is None:
        run_auto_mode.global_map_path = select_map(screen, info_font)

    display_map = pygame.image.load(run_auto_mode.global_map_path).convert_alpha()
    collision_map = display_map.copy()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)
    metadata = load_map_metadata(run_auto_mode.global_map_path)

    # pick starting point if not chosen
    if run_auto_mode.starting_position is None:
        run_auto_mode.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    # create cars and neural networks
    nets, cars = [], []
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0
        cars.append(Car(initial_pos=run_auto_mode.starting_position.copy()))

    for car in cars:
        car.update(display_map, collision_mask)

    # Force initial screen render before entering main loop
    screen.fill(LightGreen)
    screen.blit(display_map, (0, 0))
    pygame.display.flip()

    run_auto_mode.generation += 1
    print(f"Running Generation {run_auto_mode.generation}")
    generation_start_time = pygame.time.get_ticks()
    simulation_fps = 240
    offset_x, offset_y = 0, 0

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = info_font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    while True:
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
                        run_auto_mode.global_map_path = new_map
                        display_map = pygame.image.load(new_map).convert_alpha()
                        collision_map = display_map.copy()
                        collision_map.set_colorkey(LightGreen)
                        collision_mask = pygame.mask.from_surface(collision_map)
                        metadata = load_map_metadata(new_map)
                        run_auto_mode.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                        nets.clear()
                        cars.clear()
                        for _, genome in genomes:
                            net = neat.nn.FeedForwardNetwork.create(genome, config)
                            nets.append(net)
                            genome.fitness = 0
                            cars.append(Car(initial_pos=run_auto_mode.starting_position.copy()))
                        for car in cars:
                            car.update(display_map, collision_mask)
                        run_auto_mode.generation = 0
                        simulation_paused = False
                        generation_start_time = pygame.time.get_ticks()
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

        if not simulation_paused:
            remaining_cars = 0
            for i, car in enumerate(cars):
                if car.get_alive():
                    radar_data = car.get_data()
                    if len(radar_data) != 8:
                        continue
                    output = nets[i].activate(radar_data)
                    if not hasattr(car, "angular_velocity"):
                        car.angular_velocity = 0
                    desired = output[0] * 15
                    car.angular_velocity += 0.1 * (desired - car.angular_velocity)
                    car.angle += car.angular_velocity
                    car.speed = CONSTANT_SPEED
                    car.update(display_map, collision_mask)

                    fitness = car.get_reward() + car.distance * 0.1
                    if radar_data[0] > 50:
                        fitness += 0.1
                    if abs(car.angular_velocity) < 3:
                        fitness += 0.2
                    genomes[i][1].fitness += fitness
                    remaining_cars += 1

            if metadata and "finish" in metadata:
                fx, fy = metadata["finish"]
                finish_rect = pygame.Rect(fx - TRACK_WIDTH // 2, fy - TRACK_WIDTH // 2, TRACK_WIDTH, TRACK_WIDTH)
                for car in cars:
                    if car.get_alive() and finish_rect.collidepoint(car.center):
                        time_taken = (pygame.time.get_ticks() - generation_start_time) / 1000.0
                        simulation_paused = True
                        print(f"✅ Finish reached in {time_taken:.2f} seconds.")
                        break

            if remaining_cars == 0:
                print("⚠️ All cars crashed. Moving to next generation...")
                run_auto_mode.last_gen_crashed = True
                break

        alive = [car for car in cars if car.get_alive()]
        if alive:
            avg_x = sum(car.center[0] for car in alive) / len(alive)
            avg_y = sum(car.center[1] for car in alive) / len(alive)
            offset_x = int(avg_x - SCREEN_WIDTH // 2)
            offset_y = int(avg_y - SCREEN_HEIGHT // 2)

        screen.blit(display_map, (0, 0), pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))
        for car in cars:
            if car.get_alive():
                car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=True)

        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))

        if show_modes_dropdown:
            dropdown_y = modes_btn.bottom
            for i, mode in enumerate(["Self-Driving", "Manual", "Race"]):
                rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                draw_button(rect, mode, rect.collidepoint(*mouse_pos))

        if simulation_paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((240, 240, 240))
            screen.blit(overlay, (0, 0))
            msg = info_font.render("✅ Car reached the finish line!", True, (0, 0, 255))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        pygame.display.flip()
        clock.tick(simulation_fps)


# this starts the program from command line
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NEAT Self-Driving Car Simulation")
    parser.add_argument('--generations', type=int, default=1000)
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), "config.txt")
    if not os.path.exists(config_path):
        print("Error: config.txt not found")
        sys.exit(1)

    config = neat.config.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path
    )

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    population.run(run_auto_mode, args.generations)
