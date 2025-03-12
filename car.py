import pygame
import math
import os
from typing import List, Tuple

# Screen dimensions (used for camera/view size)
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

# Constants for radar length and collision detection offset
RADAR_MAX_LENGTH = 300
OFFSET_COLLISION = 30  # Offset distance to check for collisions


class Car:
    def __init__(self, initial_pos: List[float] = None) -> None:
        # Set the initial position; if none provided, use a default value.
        if initial_pos is None:
            initial_pos = [700, 650]
        self.pos: List[float] = initial_pos

        # Load the car image from the 'cars' folder and scale it to a fixed size.
        self.surface = pygame.image.load(os.path.join("cars", "car.png"))
        self.surface = pygame.transform.scale(self.surface, (70, 70))

        # This surface will be updated with the rotated version of the car.
        self.rotate_surface = self.surface

        # Initial angle (in degrees) and speed (controlled externally)
        self.angle: float = 0.0
        self.speed: float = 0.0

        # Calculate the center of the car based on its position and image size.
        self.center: List[int] = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]

        # List to hold radar sensor data as tuples (endpoint, distance)
        self.radars: List[Tuple[Tuple[int, int], int]] = []

        # Flag to indicate if the car is still active (has not collided)
        self.is_alive: bool = True

        # Variables to track how far the car has traveled and how much time has passed.
        self.distance: float = 0.0
        self.time_spent: int = 0

        # Cache to store rotated images to avoid recalculating for the same angle
        self.rotated_cache = {}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font = None, offset: Tuple[int, int] = (0, 0),
             draw_radars: bool = True) -> None:
        # Calculate the position to draw the car.
        draw_pos = (self.pos[0] - offset[0], self.pos[1] - offset[1])
        screen.blit(self.rotate_surface, draw_pos)

        # Adjust the center position for drawing.
        offset_center = (self.center[0] - offset[0], self.center[1] - offset[1])

        # Draw sensor (radar) lines only if draw_radars is True.
        if draw_radars:
            for radar in self.radars:
                radar_pos, _ = radar
                offset_radar = (radar_pos[0] - offset[0], radar_pos[1] - offset[1])
                pygame.draw.line(screen, (0, 255, 0), offset_center, offset_radar, 1)
                pygame.draw.circle(screen, (0, 255, 0), offset_radar, 5)

        # # Draw speed display if a font is provided.
        # if font is not None:
        #     speed_text = font.render("Speed: " + str(round(self.speed, 2)), True, (0, 0, 0))
        #     text_rect = speed_text.get_rect(center=(draw_pos[0] + self.surface.get_width() / 2, draw_pos[1] - 10))
        #     screen.blit(speed_text, text_rect)

    def check_collision(self, collision_mask: pygame.mask.Mask) -> None:
        """
        Check whether any of the car's four corner points collide with a non-road area
        using the provided collision mask.
        """
        self.is_alive = True  # Assume the car is alive until a collision is found
        mask_width, mask_height = collision_mask.get_size()

        # Loop through each of the four corner points of the car
        for point in self.four_points:
            x, y = int(point[0]), int(point[1])
            # Check if the point is out of bounds
            if x < 0 or x >= mask_width or y < 0 or y >= mask_height:
                self.is_alive = False
                break
            # Check if the pixel at this point is not part of the road (mask pixel is 0)
            if collision_mask.get_at((x, y)) == 0:
                self.is_alive = False
                break

    def check_radar(self, degree: float, collision_mask: pygame.mask.Mask) -> None:
        """
        Emit a radar ray from the car's center at a specific degree offset.
        The function calculates the distance until the ray hits a collision.
        """
        ray_length = 0
        mask_width, mask_height = collision_mask.get_size()

        # Calculate the initial end coordinates of the radar ray
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * ray_length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * ray_length)

        # Increase the length of the radar ray until it reaches the maximum length or a collision is detected
        while ray_length < RADAR_MAX_LENGTH:
            if x < 0 or x >= mask_width or y < 0 or y >= mask_height:
                break  # Stop if out of bounds
            if collision_mask.get_at((x, y)) == 0:
                break  # Stop if the ray hits an obstacle
            ray_length += 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * ray_length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * ray_length)

        # Calculate the distance from the center of the car to the end of the radar ray
        distance = int(math.sqrt((x - self.center[0]) ** 2 + (y - self.center[1]) ** 2))
        self.radars.append(((x, y), distance))

    def update(self, game_map: pygame.Surface, collision_mask: pygame.mask.Mask) -> None:
        """
        Update the car's position, rotation, collision points, and radar readings.
        """
        # Use a cache for rotated images to save processing time.
        angle_key = int(round(self.angle)) % 360
        if angle_key in self.rotated_cache:
            self.rotate_surface = self.rotated_cache[angle_key]
        else:
            self.rotate_surface = self.rot_center(self.surface, self.angle)
            self.rotated_cache[angle_key] = self.rotate_surface

        # Update the car's position based on its speed and current angle.
        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed

        # Update the total distance traveled and time spent moving.
        self.distance += self.speed
        self.time_spent += 1

        # Recalculate the center point of the car.
        self.center = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]

        # Calculate the four corner points of the car for collision detection.
        offset = OFFSET_COLLISION
        left_top = [
            self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * offset,
            self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * offset
        ]
        right_top = [
            self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * offset,
            self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * offset
        ]
        left_bottom = [
            self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * offset,
            self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * offset
        ]
        right_bottom = [
            self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * offset,
            self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * offset
        ]
        self.four_points = [left_top, right_top, left_bottom, right_bottom]

        # Check for collisions using the updated corner points.
        self.check_collision(collision_mask)

        # Clear previous radar data and update all radar readings.
        self.radars.clear()
        # Emit radar rays every 30 degrees from -90 to 90 degrees relative to the car's front.
        for degree in range(-90, 91, 30):
            self.check_radar(degree, collision_mask)

    def get_data(self) -> List[float]:
        """
        Return the normalized radar sensor data plus a constant speed value.
        Normalized values are in the range [0, 1].
        """
        sensors = [r[1] / RADAR_MAX_LENGTH for r in self.radars]
        # Always return a normalized speed of 1.0 so the neural network sees a constant speed.
        return sensors + [1.0]

    def get_alive(self) -> bool:
        """Return whether the car is still active (not collided)."""
        return self.is_alive

    def get_reward(self) -> float:
        """
        Calculate and return the reward for the car based on:
        - Distance traveled (base reward)
        - Time spent moving (time reward)
        - Safety (how far the nearest radar reading is)
        If the car is not alive, apply a penalty.
        """
        # Weights for different components of the reward
        base_weight = 1.0
        time_weight = 0.5
        safety_weight = 1.0

        base_reward = self.distance / 50.0
        time_reward = self.time_spent / 100.0

        # Safety reward based on the closest radar distance; use 0 if no radar data is available.
        min_distance = min([r[1] for r in self.radars], default=0)
        safety_reward = min_distance / RADAR_MAX_LENGTH

        if not self.is_alive:
            # Apply a penalty if the car is no longer active.
            return base_reward + time_reward + safety_reward - 50.0

        # Calculate the overall reward using weighted sums.
        return base_weight * base_reward + time_weight * time_reward + safety_weight * safety_reward

    def rot_center(self, image: pygame.Surface, angle: float) -> pygame.Surface:
        """
        Rotate an image while keeping its center.
        This function rotates the image and then creates a new surface that
        is correctly aligned with the original center.
        """
        # Get the original rectangle of the image.
        orig_rect = image.get_rect()
        # Rotate the image by the given angle.
        rotated_image = pygame.transform.rotate(image, angle)
        # Copy the original rectangle and set its center to the center of the rotated image.
        rot_rect = orig_rect.copy()
        rot_rect.center = rotated_image.get_rect().center
        # Create a subsurface of the rotated image that corresponds to the original rectangle and return it.
        return rotated_image.subsurface(rot_rect).copy()
