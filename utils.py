import pygame
import sys
import os
from typing import List
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT

# Colors and constants used by the utility functions.
LightGreen = (144, 238, 144)
Black = (0, 0, 0)
Red = (255, 0, 0)
White = (255, 255, 255)
CONSTANT_SPEED = 5
TRACK_WIDTH = 80  # Used for finish area drawing

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
        return float('inf')

    return sorted(files, key=sort_key)

def load_map_metadata(map_path: str):
    import json  # Local import to avoid global usage
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_dir = os.path.join(script_dir, "startfinish")
    base = os.path.splitext(os.path.basename(map_path))[0]
    metadata_filename = base + "_metadata.json"
    metadata_path = os.path.join(metadata_dir, metadata_filename)
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            return json.load(f)
    return None

# (All remaining functions like select_map, draw_map_button, dropdown_map_selection,
#  drag_and_drop_starting_position remain unchanged — no edits required)


def select_map(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    selected_index = 0
    option_width = 200
    option_height = 35
    option_x = 50
    option_y = 120
    option_spacing = 10
    preview_width = 300
    preview_height = 200
    preview_x = option_x + option_width + 50
    preview_y = option_y
    clock = pygame.time.Clock()
    selecting = True
    while selecting:
        screen.fill(LightGreen)
        title_text = font.render("Select a Map:", True, (0, 0, 0))
        screen.blit(title_text, (option_x, option_y - 50))
        mouse_pos = pygame.mouse.get_pos()
        sorted_files = get_sorted_map_files()
        for i, file in enumerate(sorted_files):
            base, _ = os.path.splitext(file)
            label = base.capitalize()
            rect = pygame.Rect(option_x, option_y + i * (option_height + option_spacing), option_width, option_height)
            if rect.collidepoint(mouse_pos):
                selected_index = i
            color = (255, 0, 0) if i == selected_index else (240, 240, 240)
            text_color = White if i == selected_index else Black
            pygame.draw.rect(screen, color, rect, border_radius=8)
            text = font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))
        pygame.draw.rect(screen, Black, (preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10), 2)
        try:
            preview_image = pygame.image.load(os.path.join("maps", sorted_files[selected_index])).convert_alpha()
            preview_image = pygame.transform.scale(preview_image, (preview_width, preview_height))
            screen.blit(preview_image, (preview_x, preview_y))
        except Exception:
            pass
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(sorted_files)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(sorted_files)
                elif event.key == pygame.K_RETURN:
                    selecting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(sorted_files)):
                    rect = pygame.Rect(option_x, option_y + i * (option_height + option_spacing), option_width, option_height)
                    if rect.collidepoint(event.pos):
                        selected_index = i
                        selecting = False
                        break
        clock.tick(60)
    return os.path.join("maps", sorted_files[selected_index])

def draw_map_button(screen: pygame.Surface, font: pygame.font.Font, current_map: str = None) -> pygame.Rect:
    sorted_files = get_sorted_map_files()
    if current_map is None:
        current_map = sorted_files[0]
    base, _ = os.path.splitext(current_map)
    label = base.capitalize()
    img = pygame.image.load("assets/simulate.png")
    img = pygame.transform.scale(img, (100, 40))
    from button import Button  # Import here if Button is defined elsewhere.
    btn = Button(image=img, pos=(SCREEN_WIDTH - 60, 30),
                 text_input=label, font=font, base_color="#d7fcd4", hovering_color="White")
    btn.update(screen)
    return btn.rect

