import pygame
import math
import os
from typing import List, Tuple

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800

RADAR_MAX_LENGTH = 300
OFFSET_COLLISION = 30

class Car:
    def __init__(self, initial_pos: List[float] = None):
        # starting position
        if initial_pos is None:
            initial_pos = [700, 650]
        self.pos = initial_pos

        # load and resize the car image
        self.surface = pygame.image.load(os.path.join("cars", "car4.png"))
        self.surface = pygame.transform.scale(self.surface, (75, 75))
        self.rotate_surface = self.surface

        self.angle = 0.0
        self.speed = 0.0

        # center of the car
        self.center = [
            int(self.pos[0] + self.surface.get_width() / 2),
            int(self.pos[1] + self.surface.get_height() / 2)
        ]

        self.radars = []
        self.is_alive = True
        self.distance = 0.0
        self.time_spent = 0
        self.rotated_cache = {}

    def draw(self, screen, font=None, offset=(0, 0), draw_radars=True):
        center_offset = (self.center[0] - offset[0], self.center[1] - offset[1])
        rotated_rect = self.rotate_surface.get_rect(center=center_offset)
        screen.blit(self.rotate_surface, rotated_rect.topleft)

        if draw_radars:
            for radar in self.radars:
                radar_pos, _ = radar
                radar_pos = (radar_pos[0] - offset[0], radar_pos[1] - offset[1])
                pygame.draw.line(screen, (255, 0, 0), center_offset, radar_pos, 1)
                pygame.draw.circle(screen, (255, 0, 0), radar_pos, 5)

    def check_collision(self, collision_mask):
        self.is_alive = True
        mask_width, mask_height = collision_mask.get_size()

        for point in self.four_points:
            x, y = int(point[0]), int(point[1])
            if x < 0 or x >= mask_width or y < 0 or y >= mask_height:
                self.is_alive = False
                break
            if collision_mask.get_at((x, y)) == 0:
                self.is_alive = False
                break

    def check_radar(self, degree, collision_mask):
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

        distance = int(math.sqrt((x - self.center[0]) ** 2 + (y - self.center[1]) ** 2))
        self.radars.append(((x, y), distance))

    def update(self, game_map, collision_mask):
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

        self.check_collision(collision_mask)

        self.radars.clear()
        for degree in range(-90, 91, 30):
            self.check_radar(degree, collision_mask)

    def get_data(self):
        sensors = [r[1] / RADAR_MAX_LENGTH for r in self.radars]
        return sensors + [1.0]

    def get_alive(self):
        return self.is_alive

    def get_reward(self):
        base_reward = self.distance / 50.0
        time_reward = self.time_spent / 100.0
        min_distance = min([r[1] for r in self.radars], default=0)
        safety_reward = min_distance / RADAR_MAX_LENGTH

        if not self.is_alive:
            return base_reward + time_reward + safety_reward - 50.0

        return base_reward + 0.5 * time_reward + 1.0 * safety_reward

    def rot_center(self, image, angle):
        rotated_image = pygame.transform.rotate(image, angle)
        return rotated_image
