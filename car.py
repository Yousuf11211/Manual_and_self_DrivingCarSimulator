import pygame
import math
import os
from typing import List, Tuple

# Screen dimensions (used for camera/view size)
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

# Constants for collision and radar
RADAR_MAX_LENGTH = 300
OFFSET_COLLISION = 40

class Car:
    def __init__(self, initial_pos: List[float] = None) -> None:
        # Default starting position if none provided.
        if initial_pos is None:
            initial_pos = [700, 650]
        self.pos: List[float] = initial_pos
        self.surface = pygame.image.load(os.path.join("cars", "car.png"))
        self.surface = pygame.transform.scale(self.surface, (100, 100))
        self.rotate_surface = self.surface
        self.angle: float = 0.0
        self.speed: float = 0.0  # Controlled externally.
        # Compute center dynamically from image dimensions
        self.center: List[int] = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]
        self.radars: List[Tuple[Tuple[int, int], int]] = []
        self.is_alive: bool = True
        self.distance: float = 0.0
        self.time_spent: int = 0
        # Cache for rotated images.
        self.rotated_cache = {}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font = None, offset: Tuple[int, int]=(0,0)) -> None:
        """Draw the car (rotated), its sensor rays, and optionally the speed text."""
        draw_pos = (self.pos[0] - offset[0], self.pos[1] - offset[1])
        screen.blit(self.rotate_surface, draw_pos)
        # Draw sensor (radar) lines (apply the same offset).
        offset_center = (self.center[0] - offset[0], self.center[1] - offset[1])
        for radar in self.radars:
            radar_pos, _ = radar
            offset_radar = (radar_pos[0] - offset[0], radar_pos[1] - offset[1])
            pygame.draw.line(screen, (0, 255, 0), offset_center, offset_radar, 1)
            pygame.draw.circle(screen, (0, 255, 0), offset_radar, 5)
        if font is not None:
            speed_text = font.render("Speed: " + str(round(self.speed, 2)), True, (0, 0, 0))
            text_rect = speed_text.get_rect(center=(draw_pos[0] + self.surface.get_width() / 2, draw_pos[1] - 10))
            screen.blit(speed_text, text_rect)

    def check_collision(self, collision_mask: pygame.mask.Mask) -> None:
        """
        Check if any of the car's four collision points fall outside the drivable road.
        A zero value in the collision mask indicates off-road.
        """
        self.is_alive = True
        mask_width, mask_height = collision_mask.get_size()
        for p in self.four_points:
            x, y = int(p[0]), int(p[1])
            if x < 0 or x >= mask_width or y < 0 or y >= mask_height:
                self.is_alive = False
                break
            if collision_mask.get_at((x, y)) == 0:
                self.is_alive = False
                break

    def check_radar(self, degree: float, collision_mask: pygame.mask.Mask) -> None:
        """
        Cast a sensor ray at a given angle (relative to the car's current angle)
        until it hits an obstacle (mask value 0) or reaches the maximum length.
        """
        ray_length = 0
        mask_width, mask_height = collision_mask.get_size()
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * ray_length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * ray_length)
        while ray_length < RADAR_MAX_LENGTH:
            if x < 0 or x >= mask_width or y < 0 or y >= mask_height:
                break
            if collision_mask.get_at((x, y)) == 0:
                break
            ray_length += 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * ray_length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * ray_length)
        dist = int(math.sqrt((x - self.center[0]) ** 2 + (y - self.center[1]) ** 2))
        self.radars.append(((x, y), dist))

    def update(self, game_map: pygame.Surface, collision_mask: pygame.mask.Mask) -> None:
        """
        Update the car's position based on its speed and angle, recalculate its center,
        update its collision points, and update its sensor rays.
        """
        # Rotate the image using cache.
        angle_key = int(round(self.angle)) % 360
        if angle_key in self.rotated_cache:
            self.rotate_surface = self.rotated_cache[angle_key]
        else:
            self.rotate_surface = self.rot_center(self.surface, self.angle)
            self.rotated_cache[angle_key] = self.rotate_surface

        # Update position.
        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed

        self.distance += self.speed
        self.time_spent += 1
        # Update center dynamically.
        self.center = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]

        # Calculate collision points (four corners) based on a fixed offset.
        offset = OFFSET_COLLISION
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * offset,
                    self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * offset]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * offset,
                     self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * offset]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * offset,
                       self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * offset]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * offset,
                        self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * offset]
        self.four_points = [left_top, right_top, left_bottom, right_bottom]

        # Check for collisions and update sensor rays.
        self.check_collision(collision_mask)
        self.radars.clear()
        for d in range(-90, 91, 30):
            self.check_radar(d, collision_mask)

    def get_data(self) -> List[float]:
        """
        Return normalized sensor distances (7 values between 0 and 1) plus the
        normalized speed as an extra input for the neural network.
        """
        sensors = [r[1] / RADAR_MAX_LENGTH for r in self.radars]
        normalized_speed = self.speed / 15.0  # Assuming max speed is roughly 15.
        return sensors + [normalized_speed]

    def get_alive(self) -> bool:
        """Return whether the car is still alive."""
        return self.is_alive

    def get_reward(self) -> float:
        """
        Compute a reward based on distance traveled, survival time, and safety (from sensor data).
        If the car has crashed, a penalty is applied.
        """
        base_weight = 1.0
        time_weight = 0.5
        safety_weight = 1.0

        base_reward = self.distance / 50.0
        time_reward = self.time_spent / 100.0
        min_distance = min([r[1] for r in self.radars], default=0)
        safety_reward = min_distance / RADAR_MAX_LENGTH

        # If the car is dead, apply a penalty.
        if not self.is_alive:
            return base_reward + time_reward + safety_reward - 50.0

        return base_weight * base_reward + time_weight * time_reward + safety_weight * safety_reward

    def rot_center(self, image: pygame.Surface, angle: float) -> pygame.Surface:
        """Rotate an image while preserving its center."""
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        return rot_image.subsurface(rot_rect).copy()
