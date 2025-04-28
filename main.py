import sys
import argparse
import pygame
from auth import entry_screen, get_user_login, register_user, is_admin
from manual import run_manual
from race import run_race
from selfdriving import run_selfdriving
from db import init_db
import os
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

        if self.image is not None:
            self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        else:
            # If no image, use text rect for button collision
            self.rect = self.text_surf.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        if self.image is not None:
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
from db import get_all_users, delete_user_by_username


def delete_map(map_name):
    import os
    map_path = os.path.join('maps', f"{map_name}.png")
    metadata_path = os.path.join('startfinish', f"{map_name}_metadata.json")

    if os.path.exists(map_path):
        os.remove(map_path)
    if os.path.exists(metadata_path):
        os.remove(metadata_path)


def get_all_maps():
    maps_folder = "maps"
    return [f[:-4] for f in os.listdir(maps_folder) if f.endswith(".png")]
def confirm_delete_map(screen, map_name):
    # You can show a simple "Are you sure?" popup here
    delete_map(map_name)


def manage_users_screen(screen):
    running = True
    field_font = pygame.font.SysFont("arial", 28, bold=True)
    title_font = pygame.font.SysFont("arial", 48, bold=True)

    scroll_offset_users = 0
    scroll_offset_maps = 0
    max_visible = 5
    scroll_speed = 30  # How much to move per scroll

    while running:
        screen.fill((30, 30, 30))

        users = get_all_users()
        maps = get_all_maps()

        user_y_start = 150
        map_y_start = 150
        mouse_pos = pygame.mouse.get_pos()

        # Title
        title_text = title_font.render("Manage Users and Maps", True, (255, 255, 255))
        screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH // 2, 60)))

        # BACK button
        back_button = Button(
            image=None,
            pos=(100, 50),
            text_input="Back",
            font=field_font,
            base_color="#d7fcd4",
            hovering_color="White"
        )
        back_button.changeColor(mouse_pos)
        back_button.update(screen)

        # -------- USERS SECTION (LEFT) --------
        users_title = title_font.render("Users", True, (255, 255, 255))
        screen.blit(users_title, (SCREEN_WIDTH // 4 - users_title.get_width() // 2, 100))

        user_buttons = []  # store remove buttons for users

        start_user_index = scroll_offset_users // scroll_speed
        for idx, username in enumerate(users[start_user_index:start_user_index + max_visible]):
            y_pos = user_y_start + idx * 60

            username_button = Button(
                image=None,
                pos=(SCREEN_WIDTH // 4 - 100, y_pos),
                text_input=username,
                font=field_font,
                base_color="#d7fcd4",
                hovering_color="White"
            )

            remove_text = field_font.render("Remove", True, (255, 0, 0))
            remove_rect = remove_text.get_rect(center=(SCREEN_WIDTH // 4 + 100, y_pos))

            if remove_rect.collidepoint(mouse_pos):
                background_color = (150, 150, 150)
            else:
                background_color = (255, 255, 255)

            pygame.draw.rect(screen, background_color, remove_rect.inflate(20, 10))
            screen.blit(remove_text, remove_rect)

            username_button.changeColor(mouse_pos)
            username_button.update(screen)

            user_buttons.append((remove_rect, username))  # save button and username for checking clicks

        # -------- MAPS SECTION (RIGHT) --------
        maps_title = title_font.render("Maps", True, (255, 255, 255))
        screen.blit(maps_title, (SCREEN_WIDTH * 3 // 4 - maps_title.get_width() // 2, 100))

        map_buttons = []  # store delete buttons for maps

        start_map_index = scroll_offset_maps // scroll_speed
        for idx, map_name in enumerate(maps[start_map_index:start_map_index + max_visible]):
            y_pos = map_y_start + idx * 60

            map_button = Button(
                image=None,
                pos=(SCREEN_WIDTH * 3 // 4 - 100, y_pos),
                text_input=map_name,
                font=field_font,
                base_color="#d7fcd4",
                hovering_color="White"
            )

            delete_text = field_font.render("Delete", True, (255, 0, 0))
            delete_rect = delete_text.get_rect(center=(SCREEN_WIDTH * 3 // 4 + 100, y_pos))

            if delete_rect.collidepoint(mouse_pos):
                background_color = (150, 150, 150)
            else:
                background_color = (255, 255, 255)

            pygame.draw.rect(screen, background_color, delete_rect.inflate(20, 10))
            screen.blit(delete_text, delete_rect)

            map_button.changeColor(mouse_pos)
            map_button.update(screen)

            map_buttons.append((delete_rect, map_name))  # save button and map for checking clicks

        # -------- Event Handling --------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if back_button.checkForInput(mouse_pos):
                        return

                    # Check if clicked any user remove button
                    for remove_rect, username in user_buttons:
                        if remove_rect.collidepoint(mouse_pos):
                            confirm_delete_user(screen, username)
                            break  # after deleting, break out

                    # Check if clicked any map delete button
                    for delete_rect, map_name in map_buttons:
                        if delete_rect.collidepoint(mouse_pos):
                            confirm_delete_map(screen, map_name)
                            break

                # Scroll users (mouse wheel)
                if event.button == 4:  # Mouse wheel up
                    if mouse_pos[0] < SCREEN_WIDTH // 2:  # Left side (users)
                        scroll_offset_users = max(scroll_offset_users - scroll_speed, 0)
                    else:  # Right side (maps)
                        scroll_offset_maps = max(scroll_offset_maps - scroll_speed, 0)
                if event.button == 5:  # Mouse wheel down
                    if mouse_pos[0] < SCREEN_WIDTH // 2:  # Left side (users)
                        if (scroll_offset_users // scroll_speed) + max_visible < len(users):
                            scroll_offset_users += scroll_speed
                    else:  # Right side (maps)
                        if (scroll_offset_maps // scroll_speed) + max_visible < len(maps):
                            scroll_offset_maps += scroll_speed

        pygame.display.update()


def confirm_delete_user(screen, username):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 30, bold=True)
    running = True

    yes_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 10, 100, 40)
    no_btn = pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 10, 100, 40)

    def draw_button(rect, text, hover=False):
        color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
        label = font.render(text, True, (0, 0, 0))
        screen.blit(label, label.get_rect(center=rect.center))

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 0))  # Full black background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        confirm_box = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 180)
        pygame.draw.rect(screen, (255, 255, 255), confirm_box)
        pygame.draw.rect(screen, (0, 0, 0), confirm_box, 2)

        prompt_text = font.render(f"Delete user '{username}'?", True, (0, 0, 0))
        screen.blit(prompt_text, (confirm_box.centerx - prompt_text.get_width() // 2, confirm_box.y + 30))

        draw_button(yes_btn, "Yes", hover=yes_btn.collidepoint(mouse_pos))
        draw_button(no_btn, "No", hover=no_btn.collidepoint(mouse_pos))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_btn.collidepoint(mouse_pos):
                    from db import delete_user_by_username
                    delete_user_by_username(username)
                    return
                elif no_btn.collidepoint(mouse_pos):
                    return

        pygame.display.flip()
        clock.tick(60)

# Main menu screen (standalone)
def main_menu(user_id=None, username="Guest", is_admin=False):
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
        # Greet the user
        hi_text = get_font(40).render(f"Hi, {username}!", True, "#d7fcd4")
        hi_rect = hi_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
        screen.blit(hi_text, hi_rect)

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
        if is_admin:
            map_editor_button = Button(
                image=pygame.image.load("assets/Simulate.png"),
                pos=(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 50),  # same y, right of Race Mode
                text_input="Map Editor",
                font=get_font(18),
                base_color="#d7fcd4",
                hovering_color="White"
            )

        # Adjust race mode button position based on user type
        race_button_x = SCREEN_WIDTH // 2 - 200
        race_button_y = SCREEN_HEIGHT // 2 + 50

        if not is_admin:
            race_button_x += 200  # Shift right by 100 pixels for normal users

        race_button = Button(
            image=pygame.image.load("assets/Simulate.png"),
            pos=(race_button_x, race_button_y),
            text_input="Race Mode",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Default Quit button position
        quit_button_x = SCREEN_WIDTH // 2
        quit_button_y = SCREEN_HEIGHT // 2 + 190

        if is_admin:
            quit_button_x -= 200  # Move 100 pixels more to the left for Admin users

        quit_button = Button(
            image=pygame.image.load("assets/Quit.png"),
            pos=(quit_button_x, quit_button_y),
            text_input="QUIT",
            font=get_font(18),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        if is_admin:
            users_button = Button(
                image=pygame.image.load("assets/Simulate.png"),
                pos=(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 190),  # beside Quit button
                text_input="Users",
                font=get_font(18),
                base_color="#d7fcd4",
                hovering_color="White"
            )
        if is_admin:
            users_button.changeColor(mouse_pos)
            users_button.update(screen)

        for btn in (self_driving_button, manual_button, race_button, quit_button):
            btn.changeColor(mouse_pos)
            btn.update(screen)

        if is_admin:
            map_editor_button.changeColor(mouse_pos)
            map_editor_button.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self_driving_button.checkForInput(mouse_pos):
                    from selfdriving import run_selfdriving
                    pygame.display.quit()  # ✅ only close the window
                    run_selfdriving(user_id=user_id, username=username, is_admin=is_admin)

                if manual_button.checkForInput(mouse_pos):
                    from manual import run_manual
                    pygame.display.quit()
                    run_manual(user_id=user_id, username=username, is_admin=is_admin)

                if race_button.checkForInput(mouse_pos):
                    from race import run_race
                    pygame.display.quit()
                    run_race(user_id=user_id, username=username, is_admin=is_admin)

                if is_admin and map_editor_button.checkForInput(mouse_pos):
                    import map_editor
                    pygame.display.quit()
                    map_editor.run_map_editor(user_id=user_id, username=username, is_admin=True)

                if is_admin and users_button.checkForInput(mouse_pos):
                    manage_users_screen(screen)

                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

# Mode selection from dropdown use
def run_selected_mode(mode, user_id=None, username="Guest", generations=1000, is_admin=False):
    if mode == "manual":
        from manual import run_manual
        run_manual(map_path=None, user_id=user_id, username=username, is_admin=is_admin)
    elif mode == "race":
        from race import run_race
        run_race(user_id=user_id, username=username, is_admin=is_admin)
    elif mode == "auto":
        from selfdriving import run_selfdriving
        run_selfdriving(generations=generations, user_id=user_id, username=username, is_admin=is_admin)


# Main entry
def main():
    init_db()
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
        user_id = get_user(username)
    else:  # guest
        user_id, username = None, "Guest"

    admin_flag = is_admin(username)

    def run_main_menu(user_id, username):
        return_value = True
        while return_value:
            mode = main_menu(user_id, username, admin_flag)
            return mode

    mode = run_main_menu(user_id, username)

    if mode == "manual":
        run_manual(map_path=None, user_id=user_id, username=username, is_admin=admin_flag)
    elif mode == "race":
        run_race(user_id=user_id, username=username, is_admin=admin_flag)
    else:
        run_selfdriving(generations=args.generations, user_id=user_id, username=username, is_admin=admin_flag)


if __name__ == "__main__":
    main()
