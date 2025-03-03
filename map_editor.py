import pygame
import os
import math
import random
from pygame.locals import *
from PIL import Image

# Adjustable parameters
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800
ROAD_WIDTH = 80  # Road width in pixels
DASH_LENGTH = 10  # Length of each dash in the center line
GAP_LENGTH = 20  # Gap between dashes
TREE_SPACING = 100  # Fixed spacing between trees (in pixels)
SNAP_DISTANCE = 10  # Minimum distance between successive points
CLOSE_THRESHOLD = 20  # Distance threshold to snap the end to the start and close the track

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (34, 139, 34)  # Tree color
GRAY = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Advanced Map Editor")
clock = pygame.time.Clock()

# Grab mouse events even if the cursor goes outside the window.
pygame.event.set_grab(True)

# Global drawing data (all stored in world coordinates)
points = []         # Raw centerline points drawn by the user.
preview_curve = []  # Smoothed centerline.
trees_left = []     # Trees on the left side.
trees_right = []    # Trees on the right side.

# Car starting position (world coordinate)
CAR_START_POS = (700, 700)

# Camera settings for infinite canvas
camera_offset = [0, 0]  # (x, y) offset in world coordinates
CAMERA_EDGE_MARGIN = 100  # Margin (in screen pixels) within which camera will pan
CAMERA_PAN_SPEED = 5      # Maximum pan speed (pixels per frame)


def world_to_screen(point):
    """Convert a world coordinate to a screen coordinate using the camera offset."""
    return (point[0] - camera_offset[0], point[1] - camera_offset[1])


