import pygame
import sys
import neat
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT, RADAR_MAX_LENGTH
from typing import List
from button import Button


# Define a light green color for the background.
LightGreen = (144, 238, 144)
# Set a constant speed for all cars during simulation.
CONSTANT_SPEED = 5


def get_sorted_map_files() -> List[str]:
    """
    Get and return a sorted list of map image files from the "maps" folder.
    The sorting ensures that "map.png" comes first, followed by "map1.png", "map2.png", etc.
    """
    maps_folder = "maps"
    # List all files in the maps folder that end with '.png'
    files = [f for f in os.listdir(maps_folder) if f.endswith('.png')]

    def sort_key(filename: str):
        base, _ = os.path.splitext(filename)
        # "map" with no number should be the first.
        if base == "map":
            return 0
        elif base.startswith("map"):
            try:
                # Extract numeric part after "map" for sorting.
                return int(base[3:])
            except:
                return float('inf')
        else:
            return float('inf')

    return sorted(files, key=sort_key)


def select_map(screen: pygame.Surface, font: pygame.font.Font) -> str:
    """
    Let the user select a map using the keyboard arrow keys and Enter.
    Displays a list of map files along with a preview of the selected map.
    Returns the full path of the selected map.
    """
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    selected_index = 0

    # Preview box dimensions and position.
    preview_width = 300
    preview_height = 200
    preview_x = 250  # x position for the preview box
    preview_y = 100  # y position for the preview box

    selecting = True
    while selecting:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # Use UP and DOWN arrow keys to change selection.
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(map_files)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(map_files)
                elif event.key == pygame.K_RETURN:
                    # Press Enter to confirm selection.
                    selecting = False

        # Draw the title.
        title_text = font.render("Select a Map:", True, (0, 0, 0))
        screen.blit(title_text, (50, 50))
        # Draw the list of map options.
        for i, map_file in enumerate(map_files):
            base, _ = os.path.splitext(map_file)
            label = base.capitalize()  # e.g., "Map", "Map1", "Map2"
            # Highlight the currently selected map in red.
            color = (255, 0, 0) if i == selected_index else (0, 0, 0)
            text = font.render(label, True, color)
            screen.blit(text, (50, 100 + i * 30))

        # Draw the preview box border.
        pygame.draw.rect(screen, (0, 0, 0), (preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10), 2)
        # Load and display the preview image for the selected map.
        try:
            preview_image = pygame.image.load(os.path.join(maps_folder, map_files[selected_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception as e:
            pass

        pygame.display.flip()
    return os.path.join(maps_folder, map_files[selected_index])


def draw_map_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """
    Draw a button on the top-right corner displaying the current map's label.
    Returns the button's rectangle area for detecting mouse clicks.
    """
    maps_folder = "maps"
    map_files = get_sorted_map_files()

    # Check if a global map path has been set in run_car; if not, use the first map.
    if hasattr(run_car, "global_map_path") and run_car.global_map_path:
        current_map = os.path.basename(run_car.global_map_path)
    else:
        current_map = map_files[0]

    base, _ = os.path.splitext(current_map)
    label = base.capitalize()

    # Load and scale the image.
    original_image = pygame.image.load("assets/simulate.png")
    scaled_image = pygame.transform.scale(original_image, (100, 40))  # Adjust width and height as needed

    # Create a button using the scaled image.
    map_button = Button(
        image=scaled_image,
        pos=(SCREEN_WIDTH - 60, 30),  # Adjust position as needed
        text_input=label,
        font=font,
        base_color="#d7fcd4",  # Consistent base color
        hovering_color="White"  # Consistent hovering color
    )

    map_button.update(screen)  # Draw the button on the screen
    return map_button.rect  # Return the button's rectangle for later detection


def draw_manual_mode_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """
    Draw a button on the top-left corner for switching to manual mode.
    Returns the button's rectangle area for detecting mouse clicks.
    """
    # Load the button image and scale it to 150x40 pixels.
    original_image = pygame.image.load("assets/simulate.png")
    scaled_image = pygame.transform.scale(original_image, (150, 40))

    # Calculate the center position of the button.
    # Since we want the button's top-left corner at (10, 10), the center is:
    # (10 + 150/2, 10 + 40/2) = (85, 30)
    pos = (10 + 150 // 2, 10 + 40 // 2)

    # Create the button using the Button class.
    manual_button = Button(
        image=scaled_image,
        pos=pos,
        text_input="Manual Mode",
        font=font,
        base_color="#d7fcd4",  # Consistent base color
        hovering_color="White"  # Consistent hovering color
    )

    # Draw the button on the screen.
    manual_button.update(screen)

    # Return the rectangle of the button for click detection.
    return manual_button.rect


def dropdown_map_selection(screen: pygame.Surface, font: pygame.font.Font) -> str:
    """
    Display a dropdown list for map selection using Button objects.
    The user can click an option to select a new map and a preview of the hovered map is shown.
    Returns the full path of the selected map.
    """
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)

    # Define the dropdown area based on the map button's position.
    button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 40)
    item_height = 30
    dropdown_rect = pygame.Rect(button_rect.left, button_rect.bottom, button_rect.width, item_height * len(map_files))

    # Set preview dimensions and position (to the left of the dropdown list).
    preview_width = 300
    preview_height = 200
    preview_x = dropdown_rect.left - preview_width - 20  # Preview appears to the left.
    preview_y = dropdown_rect.top

    # Create Button objects for each map option.
    option_buttons = []
    for i, map_file in enumerate(map_files):
        base, _ = os.path.splitext(map_file)
        label = base.capitalize()
        # For each button, calculate its center:
        center_x = dropdown_rect.left + dropdown_rect.width // 2
        center_y = dropdown_rect.top + i * item_height + item_height // 2

        # Load and scale the button image to the size of (dropdown_rect.width, item_height)
        original_image = pygame.image.load("assets/simulate.png")
        scaled_image = pygame.transform.scale(original_image, (dropdown_rect.width, item_height))

        btn = Button(
            image=scaled_image,
            pos=(center_x, center_y),
            text_input=label,
            font=font,
            base_color="#d7fcd4",
            hovering_color="White"
        )
        option_buttons.append(btn)

    dropdown_active = True
    selected_map = None
    clock = pygame.time.Clock()

    while dropdown_active:
        # Fill background (use your LightGreen color)
        screen.fill(LightGreen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                # Check if any option button is clicked.
                for i, btn in enumerate(option_buttons):
                    if btn.checkForInput(mouse_pos):
                        selected_map = os.path.join(maps_folder, map_files[i])
                        dropdown_active = False
                        break
                # If clicked outside all buttons, close the dropdown.
                if not any(btn.rect.collidepoint(mouse_pos) for btn in option_buttons):
                    dropdown_active = False

        # Create a semi-transparent overlay for a modern look.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((50, 50, 50, 180))  # RGBA, alpha 180 for semi-transparency
        screen.blit(overlay, (0, 0))

        # Draw the dropdown background with a rounded rectangle look.
        # (You can use your own rounded_rect function if desired.)
        pygame.draw.rect(screen, (240, 240, 240), dropdown_rect, border_radius=8)
        pygame.draw.rect(screen, (0, 0, 0), dropdown_rect, 2, border_radius=8)

        # Draw each option button.
        for btn in option_buttons:
            btn.changeColor(pygame.mouse.get_pos())
            btn.update(screen)

        # Draw a preview box for the hovered option.
        preview_box_rect = pygame.Rect(preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10)
        pygame.draw.rect(screen, (0, 0, 0), preview_box_rect, 2)

        # Determine the hovered option (if any).
        mouse_pos = pygame.mouse.get_pos()
        hovered_index = 0
        for i, btn in enumerate(option_buttons):
            if btn.rect.collidepoint(mouse_pos):
                hovered_index = i
                break

        try:
            preview_image = pygame.image.load(os.path.join(maps_folder, map_files[hovered_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception as e:
            pass

        pygame.display.flip()
        clock.tick(60)
    return selected_map


# Helper function that returns a sorted list of map filenames.
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


def drag_and_drop_starting_position(screen: pygame.Surface, info_font: pygame.font.Font,
                                    collision_mask: pygame.mask.Mask, display_map: pygame.Surface) -> List[float]:
    """
    Allow the user to set the starting position of the car by dragging and dropping it on the map.
    The function ensures that the car is placed in a valid location on the track.
    Returns the chosen starting position as a list [x, y].
    """
    drag_car = Car()
    initial_default_position = drag_car.pos.copy()
    dragging = False
    valid_drop = False
    message = ""
    clock = pygame.time.Clock()
    while not valid_drop:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Check if the mouse click is on the car.
                car_rect = pygame.Rect(drag_car.pos[0], drag_car.pos[1], 100, 100)
                if car_rect.collidepoint(mouse_pos):
                    dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                drag_car.update(display_map, collision_mask)
                # Accept the drop if the car is on a valid part of the track and has moved.
                if drag_car.get_alive() and drag_car.pos != initial_default_position:
                    valid_drop = True
                else:
                    message = "Please reposition the car on the track!"
            elif event.type == pygame.MOUSEMOTION and dragging:
                # Update the car's position based on mouse movement.
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
    """
    Run the NEAT simulation for controlling cars.
    Each genome controls a car, and the simulation updates the cars based on sensor input and the neural network output.
    This function handles fitness assignment, visual updates, and transitions between generations.
    """
    # Initialize global attributes for map path, starting position, and generation count if not set.
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

    # Select a map if one hasn't been chosen yet.
    if run_car.global_map_path is None:
        run_car.global_map_path = select_map(screen, info_font)
    try:
        display_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    except Exception as e:
        print(f"Error loading map image: {e}")
        sys.exit(1)
    # Create a collision mask from the map image.
    collision_map = pygame.image.load(run_car.global_map_path).convert_alpha()
    collision_map.set_colorkey(LightGreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    # Set the starting position by allowing the user to drag and drop the car if not already set.
    if run_car.starting_position is None:
        run_car.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    nets = []   # List to store neural networks for each genome.
    cars = []   # List to store car objects.
    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        genome.fitness = 0  # Initialize genome fitness.
        # Create a new car at the starting position.
        cars.append(Car(initial_pos=run_car.starting_position.copy()))

    # Update each car once before starting the simulation loop.
    for car in cars:
        car.update(display_map, collision_mask)

    run_car.generation += 1

    simulation_fps = 240  # Use a higher FPS for faster simulation.
    offset_x, offset_y = 0, 0
    running = True
    while running:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        remaining_cars = 0  # Count of cars that are still alive.
        for index, car in enumerate(cars):
            if car.get_alive():
                # Retrieve normalized sensor data (radar distances and constant speed).
                radar_data = car.get_data()
                # Activate the neural network using the sensor data.
                output = nets[index].activate(radar_data)

                # --- Smooth Steering ---
                max_steering_change = 15
                if not hasattr(car, "angular_velocity"):
                    car.angular_velocity = 0
                desired_turn = output[0] * max_steering_change
                smoothing_turn_factor = 0.1
                # Adjust the turning rate smoothly.
                car.angular_velocity += smoothing_turn_factor * (desired_turn - car.angular_velocity)
                car.angle += car.angular_velocity

                # --- Constant Speed ---
                car.speed = CONSTANT_SPEED

                # Update the car's position and sensor readings.
                car.update(display_map, collision_mask)

                # --- Enhanced Fitness Calculation ---
                fitness_boost = car.get_reward() + (car.distance * 0.05)
                if radar_data[0] > 50:
                    fitness_boost += 0.1
                if abs(car.angular_velocity) < 3:
                    fitness_boost += 0.2
                genomes[index][1].fitness += fitness_boost

                remaining_cars += 1

        # Adjust the camera to center on the average position of all alive cars.
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

        # Draw buttons for switching modes and selecting maps.
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
                    collision_map.set_colorkey(LightGreen)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    run_car.starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                    for car in cars:
                        car.pos = run_car.starting_position.copy()
                        car.center = [
                            int(car.pos[0] + car.surface.get_width() / 2),
                            int(car.pos[1] + car.surface.get_height() / 2)
                        ]

        # If no cars are alive, end the generation.
        if remaining_cars == 0:
            message = info_font.render("Generation Over", True, (0, 0, 0))
            screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 50))
            pygame.display.flip()
            pygame.time.wait(500)
            break

        pygame.display.flip()
        clock.tick(simulation_fps)
