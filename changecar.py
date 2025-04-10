import os
import pygame
from car import Car

# size for each car image
car_scales = {
    "car1.png": (75, 75),
    "car2.png": (75, 75),
    "car3.png": (75, 75),
    "car4.png": (75, 75),
    "car5.png": (75, 75),
    "car6.png": (75, 75),
    "car7.png": (75, 75),
}

# get list of car images
def get_car_images(folder="cars"):
    return [f for f in os.listdir(folder) if f.endswith(".png")]

# switch to next car
def change_car(car_images, car_index, starting_position):
    car_index = (car_index + 1) % len(car_images)
    return load_car(car_images, car_index, starting_position, car_scales), car_index

# load selected car
def load_car(car_images, car_index, starting_position, car_scales):
    car_image_name = car_images[car_index]
    car_image_path = os.path.join("cars", car_image_name)

    new_car = Car(initial_pos=starting_position.copy())
    car_image = pygame.image.load(car_image_path).convert_alpha()
    scale_size = car_scales.get(car_image_name, (75, 75))
    new_car.surface = pygame.transform.scale(car_image, scale_size)
    new_car.rotate_surface = new_car.surface
    new_car.speed = 0
    new_car.angle = 0

    return new_car
