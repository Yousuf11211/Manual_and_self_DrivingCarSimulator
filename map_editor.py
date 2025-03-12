import pygame
import os
import math
import random
from pygame.locals import *
from PIL import Image

# ----------------------- Adjustable Parameters ----------------------- #
SCREEN_WIDTH = 1500  # Width of the window
SCREEN_HEIGHT = 800  # Height of the window
ROAD_WIDTH = 80  # Road width in pixels
DASH_LENGTH = 10  # Length of each dash in the center line
GAP_LENGTH = 20  # Gap between dashes in the center line
TREE_SPACING = 100  # Fixed spacing between trees (in pixels)
SNAP_DISTANCE = 10  # Minimum distance between successive drawn points
CLOSE_THRESHOLD = 20  # Distance threshold to automatically close the track

# ----------------------------- Colors ---------------------------------- #
WHITE = (144, 238, 144)  # Background color (light green)
BLACK = (0, 0, 0)  # Black color
YELLOW = (255, 255, 0)  # Yellow color (used for dashed lines and labels)
GREEN = (34, 139, 34)  # Green color for trees
GRAY = (200, 200, 200)  # Gray color for preview points and lines

# -------------------------- Pygame Initialization ---------------------- #
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Advanced Map Editor")
clock = pygame.time.Clock()

# Grab mouse events even if the cursor goes outside the window.
pygame.event.set_grab(True)

# ---------------------- Global Drawing Data -------------------------- #
points = []  # List to store raw centerline points (in world coordinates)
preview_curve = []  # Smoothed centerline using interpolation
trees_left = []  # List of tree positions on the left side of the road
trees_right = []  # List of tree positions on the right side of the road

# Car starting position (world coordinate)
CAR_START_POS = (700, 700)

# ------------------------- Camera Settings ----------------------------- #
camera_offset = [0, 0]  # Camera offset (x, y) in world coordinates
CAMERA_EDGE_MARGIN = 100  # Margin (in screen pixels) within which camera will pan
CAMERA_PAN_SPEED = 60  # Maximum pan speed (pixels per frame)


# ----------------------- Helper Functions ------------------------------ #
def world_to_screen(point):
    """
    Convert a point in world coordinates to screen coordinates using the camera offset.
    """
    return (point[0] - camera_offset[0], point[1] - camera_offset[1])


