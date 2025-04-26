import pygame
import os
import math
import json
from pygame.locals import *
from PIL import Image
def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

def draw_button(screen, rect, text, font, hover=False):
    color = (255, 255, 255) if hover else (200, 200, 200)
    pygame.draw.rect(screen, color, rect, border_radius=5)
    pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=5)
    label = font.render(text, True, (0, 0, 0))
    screen.blit(label, label.get_rect(center=rect.center))


# screen setup
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800
ROAD_WIDTH = 80
DASH_LENGTH = 10
GAP_LENGTH = 20
TREE_SPACING = 100
SNAP_DISTANCE = 10
CLOSE_THRESHOLD = 20

# colors
LightGreen = (144, 238, 144)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (34, 139, 34)
GRAY = (200, 200, 200)

# setup pygame screen
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Map Editor")
clock = pygame.time.Clock()
pygame.event.set_grab(True)

# data lists
points = []
preview_curve = []
trees_left = []
trees_right = []
CAR_START_POS = (700, 700)

# camera variables
camera_offset = [0, 0]
CAMERA_EDGE_MARGIN = 100
CAMERA_PAN_SPEED = 60

# convert world to screen
def world_to_screen(point):
    return point[0] - camera_offset[0], point[1] - camera_offset[1]

# make smooth curve
def catmull_rom_spline(P, nPoints=100):
    if len(P) < 4:
        return P

    def CR_point(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                   (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                   (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                   (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                   (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        return (x, y)

    spline_points = []
    for i in range(-1, len(P) - 2):
        p0 = P[max(i, 0)]
        p1 = P[i + 1]
        p2 = P[i + 2]
        p3 = P[min(i + 3, len(P) - 1)]
        for t in [j / nPoints for j in range(nPoints)]:
            spline_points.append(CR_point(p0, p1, p2, p3, t))
    spline_points.append(P[-1])
    return spline_points

# make edge of road
def compute_offset_curve(curve, offset):
    offset_points = []
    for i in range(len(curve)):
        if i == 0:
            dx = curve[i + 1][0] - curve[i][0]
            dy = curve[i + 1][1] - curve[i][1]
        elif i == len(curve) - 1:
            dx = curve[i][0] - curve[i - 1][0]
            dy = curve[i][1] - curve[i - 1][1]
        else:
            dx = curve[i + 1][0] - curve[i - 1][0]
            dy = curve[i + 1][1] - curve[i - 1][1]
        length = math.hypot(dx, dy)
        if length == 0:
            perp = (0, 0)
        else:
            perp = (-dy / length, dx / length)
        offset_points.append((curve[i][0] + perp[0] * offset, curve[i][1] + perp[1] * offset))
    return offset_points

# draw yellow dashed center line
def draw_dashed_line(surface, color, points, dash_length, gap_length):
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        seg_length = math.hypot(end[0] - start[0], end[1] - start[1])
        if seg_length == 0:
            continue
        dx = (end[0] - start[0]) / seg_length
        dy = (end[1] - start[1]) / seg_length
        dist = 0
        draw_dash = True
        while dist < seg_length:
            current_dash = dash_length if draw_dash else gap_length
            seg_end_x = start[0] + dx * min(current_dash, seg_length - dist)
            seg_end_y = start[1] + dy * min(current_dash, seg_length - dist)
            if draw_dash:
                pygame.draw.line(surface, color,
                                 (start[0] + dx * dist, start[1] + dy * dist),
                                 (seg_end_x, seg_end_y), 2)
            dist += current_dash
            draw_dash = not draw_dash

# make trees on side
def generate_trees(curve, side_offset, spacing=TREE_SPACING):
    offset_curve = compute_offset_curve(curve, side_offset)
    tree_positions = []
    if not offset_curve:
        return tree_positions
    cumulative_distance = 0
    last_pos = offset_curve[0]
    tree_positions.append(last_pos)
    for pos in offset_curve[1:]:
        dx = pos[0] - last_pos[0]
        dy = pos[1] - last_pos[1]
        d = math.hypot(dx, dy)
        cumulative_distance += d
        if cumulative_distance >= spacing:
            tree_positions.append(pos)
            cumulative_distance = 0
        last_pos = pos
    return tree_positions

# save map and trees
def save_map(curve, left_trees, right_trees):
    if not curve:
        return
    left_edge = compute_offset_curve(curve, ROAD_WIDTH / 2)
    right_edge = compute_offset_curve(curve, -ROAD_WIDTH / 2)
    all_points = curve + left_edge + right_edge + left_trees + right_trees
    margin = 50
    min_x = min(p[0] for p in all_points) - margin
    max_x = max(p[0] for p in all_points) + margin
    min_y = min(p[1] for p in all_points) - margin
    max_y = max(p[1] for p in all_points) + margin

    width = int(max_x - min_x)
    height = int(max_y - min_y)

    map_surface = pygame.Surface((width, height))
    map_surface.fill(LightGreen)

    def world_to_map(point):
        return (point[0] - min_x, point[1] - min_y)

    road_polygon = [world_to_map(p) for p in (left_edge + right_edge[::-1])]
    pygame.draw.polygon(map_surface, BLACK, road_polygon)
    draw_dashed_line(map_surface, YELLOW, [world_to_map(p) for p in curve], DASH_LENGTH, GAP_LENGTH)
    for tree in left_trees + right_trees:
        pygame.draw.circle(map_surface, GREEN, world_to_map(tree), 5)

    font_large = pygame.font.SysFont("Arial", 30)
    start_text = font_large.render("Start", True, YELLOW)
    finish_text = font_large.render("Finish", True, YELLOW)
    map_surface.blit(start_text, (world_to_map(curve[0])[0], world_to_map(curve[0])[1] - 40))
    map_surface.blit(finish_text, (world_to_map(curve[-1])[0], world_to_map(curve[-1])[1] - 40))

    map_data = pygame.image.tostring(map_surface, 'RGBA')
    img = Image.frombytes('RGBA', (width, height), map_data)
    maps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)

    existing_files = os.listdir(maps_dir)
    numbers = [int(f[3:-4]) for f in existing_files if f.startswith("map") and f.endswith(".png") and f[3:-4].isdigit()]
    next_number = max(numbers) + 1 if numbers else 0
    file_name = "map.png" if next_number == 0 else f"map{next_number}.png"
    file_path = os.path.join(maps_dir, file_name)
    img.save(file_path)
    print(f"Map saved as {file_path}")

    metadata = {
        "start": world_to_map(curve[0]),
        "finish": world_to_map(curve[-1]),
    }
    startfinish_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startfinish")
    if not os.path.exists(startfinish_dir):
        os.makedirs(startfinish_dir)
    metadata_path = os.path.join(startfinish_dir, os.path.splitext(file_name)[0] + "_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)
    print(f"Metadata saved as {metadata_path}")

# show the road lines
def draw_curve(surface, curve):
    if len(curve) > 1:
        pygame.draw.lines(surface, GRAY, False, curve, 2)
        draw_dashed_line(surface, YELLOW, curve, DASH_LENGTH, GAP_LENGTH)

# show preview points
def draw_preview_points(surface, pts):
    for p in pts:
        pygame.draw.circle(surface, GRAY, p, 5)

# start the program
def main(user_id=None, username="Guest", is_admin=False):
    global points, preview_curve, trees_left, trees_right, camera_offset
    running = True
    drawing = False
    font = pygame.font.SysFont("Arial", 20)
    menu_font = pygame.font.SysFont("Arial", 28)
    main_menu_btn = pygame.Rect(20, 20, 160, 40)

    while running:
        screen.fill(LightGreen)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # move camera
        if mouse_x < CAMERA_EDGE_MARGIN:
            camera_offset[0] -= (CAMERA_EDGE_MARGIN - mouse_x) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
        elif mouse_x > SCREEN_WIDTH - CAMERA_EDGE_MARGIN:
            camera_offset[0] += (mouse_x - (SCREEN_WIDTH - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
        if mouse_y < CAMERA_EDGE_MARGIN:
            camera_offset[1] -= (CAMERA_EDGE_MARGIN - mouse_y) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
        elif mouse_y > SCREEN_HEIGHT - CAMERA_EDGE_MARGIN:
            camera_offset[1] += (mouse_y - (SCREEN_HEIGHT - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                if main_menu_btn.collidepoint(pygame.mouse.get_pos()):
                    pygame.quit()
                    from main import main_menu
                    main_menu(user_id, username, is_admin)

                    return
                drawing = True
                start_pos = (mouse_x + camera_offset[0], mouse_y + camera_offset[1])
                points.append(start_pos)


            elif event.type == MOUSEBUTTONUP and event.button == 1:
                drawing = False
            elif event.type == KEYDOWN:
                if event.key == K_s and preview_curve:
                    save_map(preview_curve, trees_left, trees_right)
                elif event.key == K_c:
                    points.clear()
                    preview_curve.clear()
                    trees_left.clear()
                    trees_right.clear()
                elif event.key == K_e:
                    running = False

        # add points when mouse held
        if drawing:
            current_point = (mouse_x + camera_offset[0], mouse_y + camera_offset[1])
            if not points or math.hypot(current_point[0] - points[-1][0],
                                        current_point[1] - points[-1][1]) >= SNAP_DISTANCE:
                points.append(current_point)
            if len(points) >= 3 and math.hypot(current_point[0] - points[0][0],
                                               current_point[1] - points[0][1]) < CLOSE_THRESHOLD:
                points.append(points[0])
                drawing = False

        # update preview and tree positions
        if len(points) >= 2:
            pts = points if len(points) >= 4 else [points[0]] + points + [points[-1]]
            preview_curve = catmull_rom_spline(pts, nPoints=30)
            trees_left = generate_trees(preview_curve, ROAD_WIDTH / 2 + 10)
            trees_right = generate_trees(preview_curve, -ROAD_WIDTH / 2 - 10)

        for p in points:
            pygame.draw.circle(screen, BLACK, world_to_screen(p), 5)
        draw_preview_points(screen, [world_to_screen(p) for p in points])

        if preview_curve:
            left_edge = compute_offset_curve(preview_curve, ROAD_WIDTH / 2)
            right_edge = compute_offset_curve(preview_curve, -ROAD_WIDTH / 2)
            road_polygon = [world_to_screen(p) for p in (left_edge + right_edge[::-1])]
            pygame.draw.polygon(screen, BLACK, road_polygon)
            draw_dashed_line(screen, YELLOW, [world_to_screen(p) for p in preview_curve], DASH_LENGTH, GAP_LENGTH)
            for tree in trees_left + trees_right:
                pygame.draw.circle(screen, GREEN, world_to_screen(tree), 5)
            draw_curve(screen, [world_to_screen(p) for p in preview_curve])
            draw_button(screen, main_menu_btn, "Main Menu", menu_font, main_menu_btn.collidepoint(mouse_x, mouse_y))

            font_large = pygame.font.SysFont("Arial", 30)
            screen.blit(font_large.render("Start", True, YELLOW), (world_to_screen(preview_curve[0])[0], world_to_screen(preview_curve[0])[1] - 40))
            screen.blit(font_large.render("Finish", True, YELLOW), (world_to_screen(preview_curve[-1])[0], world_to_screen(preview_curve[-1])[1] - 40))

            msg = "Hold left mouse button and drag to draw. Press S to save, C to clear, E to exit."
        else:
            msg = "Hold left mouse button and drag to draw. Press E to exit."
        screen.blit(font.render(msg, True, BLACK), (20, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
def run_map_editor(user_id=None, username="Guest", is_admin=False):
    pygame.quit()
    pygame.init()
    global screen, clock
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map Editor")
    clock = pygame.time.Clock()
    main(user_id, username, is_admin)




