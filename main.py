import neat
import os
import sys
import argparse
import pygame
from auth import entry_screen, get_user_login, register_user
from manual import run_manual
from race import run_race
from selfdriving import run_selfdriving

# Screen size
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

# Button class
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

# Load font
def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

# Splash screen
def splash_screen(screen, font):
    splash = True
    while splash:
        screen.fill((0, 0, 0))
        welcome_text = font.render("This is a simple car driving simulator", True, (255, 255, 255))
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

# Main menu screen (standalone)
def main_menu(user_id=None, username="Guest"):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Main Menu")
    font = get_font(30)

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
                    from selfdriving import run_selfdriving
                    pygame.quit()
                    run_selfdriving()
                if manual_button.checkForInput(mouse_pos):
                    from manual import run_manual
                    pygame.quit()
                    run_manual(user_id=user_id, username=username)

                if race_button.checkForInput(mouse_pos):
                    from race import run_race
                    pygame.quit()
                    run_race()
                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

# Mode selection from dropdown use
def run_selected_mode(mode, user_id=None, username="Guest", generations=1000):
    if mode == "manual":
        from manual import run_manual
        run_manual(map_path=None, user_id=user_id, username=username)
    elif mode == "race":
        from race import run_race
        run_race()
    elif mode == "auto":
        from selfdriving import run_selfdriving
        run_selfdriving(generations=generations)

# Main entry
def main():
    parser = argparse.ArgumentParser(description="NEAT Car Simulation")
    parser.add_argument('--generations', type=int, default=1000,
                        help="Number of generations to run")
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Self Driving Car Simulator")
    font = get_font(30)

    background = pygame.image.load("assets/login.png").convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_x, bg_y = 0, 0

    splash_screen(screen, font)
    action = entry_screen(screen, font)

    if action == "login":
        user_id, username = get_user_login(screen, font, background, bg_x, bg_y)
    elif action == "register":
        username = register_user(screen, font, background, bg_x, bg_y)
        from db import get_user
        user_id = get_user(username, None)
    else:  # guest
        user_id, username = None, "Guest"

    mode = run_main_menu(user_id, username)

    if mode == "manual":
        run_manual(map_path=None, user_id=user_id, username=username)
    elif mode == "race":
        run_race()
    else:
        run_selfdriving(generations=args.generations)

# For entry screen flow only — keeps full menu return modular
def run_main_menu(user_id, username):
    return_value = True
    while return_value:
        mode = main_menu(user_id, username)
        return mode


if __name__ == "__main__":
    main()