def catmull_rom_spline(P, nPoints=100):
    """
    Generate a smooth curve (spline) using the Catmull–Rom algorithm.

    Parameters:
        P (list): List of control points (tuples) in world coordinates.
        nPoints (int): Number of points to interpolate between control points.

    Returns:
        list: List of points along the smooth spline.
    """
    if len(P) < 4:
        return P

    def CR_point(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        # Calculate a new point on the spline using the Catmull-Rom formula.
        x = 0.5 * ((2 * p1[0]) +
                   (-p0[0] + p2[0]) * t +
                   (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                   (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
        y = 0.5 * ((2 * p1[1]) +
                   (-p0[1] + p2[1]) * t +
                   (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                   (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        return (x, y)

    spline_points = []
    # Iterate over segments of the control points
    for i in range(-1, len(P) - 2):
        p0 = P[max(i, 0)]
        p1 = P[i + 1]
        p2 = P[i + 2]
        p3 = P[min(i + 3, len(P) - 1)]
        # Interpolate between p1 and p2
        for t in [j / nPoints for j in range(nPoints)]:
            spline_points.append(CR_point(p0, p1, p2, p3, t))
    spline_points.append(P[-1])
    return spline_points


def compute_offset_curve(curve, offset):
    """
    Compute a curve that is offset from the original curve by a fixed distance.
    This is used to calculate road edges and tree positions.

    Parameters:
        curve (list): List of points along the centerline.
        offset (float): Distance to offset (positive for one side, negative for the other).

    Returns:
        list: List of offset points.
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
        # If there is no movement, set perpendicular to zero
        if length == 0:
            perp = (0, 0)
        else:
            # Calculate perpendicular vector (normalized)
            perp = (-dy / length, dx / length)
        # Offset the current point by the perpendicular vector scaled by the offset value
        offset_points.append((curve[i][0] + perp[0] * offset, curve[i][1] + perp[1] * offset))
    return offset_points


def draw_dashed_line(surface, color, points, dash_length, gap_length):
    """
    Draw a dashed line on the given surface along a list of points.

    Parameters:
        surface (pygame.Surface): Surface to draw on.
        color (tuple): Color of the dashes.
        points (list): List of points (tuples) to form the line.
        dash_length (int): Length of each dash.
        gap_length (int): Length of the gap between dashes.
    """
    if len(points) < 2:
        return
    # Draw each segment between consecutive points
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


def generate_trees(curve, side_offset, spacing=TREE_SPACING):
    """
    Generate tree positions along a side of the road at fixed intervals.

    Parameters:
        curve (list): The centerline curve of the road.
        side_offset (float): The offset from the centerline (positive for left side, negative for right).
        spacing (int): Distance between trees.

    Returns:
        list: List of positions for trees.
    """
    offset_curve = compute_offset_curve(curve, side_offset)
    tree_positions = []
    if not offset_curve:
        return tree_positions
    cumulative_distance = 0
    last_pos = offset_curve[0]
    tree_positions.append(last_pos)
    # Walk along the offset curve and place trees at fixed intervals.
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
    Save the drawn map to an image file.
    This function calculates the bounding box for the entire map,
    draws the road, dashed centerline, trees, and start/finish labels,
    and saves the result as a PNG image in the "maps" folder.
    """
    if not curve:
        return

    # Compute the left and right edges of the road based on the centerline.
    left_edge = compute_offset_curve(curve, ROAD_WIDTH / 2)
    right_edge = compute_offset_curve(curve, -ROAD_WIDTH / 2)
    # Combine all points to compute the bounding box.
    all_points = curve + left_edge + right_edge + left_trees + right_trees
    margin = 50  # Extra margin around the map.
    min_x = min(p[0] for p in all_points) - margin
    max_x = max(p[0] for p in all_points) + margin
    min_y = min(p[1] for p in all_points) - margin
    max_y = max(p[1] for p in all_points) + margin

    width = int(max_x - min_x)
    height = int(max_y - min_y)

    # Create a new surface for the map image.
    map_surface = pygame.Surface((width, height))
    map_surface.fill(WHITE)

    def world_to_map(point):
        """Convert world coordinates to the new map image coordinates."""
        return (point[0] - min_x, point[1] - min_y)

    # Draw the road polygon.
    road_polygon = [world_to_map(p) for p in (left_edge + right_edge[::-1])]
    pygame.draw.polygon(map_surface, BLACK, road_polygon)
    # Draw the dashed centerline.
    draw_dashed_line(map_surface, YELLOW, [world_to_map(p) for p in curve], DASH_LENGTH, GAP_LENGTH)
    # Draw trees.
    for tree in left_trees + right_trees:
        pygame.draw.circle(map_surface, GREEN, world_to_map(tree), 5)
    # Draw start and finish labels.
    font_large = pygame.font.SysFont("Arial", 30)
    start_text = font_large.render("Start", True, YELLOW)
    finish_text = font_large.render("Finish", True, YELLOW)
    start_pos = world_to_map(curve[0])
    finish_pos = world_to_map(curve[-1])
    map_surface.blit(start_text, (start_pos[0], start_pos[1] - 40))
    map_surface.blit(finish_text, (finish_pos[0], finish_pos[1] - 40))

    # Save the surface as an image using PIL.
    map_data = pygame.image.tostring(map_surface, 'RGBA')
    img = Image.frombytes('RGBA', (width, height), map_data)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    maps_dir = os.path.join(script_dir, "maps")
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)

    # Determine the next available filename.
    existing_files = os.listdir(maps_dir)
    numbers = []
    for f in existing_files:
        if f.startswith("map") and f.endswith(".png"):
            num_part = f[3:-4]  # Extract number from filename
            if num_part == "":
                numbers.append(0)
            else:
                try:
                    numbers.append(int(num_part))
                except ValueError:
                    pass
    next_number = max(numbers) + 1 if numbers else 0
    file_name = "map.png" if next_number == 0 else f"map{next_number}.png"

    file_path = os.path.join(maps_dir, file_name)
    img.save(file_path)
    print(f"Map saved as {file_path}")


def draw_curve(surface, curve):
    """
    Draw the smoothed centerline (solid gray line) and the dashed yellow centerline.
    """
    if len(curve) > 1:
        pygame.draw.lines(surface, GRAY, False, curve, 2)
        draw_dashed_line(surface, YELLOW, curve, DASH_LENGTH, GAP_LENGTH)


def draw_preview_points(surface, pts):
    """
    Draw small gray circles at given points to preview the drawn path.
    """
    for p in pts:
        pygame.draw.circle(surface, GRAY, p, 5)


# ---------------------------- Main Function ---------------------------- #
def main():
    """
    Main loop for the advanced map editor.

    Left mouse button: Draw (drag to add points).
    S key: Save the current map.
    C key: Clear the current drawing.
    E key: Exit the editor.
    """
    global points, preview_curve, trees_left, trees_right, camera_offset
    running = True
    drawing = False  # True when the left mouse button is held down
    font = pygame.font.SysFont("Arial", 20)

    while running:
        # Clear the screen with white.
        screen.fill(WHITE)

        # ----------------- Smooth Camera Panning ----------------- #
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Pan left
        if mouse_x < CAMERA_EDGE_MARGIN:
            pan_speed = (CAMERA_EDGE_MARGIN - mouse_x) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[0] -= pan_speed
        # Pan right
        elif mouse_x > SCREEN_WIDTH - CAMERA_EDGE_MARGIN:
            pan_speed = (mouse_x - (SCREEN_WIDTH - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[0] += pan_speed
        # Pan up
        if mouse_y < CAMERA_EDGE_MARGIN:
            pan_speed = (CAMERA_EDGE_MARGIN - mouse_y) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[1] -= pan_speed
        # Pan down
        elif mouse_y > SCREEN_HEIGHT - CAMERA_EDGE_MARGIN:
            pan_speed = (mouse_y - (SCREEN_HEIGHT - CAMERA_EDGE_MARGIN)) / CAMERA_EDGE_MARGIN * CAMERA_PAN_SPEED
            camera_offset[1] += pan_speed

        # -------------------- Event Handling ---------------------- #
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button starts drawing
                    drawing = True
                    # Convert mouse position to world coordinates.
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
                    # Clear all drawing data.
                    points = []
                    preview_curve = []
                    trees_left = []
                    trees_right = []
                elif event.key == K_e:
                    running = False

        # ---------------------- Update Drawing --------------------- #
        if drawing:
            current_point = (pygame.mouse.get_pos()[0] + camera_offset[0],
                             pygame.mouse.get_pos()[1] + camera_offset[1])
            # Only add the point if it is far enough from the last point.
            if not points or math.hypot(current_point[0] - points[-1][0],
                                        current_point[1] - points[-1][1]) >= SNAP_DISTANCE:
                points.append(current_point)
            # If the current point is close enough to the starting point, close the curve.
            if len(points) >= 3 and math.hypot(current_point[0] - points[0][0],
                                               current_point[1] - points[0][1]) < CLOSE_THRESHOLD:
                points.append(points[0])
                drawing = False

        # ---------------- Update Curves and Tree Positions ---------------- #
        if len(points) >= 2:
            # For a better spline, if we have less than 4 points, duplicate the first and last points.
            pts = points if len(points) >= 4 else [points[0]] + points + [points[-1]]
            preview_curve = catmull_rom_spline(pts, nPoints=30)
            trees_left = generate_trees(preview_curve, ROAD_WIDTH / 2 + 10, spacing=TREE_SPACING)
            trees_right = generate_trees(preview_curve, -ROAD_WIDTH / 2 - 10, spacing=TREE_SPACING)

        # --------------------- Drawing on Screen --------------------- #
        # Draw raw points and preview circles.
        for p in points:
            pygame.draw.circle(screen, BLACK, world_to_screen(p), 5)
        draw_preview_points(screen, [world_to_screen(p) for p in points])

        if preview_curve:
            # Compute road edges based on the smoothed curve.
            left_edge = compute_offset_curve(preview_curve, ROAD_WIDTH / 2)
            right_edge = compute_offset_curve(preview_curve, -ROAD_WIDTH / 2)
            road_polygon = [world_to_screen(p) for p in (left_edge + right_edge[::-1])]
            pygame.draw.polygon(screen, BLACK, road_polygon)
            # Draw the dashed centerline.
            draw_dashed_line(screen, YELLOW, [world_to_screen(p) for p in preview_curve], DASH_LENGTH, GAP_LENGTH)
            # Draw trees.
            for tree in trees_left + trees_right:
                pygame.draw.circle(screen, GREEN, world_to_screen(tree), 5)
            # Draw the centerline curve.
            draw_curve(screen, [world_to_screen(p) for p in preview_curve])
            # Draw start and finish labels.
            font_large = pygame.font.SysFont("Arial", 30)
            start_text = font_large.render("Start", True, YELLOW)
            finish_text = font_large.render("Finish", True, YELLOW)
            start_pos = world_to_screen(preview_curve[0])
            finish_pos = world_to_screen(preview_curve[-1])
            screen.blit(start_text, (start_pos[0], start_pos[1] - 40))
            screen.blit(finish_text, (finish_pos[0], finish_pos[1] - 40))
            # Display instructions at the bottom of the screen.
            instr = font.render("Hold left mouse button and drag to draw. Press S to save, C to clear, E to exit.",
                                True, BLACK)
            screen.blit(instr, (20, SCREEN_HEIGHT - 40))
        else:
            # If no curve is drawn yet, display a simple instruction.
            instr = font.render("Hold left mouse button and drag to draw. Press E to exit.", True, BLACK)
            screen.blit(instr, (20, SCREEN_HEIGHT - 40))

        # Draw the car's starting position as a small circle.
        pygame.draw.circle(screen, BLACK, world_to_screen(CAR_START_POS), 5)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
