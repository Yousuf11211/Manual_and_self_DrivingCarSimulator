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


def run_ai_generation(genomes, config, display_map, collision_mask, start_pos, ai_car_surface):
    nets = []
    cars = []
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0
        cars.append(Car(initial_pos=start_pos.copy(), surface=ai_car_surface))
    for car in cars:
        car.update(display_map, collision_mask)
    return nets, cars


def race(user_id=None, username="Guest", is_admin=False):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    admin_status = "Admin" if is_admin else "Not Admin"
    pygame.display.set_caption(f"Race: Manual vs Evolving AI | User: {username} | {admin_status}")

    ai_car_surface = pygame.image.load(os.path.join("cars", "car7.png")).convert_alpha()
    ai_car_surface = pygame.transform.scale(ai_car_surface, (75, 75))

    manual_car_surface = pygame.image.load(os.path.join("cars", "car.png")).convert_alpha()
    manual_car_surface = pygame.transform.scale(manual_car_surface, (75, 75))

    clock = pygame.time.Clock()
    info_font = pygame.font.SysFont("Arial", 30)

    # Button definitions
    button_width, button_height = 140, 40
    spacing = 20
    top_margin = 20

    main_menu_btn = pygame.Rect(spacing, top_margin, button_width, button_height)
    modes_btn = pygame.Rect(main_menu_btn.right + spacing, top_margin, button_width, button_height)
    map_btn = pygame.Rect(modes_btn.right + spacing, top_margin, button_width, button_height)
    quit_btn = pygame.Rect(SCREEN_WIDTH - button_width - spacing, top_margin, button_width, button_height)
    logout_btn = pygame.Rect(quit_btn.left - button_width - spacing, top_margin, button_width, button_height)

    show_logout_prompt = False
    show_modes_dropdown = False

    # Initialize map and AI
    map_path = select_map(screen, info_font)
    display_map, collision_mask = load_map_and_mask(map_path)
    metadata = load_map_metadata(map_path)

    start_pos = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
    manual_car = restart_manual_car(start_pos)
    manual_angular_velocity = 0.0
    manual_finished = False

    # NEAT configuration
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

    # AI and race state variables
    genomes = []
    nets, cars = [], []
    best_car_finished = False
    best_index = -1
    first_finisher = None
    finish_time = None
    final_popup_shown = False
    result_order = []

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = info_font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    def show_popup(message, screen, font):
        popup = font.render(message, True, (255, 255, 255))
        padding = 20
        text_rect = popup.get_rect()
        bg_width = text_rect.width + padding * 2
        bg_height = text_rect.height + padding
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        bg_surface.blit(popup, (padding, padding // 2))
        screen.blit(bg_surface, ((SCREEN_WIDTH - bg_width) // 2, 10))

    def start_new_generation():
        nonlocal genomes, nets, cars, best_car_finished, best_index
        genomes = [(i, genome) for i, genome in enumerate(population.population.values())]
        nets, cars = run_ai_generation(genomes, config, display_map, collision_mask, start_pos, ai_car_surface)
        best_car_finished = False
        best_index = -1

    start_new_generation()

    while True:
        clock.tick(60)
        screen.fill(LightGreen)
        mouse_pos = pygame.mouse.get_pos()
        yes_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 10, 100, 40)
        no_btn = pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 10, 100, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                if show_logout_prompt:
                    if yes_btn.collidepoint(mx, my):
                        pygame.quit()
                        os.system("python main.py")
                        return
                    elif no_btn.collidepoint(mx, my):
                        show_logout_prompt = False
                else:
                    if main_menu_btn.collidepoint(mx, my):
                        from main import main_menu
                        pygame.quit()
                        main_menu(user_id=user_id, username=username, is_admin=is_admin)


                    elif modes_btn.collidepoint(mx, my):
                        show_modes_dropdown = not show_modes_dropdown

                    elif logout_btn.collidepoint(mx, my):
                        show_logout_prompt = True

                    elif map_btn.collidepoint(mx, my):
                        new_map = dropdown_map_selection(screen, info_font)
                        if new_map:
                            map_path = new_map
                            display_map, collision_mask = load_map_and_mask(map_path)
                            metadata = load_map_metadata(map_path)
                            start_pos = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                            manual_car = restart_manual_car(start_pos)
                            manual_angular_velocity = 0.0
                            manual_finished = False
                            first_finisher = None
                            finish_time = None
                            final_popup_shown = False
                            result_order = []
                            start_new_generation()

                    elif quit_btn.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()

                    elif show_modes_dropdown:
                        dropdown_y = modes_btn.bottom
                        for i, label in enumerate(["Self-Driving", "Manual", "Race"]):
                            rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width,
                                               button_height)
                            if rect.collidepoint(mx, my):
                                pygame.display.quit()  # ❗ Only close the Pygame display, not the whole program
                                import main
                                if label == "Self-Driving":
                                    main.run_selected_mode("auto", user_id=user_id, username=username,
                                                           is_admin=is_admin)
                                elif label == "Manual":
                                    main.run_selected_mode("manual", user_id=user_id, username=username,
                                                           is_admin=is_admin)
                                elif label == "Race":
                                    main.run_selected_mode("race", user_id=user_id, username=username,
                                                           is_admin=is_admin)
                                return  # ❗ Do not use sys.exit()
                        show_modes_dropdown = False

        # Manual car controls
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
                manual_angular_velocity = max(manual_angular_velocity - turn_decel,
                                              0) if manual_angular_velocity > 0 else min(
                    manual_angular_velocity + turn_decel, 0)

            manual_angular_velocity = max(-max_turn, min(max_turn, manual_angular_velocity))
            manual_car.angle += manual_angular_velocity
            manual_car.update(display_map, collision_mask)

            if not manual_car.get_alive():
                manual_car = restart_manual_car(start_pos)
                manual_angular_velocity = 0.0

        # AI car logic
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

        if alive_count == 0:
            population.run(lambda g, c: None, 1)
            start_new_generation()

        # Camera positioning
        offset_x = manual_car.center[0] - SCREEN_WIDTH // 2
        offset_y = manual_car.center[1] - SCREEN_HEIGHT // 2
        screen.blit(display_map, (0, 0), pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Draw cars
        manual_car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)
        best_car = None
        if best_index != -1 and cars[best_index].get_alive():
            best_car = cars[best_index]
            best_car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        # Finish line logic
        if metadata and "finish" in metadata:
            fx, fy = metadata["finish"]
            finish_rect = pygame.Rect(fx - TRACK_WIDTH // 2, fy - TRACK_WIDTH // 2, TRACK_WIDTH, TRACK_WIDTH)
            pygame.draw.rect(screen, (0, 0, 255), finish_rect.move(-offset_x, -offset_y), 2)

            if not manual_finished and finish_rect.collidepoint(manual_car.center):
                manual_finished = True
                manual_car.speed = 0
                if "Manual Car" not in result_order:
                    result_order.append("Manual Car")
                    if not first_finisher:
                        first_finisher = "Manual Car"
                        finish_time = pygame.time.get_ticks()

            if best_car and not best_car_finished and finish_rect.collidepoint(best_car.center):
                best_car_finished = True
                best_car.speed = 0
                if "AI Car" not in result_order:
                    result_order.append("AI Car")
                    if not first_finisher:
                        first_finisher = "AI Car"
                        finish_time = pygame.time.get_ticks()

        # Race status popups
        if finish_time and not final_popup_shown and pygame.time.get_ticks() - finish_time < 2000:
            show_popup(f"{first_finisher} reached the finish line first!", screen, info_font)

        if manual_finished and best_car_finished and not final_popup_shown:
            final_popup_shown = True
            finish_time = pygame.time.get_ticks()

        if final_popup_shown and pygame.time.get_ticks() - finish_time < 2000 and len(result_order) == 2:
            show_popup(f"Race finished! 1st: {result_order[0]}, 2nd: {result_order[1]}", screen, info_font)

        # Draw UI elements
        draw_button(main_menu_btn, "Main Menu", main_menu_btn.collidepoint(*mouse_pos))
        draw_button(modes_btn, "Modes", modes_btn.collidepoint(*mouse_pos))
        draw_button(map_btn, "Map", map_btn.collidepoint(*mouse_pos))
        draw_button(quit_btn, "Quit", quit_btn.collidepoint(*mouse_pos))
        draw_button(logout_btn, "Logout", logout_btn.collidepoint(*mouse_pos))

        if show_modes_dropdown:
            dropdown_y = modes_btn.bottom
            for i, mode in enumerate(["Self-Driving", "Manual", "Race"]):
                rect = pygame.Rect(modes_btn.left, dropdown_y + i * button_height, button_width, button_height)
                draw_button(rect, mode, rect.collidepoint(*mouse_pos))

        # Logout prompt
        if show_logout_prompt:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            confirm_box = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 180)
            pygame.draw.rect(screen, (255, 255, 255), confirm_box)
            pygame.draw.rect(screen, (0, 0, 0), confirm_box, 2)

            prompt_text = info_font.render("Are you sure you want to logout?", True, (0, 0, 0))
            screen.blit(prompt_text, (confirm_box.centerx - prompt_text.get_width() // 2, confirm_box.y + 30))

            draw_button(yes_btn, "Yes", yes_btn.collidepoint(*mouse_pos))
            draw_button(no_btn, "No", no_btn.collidepoint(*mouse_pos))

        pygame.display.flip()


def run_race(user_id=None, username="Guest", is_admin=False):
    race(user_id, username, is_admin)
