import neat
import os
import sys
import argparse
import pygame
from simulation import run_car, select_map  # Notice we import select_map from simulation.py
from button import Button

# Global screen dimensions
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

def get_font(size):
    """Returns a font object from the assets folder."""
    return pygame.font.Font("assets/font.ttf", size)

def splash_screen(screen, font):
    """Display a welcome screen and wait for any key press."""
    splash = True
    while splash:
        screen.fill((0, 0, 0))  # Black background for splash
        welcome_text = font.render("Welcome to Self Driving Car Simulator", True, (255, 255, 255))
        instruct_text = font.render("Press any key to continue", True, (255, 255, 255))

        # Center the text on the screen
        screen.blit(welcome_text, welcome_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))
        screen.blit(instruct_text, instruct_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                splash = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

def main_menu(screen, font):
    """Display a main menu with two mode selection buttons and a quit button below."""
    while True:
        # Load and scale background image.
        BG = pygame.image.load("assets/Background.png")
        BG = pygame.transform.scale(BG, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()
        MENU_TEXT = get_font(100).render("MAIN MENU", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(MENU_TEXT, MENU_RECT)

        # Create two buttons for the driving modes.
        self_driving_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2),
            text_input="Self Driving Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        manual_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2),
            text_input="Manual Driving Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Create a quit button positioned just below the other two buttons.
        quit_button = Button(
            image=pygame.image.load("assets/Quit.png"),
            pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150),
            text_input="QUIT",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Update each button.
        for button in [self_driving_button, manual_button, quit_button]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(screen)

        # Check for events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self_driving_button.checkForInput(MENU_MOUSE_POS):
                    return "auto"
                elif manual_button.checkForInput(MENU_MOUSE_POS):
                    return "manual"
                elif quit_button.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

def main() -> None:
    # Set up argument parsing for NEAT (if needed)
    parser = argparse.ArgumentParser(description="NEAT Car Simulation")
    parser.add_argument('--generations', type=int, default=1000, help="Number of generations to run")
    args = parser.parse_args()

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Self Driving Car Simulator")
    font = get_font(30)

    # Show the splash screen first
    splash_screen(screen, font)

    # Show the main menu and get user selection
    mode = main_menu(screen, font)

    if mode == "manual":
        # Let the user select a map.
        # The select_map function (from simulation.py) displays a map selection interface
        global_map_path = select_map(screen, font)
        # Launch manual driving mode, passing the selected map path as an argument.
        # (Your manual.py code should be modified to accept a command-line argument --map_path.)
        os.system(f'python manual.py --map_path "{global_map_path}"')
        sys.exit(0)
    else:  # "auto" selected
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

        population.run(run_car, args.generations)

if __name__ == "__main__":
    main()
