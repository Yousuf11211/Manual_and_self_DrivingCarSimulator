import pygame
import math
import os
from typing import List, Tuple

# Screen dimensions (used for camera/view size)
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

# Constants for collision and radar
RADAR_MAX_LENGTH = 300
OFFSET_COLLISION = 30  # Reduced offset to help avoid false collisions

class Car:
    def __init__(self, initial_pos: List[float] = None) -> None:
        if initial_pos is None:
            initial_pos = [700, 650]
        self.pos: List[float] = initial_pos
        self.surface = pygame.image.load(os.path.join("cars", "car.png"))
        self.surface = pygame.transform.scale(self.surface, (70, 70))
        self.rotate_surface = self.surface
        self.angle: float = 0.0
        self.speed: float = 0.0  # Speed will be controlled externally (constant)
        self.center: List[int] = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]
        self.radars: List[Tuple[Tuple[int, int], int]] = []
        self.is_alive: bool = True
        self.distance: float = 0.0
        self.time_spent: int = 0
        self.rotated_cache = {}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font = None, offset: Tuple[int, int]=(0, 0)) -> None:
        draw_pos = (self.pos[0] - offset[0], self.pos[1] - offset[1])
        screen.blit(self.rotate_surface, draw_pos)
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
        angle_key = int(round(self.angle)) % 360
        if angle_key in self.rotated_cache:
            self.rotate_surface = self.rotated_cache[angle_key]
        else:
            self.rotate_surface = self.rot_center(self.surface, self.angle)
            self.rotated_cache[angle_key] = self.rotate_surface

        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed

        self.distance += self.speed
        self.time_spent += 1

        self.center = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]

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

        self.check_collision(collision_mask)
        self.radars.clear()
        for d in range(-90, 91, 30):
            self.check_radar(d, collision_mask)

    def get_data(self) -> List[float]:
        sensors = [r[1] / RADAR_MAX_LENGTH for r in self.radars]
        # Return constant normalized speed (1.0) so that the NN always sees the same speed input.
        return sensors + [1.0]

    def get_alive(self) -> bool:
        return self.is_alive

    def get_reward(self) -> float:
        base_weight = 1.0
        time_weight = 0.5
        safety_weight = 1.0

        base_reward = self.distance / 50.0
        time_reward = self.time_spent / 100.0
        min_distance = min([r[1] for r in self.radars], default=0)
        safety_reward = min_distance / RADAR_MAX_LENGTH

        if not self.is_alive:
            return base_reward + time_reward + safety_reward - 50.0

        return base_weight * base_reward + time_weight * time_reward + safety_weight * safety_reward

    def rot_center(self, image: pygame.Surface, angle: float) -> pygame.Surface:
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        return rot_image.subsurface(rot_rect).copy()
