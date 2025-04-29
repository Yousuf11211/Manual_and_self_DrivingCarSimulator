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

    field_font = pygame.font.SysFont("arial", 28, bold=True)
    title_font = pygame.font.SysFont("arial", 48, bold=True)

    username_box = pygame.Rect(300, 280, 220, 40)
    password_box = pygame.Rect(300, 340, 220, 40)

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

    show_forgot_password = False

    register_font = pygame.font.SysFont("arial", 24, bold=False)
    forgot_font = pygame.font.SysFont("arial", 22, bold=True)

    while True:
        screen.blit(background, (bg_x, bg_y))
        mouse_pos = pygame.mouse.get_pos()

        register_text = register_font.render("New user? Register here", True, (0, 0, 255))
        register_rect = register_text.get_rect(topleft=(200,450))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if username_box.collidepoint(event.pos):
                    username_active = True
                    password_active = False
                elif password_box.collidepoint(event.pos):
                    password_active = True
                    username_active = False
                elif show_forgot_password and forgot_rect.collidepoint(event.pos):
                    handle_forgot_password(screen, font, background, bg_x, bg_y)
                    username = ""
                    password = ""
                    error_msg = ""
                    show_forgot_password = False
                elif register_rect.collidepoint(event.pos):
                    username = register_user(screen, font, background, bg_x, bg_y)
                    user_id = get_user(username)
                    return user_id, username

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
                                error_msg = "Incorrect password."
                                show_forgot_password = True
                            else:
                                error_msg = "Username or Password does not match."
                                show_forgot_password = True
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode

        # Title
        prompt = title_font.render("Login page", True, (0, 0, 0))
        screen.blit(prompt, (750, 100))

        blink = pygame.time.get_ticks() // 500 % 2

        # Username
        username_label = field_font.render("Username", True, (0, 0, 0))
        screen.blit(username_label, (username_box.x - username_label.get_width() - 20, username_box.y + 5))

        username_surface = field_font.render(username, True, username_color)
        screen.blit(username_surface, (username_box.x + 5, username_box.y + 10))
        if username_active and blink:
            cursor_x = username_box.x + 5 + username_surface.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, username_box.y + 10), (cursor_x, username_box.y + 35), 2)
        pygame.draw.rect(screen, username_color, username_box, 2)

        # Password
        password_label = field_font.render("Password", True, (0, 0, 0))
        screen.blit(password_label, (password_box.x - password_label.get_width() - 20, password_box.y + 5))

        password_surface = field_font.render('*' * len(password), True, password_color)
        screen.blit(password_surface, (password_box.x + 5, password_box.y + 10))
        if password_active and blink:
            cursor_x = password_box.x + 5 + password_surface.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, password_box.y + 10), (cursor_x, password_box.y + 35), 2)
        pygame.draw.rect(screen, password_color, password_box, 2)

        # Error message
        if error_msg:
            error_surface = field_font.render(error_msg, True, (255, 0, 0))
            screen.blit(error_surface, (SCREEN_WIDTH // 2 - error_surface.get_width() // 2, password_box.y + 50))

        # Forgot Password link
        if show_forgot_password:
            forgot_text = forgot_font.render("Forgot Password?", True, (0, 0, 255))
            forgot_rect = forgot_text.get_rect(center=(password_box.x + 110, password_box.y + 90))
            screen.blit(forgot_text, forgot_rect)

        # Register link
        screen.blit(register_text, register_rect)

        pygame.display.flip()
        pygame.time.Clock().tick(30)

def register_user(screen, font, background, bg_x, bg_y):
    import pygame
    import sys
    from db import create_user, get_user
    from auth import get_user_login  # Import here so we can call back to login

    SCREEN_WIDTH = 1500
    SCREEN_HEIGHT = 800

    start_y = 250
    box_width = 220
    box_height = 40
    gap = 60
    left_x = 300

    field_font = pygame.font.SysFont("arial", 28, bold=True)
    title_font = pygame.font.SysFont("arial", 48, bold=True)

    link_font = pygame.font.SysFont("arial", 24, bold=False)
    back_to_login_text = link_font.render("Back to Login", True, (0, 0, 255))
    back_to_login_rect = back_to_login_text.get_rect()
    back_to_login_rect.topleft = (250, 550)

    input_box_user = pygame.Rect(left_x, start_y + gap * 0, box_width, box_height)
    input_box_pass = pygame.Rect(left_x, start_y + gap * 1, box_width, box_height)
    input_box_confirmpass = pygame.Rect(left_x, start_y + gap * 2, box_width, box_height)
    question_box = pygame.Rect(left_x, start_y + gap * 3, box_width, box_height)
    input_box_answ = pygame.Rect(left_x, start_y + gap * 4, box_width, box_height)

    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    active_field = None

    username = ""
    password = ""
    confirm_password = ""
    answer = ""
    selected_index = None
    error_msg = ""

    questions = [
        "Favorite color?",
        "Pet's name?",
        "Birth City?",
        "Favorite food?"
    ]
    dropdown_open = False

    clock = pygame.time.Clock()

    while True:
        screen.blit(background, (bg_x, bg_y))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_to_login_rect.collidepoint(event.pos):
                    get_user_login(screen, font, background, bg_x, bg_y)
                    return
                if input_box_user.collidepoint(event.pos):
                    active_field = "user"
                    dropdown_open = False
                elif input_box_pass.collidepoint(event.pos):
                    active_field = "pass"
                    dropdown_open = False
                elif input_box_confirmpass.collidepoint(event.pos):
                    active_field = "confirmpass"
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
                if event.key == pygame.K_RETURN:
                    if active_field == "user":
                        active_field = "pass"
                    elif active_field == "pass":
                        active_field = "confirmpass"
                    elif active_field == "confirmpass":
                        active_field = "answ" if selected_index is not None else None
                    elif active_field == "answ":
                        if username.strip() and password.strip() and confirm_password.strip() and selected_index is not None and answer.strip():
                            if password != confirm_password:
                                error_msg = "Passwords do not match."
                            elif get_user(username.strip()) is not None:
                                error_msg = "Username already exists!"
                            else:
                                create_user(username.strip(), password.strip(), questions[selected_index], answer.strip())
                                return username.strip()
                        else:
                            error_msg = "All fields are required."

                elif event.key == pygame.K_BACKSPACE:
                    if active_field == "user":
                        username = username[:-1]
                    elif active_field == "pass":
                        password = password[:-1]
                    elif active_field == "confirmpass":
                        confirm_password = confirm_password[:-1]
                    elif active_field == "answ":
                        answer = answer[:-1]

                elif len(event.unicode) == 1 and event.unicode.isprintable():
                    if active_field == "user":
                        username += event.unicode
                    elif active_field == "pass":
                        password += event.unicode
                    elif active_field == "confirmpass":
                        confirm_password += event.unicode
                    elif active_field == "answ":
                        answer += event.unicode

        # Title
        prompt = title_font.render("Registration Page", True, (0, 0, 0))
        screen.blit(prompt, (650, 80))

        # Input fields
        fields = [
            (input_box_user, username, active_field == "user"),
            (input_box_pass, '*' * len(password), active_field == "pass"),
            (input_box_confirmpass, '*' * len(confirm_password), active_field == "confirmpass")
        ]

        if selected_index is not None:
            fields.append((input_box_answ, answer, active_field == "answ"))

        blink = pygame.time.get_ticks() // 500 % 2  # 0 or 1 every 500ms

        for rect, text, is_active in fields:
            color = color_active if is_active else color_inactive
            text_color = color  # Match border and text color
            txt_surface = field_font.render(text, True, text_color)
            rect.w = box_width
            screen.blit(txt_surface, (rect.x + 5, rect.y + 6))  # shift up

            # Blinking cursor
            if is_active and blink:
                cursor_x = rect.x + 5 + txt_surface.get_width()
                cursor_y = rect.y + 10
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 25), 2)

            pygame.draw.rect(screen, color, rect, 2)

        # Dropdown
        draw_dropdown(screen, question_box, field_font, questions, selected_index, dropdown_open)

        # Labels
        labels = ["Username", "Password", "Confirm Password", "Security Question"]
        boxes = [input_box_user, input_box_pass, input_box_confirmpass, question_box]
        if selected_index is not None:
            labels.append("Your Answer")
            boxes.append(input_box_answ)

        for label, box in zip(labels, boxes):
            label_surface = field_font.render(label, True, (0, 0, 0))
            screen.blit(label_surface, (box.x - label_surface.get_width() - 20, box.y + 5))

        if error_msg:
            error_surface = field_font.render(error_msg, True, (255, 0, 0))
            screen.blit(error_surface, (SCREEN_WIDTH // 2 - error_surface.get_width() // 2, SCREEN_HEIGHT // 2 + 130))

        # Draw "Back to Login" link
        screen.blit(back_to_login_text, back_to_login_rect.topleft)

        pygame.display.flip()
        clock.tick(30)

def handle_forgot_password(screen, font, background, bg_x, bg_y):
    import pygame
    import sys
    from db import get_user_question, verify_security_answer, update_user_password
    from auth import get_user_login

    SCREEN_WIDTH = 1500
    SCREEN_HEIGHT = 800

    field_font = pygame.font.SysFont("arial", 28, bold=True)
    title_font = pygame.font.SysFont("arial", 48, bold=True)
    link_font = pygame.font.SysFont("arial", 24, bold=False)

    username = ""
    answer = ""
    new_password = ""
    stage = "username"  # stages: username -> question -> new_password
    error_msg = ""
    security_question = None
    success_msg = ""

    username_box = pygame.Rect(300, 280, 300, 40)
    answer_box = pygame.Rect(300, 340, 300, 40)
    password_box = pygame.Rect(300, 400, 300, 40)

    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    active_field = "username"

    back_to_login_text = link_font.render("Back to Login", True, (0, 0, 255))
    back_to_login_rect = back_to_login_text.get_rect(topleft=(320, 550))

    clock = pygame.time.Clock()

    while True:
        screen.blit(background, (bg_x, bg_y))
        blink = pygame.time.get_ticks() // 500 % 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_to_login_rect.collidepoint(event.pos):
                    get_user_login(screen, font, background, bg_x, bg_y)
                    return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if stage == "username":
                        if username.strip():
                            security_question = get_user_question(username.strip())
                            if security_question:
                                stage = "question"
                                active_field = "answer"
                            else:
                                error_msg = "Username not found."
                    elif stage == "question":
                        if answer.strip():
                            if verify_security_answer(username.strip(), answer.strip()):
                                stage = "new_password"
                                active_field = "new_password"
                            else:
                                error_msg = "Incorrect answer."
                    elif stage == "new_password":
                        if new_password.strip():
                            update_user_password(username.strip(), new_password.strip())
                            success_msg = "Password updated successfully!"
                            return

                elif event.key == pygame.K_BACKSPACE:
                    if active_field == "username":
                        username = username[:-1]
                    elif active_field == "answer":
                        answer = answer[:-1]
                    elif active_field == "new_password":
                        new_password = new_password[:-1]

                else:
                    if event.unicode.isprintable():
                        if active_field == "username":
                            username += event.unicode
                        elif active_field == "answer":
                            answer += event.unicode
                        elif active_field == "new_password":
                            new_password += event.unicode

        # Title
        prompt = title_font.render("Forgot Password", True, (0, 0, 0))
        screen.blit(prompt, (600, 80))

        # Fields
        if stage == "username":
            pygame.draw.rect(screen, color_active, username_box, 2)
            input_surface = field_font.render(username, True, color_active)
            screen.blit(input_surface, (username_box.x + 5, username_box.y + 10))

            if active_field == "username" and blink:
                cursor_x = username_box.x + 5 + input_surface.get_width()
                cursor_y = username_box.y + 10
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 25), 2)

            label = field_font.render("Enter your username:", True, (0, 0, 0))
            screen.blit(label, (username_box.x - label.get_width() - 10, username_box.y + 5))

        elif stage == "question":
            pygame.draw.rect(screen, color_active, answer_box, 2)
            input_surface = field_font.render(answer, True, color_active)
            screen.blit(input_surface, (answer_box.x + 5, answer_box.y + 10))

            if active_field == "answer" and blink:
                cursor_x = answer_box.x + 5 + input_surface.get_width()
                cursor_y = answer_box.y + 10
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 25), 2)

            label = field_font.render(security_question, True, (0, 0, 0))
            screen.blit(label, (answer_box.x - label.get_width() - 10, answer_box.y + 5))

        elif stage == "new_password":
            pygame.draw.rect(screen, color_active, password_box, 2)
            input_surface = field_font.render('*' * len(new_password), True, color_active)
            screen.blit(input_surface, (password_box.x + 5, password_box.y + 10))

            if active_field == "new_password" and blink:
                cursor_x = password_box.x + 5 + input_surface.get_width()
                cursor_y = password_box.y + 10
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 25), 2)

            label = field_font.render("New password:", True, (0, 0, 0))
            screen.blit(label, (password_box.x - label.get_width() - 10, password_box.y + 5))

        # Error or Success messages
        if error_msg:
            error_surface = field_font.render(error_msg, True, (255, 0, 0))
            screen.blit(error_surface, (SCREEN_WIDTH // 2 - error_surface.get_width() // 2, 500))

        if success_msg:
            success_surface = field_font.render(success_msg, True, (0, 200, 0))
            screen.blit(success_surface, (SCREEN_WIDTH // 2 - success_surface.get_width() // 2, 550))

        # Draw Back to Login link
        screen.blit(back_to_login_text, back_to_login_rect.topleft)

        pygame.display.flip()
        clock.tick(30)

def is_admin(username: str) -> bool:
    return username.strip().lower() == "yousuf"



