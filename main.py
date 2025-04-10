import neat
import os
import sys
import argparse
import pygame

# button class
class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image
        self.x_pos, self.y_pos = pos
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input

        self.text_surf = self.font.render(self.text_input, True, self.base_color)
        self.text_rect = self.text_surf.get_rect(center=(self.x_pos, self.y_pos))
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.text_surf, self.text_rect)

    def checkForInput(self, position):
        return self.rect.collidepoint(position)

    def changeColor(self, position):
        if self.rect.collidepoint(position):
            self.text_surf = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text_surf = self.font.render(self.text_input, True, self.base_color)

# screen size
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

# load font
def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

# welcome screen
def splash_screen(screen, font):
    splash = True
    while splash:
        screen.fill((0, 0, 0))
        welcome_text = font.render("Welcome to Self Driving Car Simulator", True, (255, 255, 255))
        instruct_text = font.render("Press any key to continue", True, (255, 255, 255))

        screen.blit(welcome_text, welcome_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)))
        screen.blit(instruct_text, instruct_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                splash = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

# menu screen
def main_menu(screen, font):
    while True:
        BG = pygame.image.load("assets/Background.png")
        BG = pygame.transform.scale(BG, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(BG, (0, 0))

        mouse_pos = pygame.mouse.get_pos()

        menu_text = get_font(100).render("MAIN MENU", True, "#b68f40")
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        screen.blit(menu_text, menu_rect)

        self_driving_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 100),
            text_input="Self Driving Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )
        manual_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(SCREEN_WIDTH//2 + 200, SCREEN_HEIGHT//2 - 100),
            text_input="Manual Driving Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )
        race_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50),
            text_input="Race Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )
        quit_button = Button(
            image=pygame.image.load("assets/Quit.png"),
            pos=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 190),
            text_input="QUIT",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        for btn in (self_driving_button, manual_button, race_button, quit_button):
            btn.changeColor(mouse_pos)
            btn.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self_driving_button.checkForInput(mouse_pos):
                    return "auto"
                if manual_button.checkForInput(mouse_pos):
                    return "manual"
                if race_button.checkForInput(mouse_pos):
                    return "race"
                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

# main function
def main():
    parser = argparse.ArgumentParser(description="NEAT Car Simulation")
    parser.add_argument('--generations', type=int, default=1000,
                        help="Number of generations to run")
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Self Driving Car Simulator")
    font = get_font(30)

    splash_screen(screen, font)
    mode = main_menu(screen, font)

    if mode == "manual":
        os.system('python manual.py')
        sys.exit(0)
    elif mode == "race":
        os.system('python race.py')
        sys.exit(0)
    else:
        from selfdriving import run_auto_mode
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
        population.run(run_auto_mode, args.generations)

if __name__ == "__main__":
    main()
