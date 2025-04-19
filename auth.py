# auth.py

import pygame
import sys
from db import get_user, create_user, get_top_scores

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

def draw_dropdown(screen, rect, font, options, selected_index, open_dropdown):
    dropdown_color = (255, 255, 255)
    text_color = (0, 0, 0)
    hover_color = (200, 200, 200)
    border_color = (0, 0, 0)

    pygame.draw.rect(screen, dropdown_color, rect)
    pygame.draw.rect(screen, border_color, rect, 2)

    text = options[selected_index] if selected_index is not None else "Select a question..."
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (rect.x + 5, rect.y + 8))

    if open_dropdown:
        for i, option in enumerate(options):
            item_rect = pygame.Rect(rect.x, rect.y + (i + 1) * rect.height, rect.width, rect.height)
            pygame.draw.rect(screen, dropdown_color, item_rect)
            pygame.draw.rect(screen, border_color, item_rect, 2)
            mouse_pos = pygame.mouse.get_pos()
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, hover_color, item_rect)
            item_text = font.render(option, True, text_color)
            screen.blit(item_text, (item_rect.x + 5, item_rect.y + 8))

def entry_screen(screen, font):
    login_btn = pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 30, 140, 50)
    register_btn = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 30, 140, 50)
    guest_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 40, 140, 45)  # New Guest button
    clock = pygame.time.Clock()

    button_font = pygame.font.SysFont("arial", 28, bold=True)

    while True:
        screen.fill((30, 30, 30))
        title = font.render("Login if you are Returning Player or else Register", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        mouse_pos = pygame.mouse.get_pos()
        for rect, label in [
            (login_btn, "Login"),
            (register_btn, "Register"),
            (guest_btn, "Guest")  # New label
        ]:
            hover = rect.collidepoint(mouse_pos)
            color = (255, 255, 255) if hover else (180, 180, 180)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=8)

            text_surface = button_font.render(label, True, (0, 0, 0))
            screen.blit(text_surface, text_surface.get_rect(center=rect.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if login_btn.collidepoint(event.pos):
                    return "login"
                elif register_btn.collidepoint(event.pos):
                    return "register"
                elif guest_btn.collidepoint(event.pos):
                    return "guest"  # New return value

        pygame.display.flip()
        clock.tick(30)


def get_user_login(screen, font, background, bg_x, bg_y):
    import pygame
    from db import get_user, get_top_scores

    field_font = pygame.font.SysFont("arial", 28, bold=True)  # Custom font for fields

    username_box = pygame.Rect(120, 280, 300, 40)
    password_box = pygame.Rect(120, 340, 300, 40)

    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    username_color = color_inactive
    password_color = color_inactive
    username_active = False
    password_active = False
    username = ''
    password = ''
    error_msg = ''
    rankings = get_top_scores(100)

    while True:
        screen.blit(background, (bg_x, bg_y))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if username_box.collidepoint(event.pos):
                    username_active = True
                    password_active = False
                elif password_box.collidepoint(event.pos):
                    password_active = True
                    username_active = False
                else:
                    username_active = password_active = False
                username_color = color_active if username_active else color_inactive
                password_color = color_active if password_active else color_inactive
            elif event.type == pygame.KEYDOWN:
                if username_active and not password_active:
                    if event.key == pygame.K_RETURN:
                        username_active = False
                        password_active = True
                        username_color = color_inactive
                        password_color = color_active
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
                elif password_active and not username_active:
                    if event.key == pygame.K_RETURN and username.strip() and password.strip():
                        user_id = get_user(username.strip(), password.strip())
                        if user_id:
                            return user_id, username.strip()
                        else:
                            existing_id = get_user(username.strip())
                            if existing_id:
                                error_msg = "❌ Incorrect password."
                            else:
                                from auth import register_user
                                username = register_user(screen, font, background, bg_x, bg_y)
                                user_id = get_user(username, password.strip())
                                return user_id, username
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode

        # Title
        prompt = field_font.render("Login", True, (0, 0, 0))
        screen.blit(prompt, (140, 220))

        # Input text
        username_surface = field_font.render(username, True, username_color)
        password_surface = field_font.render('*' * len(password), True, password_color)

        username_box.w = max(300, username_surface.get_width() + 10)
        password_box.w = max(300, password_surface.get_width() + 10)

        screen.blit(username_surface, (username_box.x + 5, username_box.y + 10))
        screen.blit(password_surface, (password_box.x + 5, password_box.y + 10))
        pygame.draw.rect(screen, username_color, username_box, 2)
        pygame.draw.rect(screen, password_color, password_box, 2)

        # Error message
        if error_msg:
            error_surface = field_font.render(error_msg, True, (255, 0, 0))
            screen.blit(error_surface, (SCREEN_WIDTH // 2 - error_surface.get_width() // 2, password_box.y + 50))

        pygame.display.flip()
        pygame.time.Clock().tick(30)

def register_user(screen, font, background, bg_x, bg_y):
    import pygame
    from db import create_user, get_user

    field_font = pygame.font.SysFont("arial", 28, bold=True)  # NEW FONT

    start_y = 180
    box_width = 300
    box_height = 40
    gap = 70
    left_x = 120

    input_box_user = pygame.Rect(left_x, start_y + gap * 0, box_width, box_height)
    input_box_pass = pygame.Rect(left_x, start_y + gap * 1, box_width, box_height)
    question_box = pygame.Rect(left_x, start_y + gap * 2, box_width, box_height)
    input_box_answ = pygame.Rect(left_x, start_y + gap * 3, box_width, box_height)

    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    active_field = None

    username = ""
    password = ""
    answer = ""
    selected_index = None
    error_msg = ""

    questions = [
        "What is your favorite color?",
        "What is your pet's name?",
        "What city were you born in?",
        "What is your favorite food?"
    ]
    dropdown_open = False

    while True:
        screen.blit(background, (bg_x, bg_y))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box_user.collidepoint(event.pos):
                    active_field = "user"
                    dropdown_open = False
                elif input_box_pass.collidepoint(event.pos):
                    active_field = "pass"
                    dropdown_open = False
                elif input_box_answ.collidepoint(event.pos):
                    active_field = "answ"
                    dropdown_open = False
                elif question_box.collidepoint(event.pos):
                    dropdown_open = not dropdown_open
                    active_field = None
                else:
                    active_field = None
                    if dropdown_open:
                        for i, _ in enumerate(questions):
                            option_rect = pygame.Rect(
                                question_box.x,
                                question_box.y + (i + 1) * question_box.height,
                                question_box.width,
                                question_box.height
                            )
                            if option_rect.collidepoint(event.pos):
                                selected_index = i
                                dropdown_open = False
                                break
                        else:
                            dropdown_open = False
            elif event.type == pygame.KEYDOWN:
                if active_field == "user":
                    if event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
                elif active_field == "pass":
                    if event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode
                elif active_field == "answ":
                    if event.key == pygame.K_BACKSPACE:
                        answer = answer[:-1]
                    else:
                        answer += event.unicode

                if event.key == pygame.K_RETURN:
                    if username.strip() and password.strip() and selected_index is not None and answer.strip():
                        if get_user(username.strip()) is not None:
                            error_msg = "Username already exists!"
                        else:
                            create_user(
                                username.strip(),
                                password.strip(),
                                questions[selected_index],
                                answer.strip()
                            )
                            return username.strip()
                    else:
                        error_msg = "All fields are required."

        # Title
        prompt = field_font.render("Register New Account", True, (0, 0, 0))
        screen.blit(prompt, (left_x, start_y - 80))

        # Input fields
        fields = [
            (input_box_user, username, active_field == "user"),
            (input_box_pass, '*' * len(password), active_field == "pass")
        ]
        if selected_index is not None:
            fields.append((input_box_answ, answer, active_field == "answ"))

        for rect, text, is_active in fields:
            color = color_active if is_active else color_inactive
            txt_surface = field_font.render(text, True, (255, 255, 255))
            rect.w = max(300, txt_surface.get_width() + 10)
            screen.blit(txt_surface, (rect.x + 5, rect.y + 12))
            pygame.draw.rect(screen, color, rect, 2)

        # Dropdown
        draw_dropdown(screen, question_box, field_font, questions, selected_index, dropdown_open)

        # Labels
        labels = ["Username", "Password", "Choose a question"]
        boxes = [input_box_user, input_box_pass, question_box]
        if selected_index is not None:
            labels.append("Your Answer")
            boxes.append(input_box_answ)

        for label, box in zip(labels, boxes):
            label_surface = field_font.render(label, True, (180, 180, 180))
            screen.blit(label_surface, (box.x, box.y - 35))

        if error_msg:
            error_surface = field_font.render(error_msg, True, (255, 0, 0))
            screen.blit(error_surface, (SCREEN_WIDTH // 2 - error_surface.get_width() // 2, SCREEN_HEIGHT // 2 + 130))

        pygame.display.flip()
        pygame.time.Clock().tick(30)