def draw_manual_mode_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    img = pygame.image.load("assets/simulate.png")
    img = pygame.transform.scale(img, (150, 40))
    pos = (10 + 150 // 2, 10 + 40 // 2)
    from button import Button  # Import here if Button is defined elsewhere.
    btn = Button(image=img, pos=pos, text_input="Manual Mode",
                 font=font, base_color="#d7fcd4", hovering_color="White")
    btn.update(screen)
    return btn.rect

def dropdown_map_selection(screen: pygame.Surface, font: pygame.font.Font) -> str:
    maps_folder = "maps"
    if not os.path.exists(maps_folder):
        print("Error: 'maps' folder not found.")
        sys.exit(1)
    map_files = get_sorted_map_files()
    if not map_files:
        print("Error: No map files found in the 'maps' folder.")
        sys.exit(1)
    selected_index = 0
    popup_width = 250
    popup_height = 30 * len(map_files) + 20
    popup_x = SCREEN_WIDTH - popup_width - 20
    popup_y = 60
    option_width = popup_width - 20
    option_height = 30
    option_start_x = popup_x + 10
    option_start_y = popup_y + 10
    preview_width = 300
    preview_height = 200
    preview_x = popup_x - preview_width - 20
    preview_y = popup_y
    clock = pygame.time.Clock()
    active = True
    while active:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(screen, (240, 240, 240), popup_rect, border_radius=8)
        pygame.draw.rect(screen, Black, popup_rect, 2, border_radius=8)
        mouse_pos = pygame.mouse.get_pos()
        for i, file in enumerate(map_files):
            base, _ = os.path.splitext(file)
            label = base.capitalize()
            rect = pygame.Rect(option_start_x, option_start_y + i * option_height, option_width, option_height)
            if rect.collidepoint(mouse_pos):
                selected_index = i
            color = Red if i == selected_index else (240, 240, 240)
            text_color = White if i == selected_index else Black
            pygame.draw.rect(screen, color, rect, border_radius=8)
            text = font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))
        preview_box = pygame.Rect(preview_x - 5, preview_y - 5, preview_width + 10, preview_height + 10)
        pygame.draw.rect(screen, Black, preview_box, 2)
        try:
            preview = pygame.image.load(os.path.join(maps_folder, map_files[selected_index])).convert_alpha()
            preview = pygame.transform.scale(preview, (preview_width, preview_height))
            screen.blit(preview, (preview_x, preview_y))
        except Exception:
            pass
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(map_files)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(map_files)
                elif event.key == pygame.K_RETURN:
                    active = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(map_files)):
                    rect = pygame.Rect(option_start_x, option_start_y + i * option_height, option_width, option_height)
                    if rect.collidepoint(event.pos):
                        selected_index = i
                        active = False
                        break
                if not popup_rect.collidepoint(event.pos):
                    active = False
        clock.tick(60)
    return os.path.join(maps_folder, map_files[selected_index])

def drag_and_drop_starting_position(screen: pygame.Surface, info_font: pygame.font.Font,
                                    collision_mask: pygame.mask.Mask, display_map: pygame.Surface,
                                    drag_car: Car = None) -> list:
    if drag_car is None:
        drag_car = Car()

    initial_default = drag_car.pos.copy()
    dragging = False
    valid = False
    message = ""
    clock = pygame.time.Clock()
    while not valid:
        screen.fill(LightGreen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                car_rect = pygame.Rect(drag_car.pos[0], drag_car.pos[1], 100, 100)
                if car_rect.collidepoint(mouse_pos):
                    dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                drag_car.update(display_map, collision_mask)
                if drag_car.get_alive() and drag_car.pos != initial_default:
                    valid = True
                else:
                    message = "Please reposition the car on the track!"
            elif event.type == pygame.MOUSEMOTION and dragging:
                new_x = event.pos[0] - 50
                new_y = event.pos[1] - 50
                drag_car.pos[0] = new_x
                drag_car.pos[1] = new_y
                drag_car.center = [int(new_x + drag_car.surface.get_width() / 2),
                                   int(new_y + drag_car.surface.get_height() / 2)]
        screen.blit(display_map, (0, 0))
        drag_car.draw(screen, info_font, draw_radars=False)
        if message:
            msg = info_font.render(message, True, (255, 0, 0))
            screen.blit(msg, (50, 50))
        pygame.display.flip()
        clock.tick(60)
    return drag_car.pos.copy()