def catmull_rom_spline(P, nPoints=100):
    """Return nPoints interpolated along a Catmull–Rom spline given control points P."""
    if len(P) < 4:
        return P

    def CR_point(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        return (
            0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                   (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
            0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                   (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        )

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


def compute_offset_curve(curve, offset):
    """
    Given a curve (list of points) and an offset (in pixels), compute a new curve offset perpendicularly.
    """
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


def draw_dashed_line(surface, color, points, dash_length, gap_length):
    """
    Draw a dashed line along the given list of points.
    """
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
            dash = dash_length if draw_dash else gap_length
            seg_end_x = start[0] + dx * min(dash, seg_length - dist)
            seg_end_y = start[1] + dy * min(dash, seg_length - dist)
            if draw_dash:
                pygame.draw.line(surface, color,
                                 (start[0] + dx * dist, start[1] + dy * dist),
                                 (seg_end_x, seg_end_y), 2)
            dist += dash
            draw_dash = not draw_dash


def generate_trees(curve, side_offset, spacing=TREE_SPACING):
    """
    Generate tree positions along the offset curve at fixed intervals.
    """
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


def save_map(curve, left_trees, right_trees):
    """
    Save the entire drawn map to an image file.
    This version computes the bounding box that encloses the entire map and
    renders everything onto a new surface of that size.
    The file is saved with an automatically incremented filename based on existing maps.
    """
    if not curve:
        return

    # Compute road edges.
    left_edge = compute_offset_curve(curve, ROAD_WIDTH / 2)
    right_edge = compute_offset_curve(curve, -ROAD_WIDTH / 2)
    # Combine all relevant points.
    all_points = curve + left_edge + right_edge + left_trees + right_trees
    margin = 50  # Add some extra space around the map.
    min_x = min(p[0] for p in all_points) - margin
    max_x = max(p[0] for p in all_points) + margin
    min_y = min(p[1] for p in all_points) - margin
    max_y = max(p[1] for p in all_points) + margin

    width = int(max_x - min_x)
    height = int(max_y - min_y)

    map_surface = pygame.Surface((width, height))
    map_surface.fill(WHITE)

    # Helper to convert world coordinates to coordinates on the new surface.
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
    start_pos = world_to_map(curve[0])
    finish_pos = world_to_map(curve[-1])
    map_surface.blit(start_text, (start_pos[0], start_pos[1] - 40))
    map_surface.blit(finish_text, (finish_pos[0], finish_pos[1] - 40))

    map_data = pygame.image.tostring(map_surface, 'RGBA')
    img = Image.frombytes('RGBA', (width, height), map_data)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    maps_dir = os.path.join(script_dir, "maps")
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)

    # Determine next available file name.
    existing_files = os.listdir(maps_dir)
    numbers = []
    for f in existing_files:
        if f.startswith("map") and f.endswith(".png"):
            num_part = f[3:-4]  # Extract the number part; for "map.png" this will be an empty string.
            if num_part == "":
                numbers.append(0)
            else:
                try:
                    numbers.append(int(num_part))
                except ValueError:
                    pass
    next_number = max(numbers) + 1 if numbers else 0
    if next_number == 0:
        file_name = "map.png"
    else:
        file_name = f"map{next_number}.png"

    file_path = os.path.join(maps_dir, file_name)
    img.save(file_path)
    print(f"Map saved as {file_path}")


def draw_curve(surface, curve):
    """Draw the smooth centerline and dashed yellow center line."""
    if len(curve) > 1:
        pygame.draw.lines(surface, GRAY, False, curve, 2)
        draw_dashed_line(surface, YELLOW, curve, DASH_LENGTH, GAP_LENGTH)


def draw_preview_points(surface, pts):
    """Draw preview points as small gray circles."""
    for p in pts:
        pygame.draw.circle(surface, GRAY, p, 5)


def main():
    global points, preview_curve, trees_left, trees_right, camera_offset
    running = True
    drawing = False  # Indicates whether the left mouse button is held.
    font = pygame.font.SysFont("Arial", 20)

    while running:
        screen.fill(WHITE)

        # --- Smooth Camera Panning ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x < CAMERA_EDGE_MARGIN:
            pan_speed = (CAMERA_EDGE_MARGIN - mouse_x) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[0] -= pan_speed
        elif mouse_x > SCREEN_WIDTH - CAMERA_EDGE_MARGIN:
            pan_speed = (mouse_x - (SCREEN_WIDTH - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[0] += pan_speed
        if mouse_y < CAMERA_EDGE_MARGIN:
            pan_speed = (CAMERA_EDGE_MARGIN - mouse_y) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[1] -= pan_speed
        elif mouse_y > SCREEN_HEIGHT - CAMERA_EDGE_MARGIN:
            pan_speed = (mouse_y - (SCREEN_HEIGHT - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[1] += pan_speed

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    drawing = True
                    # Start drawing at the current mouse position in world coordinates.
                    start_pos = (pygame.mouse.get_pos()[0] + camera_offset[0],
                                 pygame.mouse.get_pos()[1] + camera_offset[1])
                    points.append(start_pos)

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False

            elif event.type == KEYDOWN:
                if event.key == K_s:
                    if preview_curve:
                        save_map(preview_curve, trees_left, trees_right)
                elif event.key == K_c:
                    points = []
                    preview_curve = []
                    trees_left = []
                    trees_right = []
                elif event.key == K_e:
                    running = False

        # --- Update Drawing ---
        if drawing:
            current_point = (pygame.mouse.get_pos()[0] + camera_offset[0],
                             pygame.mouse.get_pos()[1] + camera_offset[1])
            if not points or math.hypot(current_point[0] - points[-1][0],
                                        current_point[1] - points[-1][1]) >= SNAP_DISTANCE:
                points.append(current_point)
            if len(points) >= 3 and math.hypot(current_point[0] - points[0][0],
                                               current_point[1] - points[0][1]) < CLOSE_THRESHOLD:
                points.append(points[0])
                drawing = False

        # --- Update Curves and Trees ---
        if len(points) >= 2:
            pts = points if len(points) >= 4 else [points[0]] + points + [points[-1]]
            preview_curve = catmull_rom_spline(pts, nPoints=30)
            trees_left = generate_trees(preview_curve, ROAD_WIDTH / 2 + 10, spacing=TREE_SPACING)
            trees_right = generate_trees(preview_curve, -ROAD_WIDTH / 2 - 10, spacing=TREE_SPACING)

        # --- Drawing on Screen ---
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
            font_large = pygame.font.SysFont("Arial", 30)
            start_text = font_large.render("Start", True, YELLOW)
            finish_text = font_large.render("Finish", True, YELLOW)
            start_pos = world_to_screen(preview_curve[0])
            finish_pos = world_to_screen(preview_curve[-1])
            screen.blit(start_text, (start_pos[0], start_pos[1] - 40))
            screen.blit(finish_text, (finish_pos[0], finish_pos[1] - 40))
            instr = font.render("Hold left mouse button and drag to draw. Press S to save, C to clear, E to exit.",
                                True, BLACK)
            screen.blit(instr, (20, SCREEN_HEIGHT - 40))
        else:
            instr = font.render("Hold left mouse button and drag to draw. Press E to exit.", True, BLACK)
            screen.blit(instr, (20, SCREEN_HEIGHT - 40))

        pygame.draw.circle(screen, BLACK, world_to_screen(CAR_START_POS), 5)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
