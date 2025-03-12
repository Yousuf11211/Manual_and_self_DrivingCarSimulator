import pygame
import sys
import os
from car import Car, SCREEN_WIDTH, SCREEN_HEIGHT
from simulation import (
    drag_and_drop_starting_position,
    draw_map_button,
    dropdown_map_selection,
    select_map
)
from button import Button


def draw_switch_button(screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """
    Draws a button in the top-left corner to switch from manual to automatic mode.
    Returns the button's rectangle area for mouse click detection.
    """
    # Load and scale the image to 150x40 pixels.
    original_image = pygame.image.load("assets/simulate.png")
    scaled_image = pygame.transform.scale(original_image, (150, 40))

    # Since we want the button's top-left corner at (10, 10) and the Button class uses the center,
    # calculate the center position: (10 + 150/2, 10 + 40/2) = (85, 30)
    pos = (10 + 150 // 2, 10 + 40 // 2)

    # Create the button with the label "Auto Mode".
    auto_button = Button(
        image=scaled_image,
        pos=pos,
        text_input="Auto Mode",
        font=font,
        base_color="#d7fcd4",  # Consistent base color
        hovering_color="White"  # Consistent hovering color
    )

    # Draw the button on the screen.
    auto_button.update(screen)

    # Return the button's rectangle for mouse click detection.
    return auto_button.rect


def main():
    """Main function to run the manual car control simulation."""
    # Initialize pygame and create a window.
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Manual Car Control")
    clock = pygame.time.Clock()  # Clock to control the frame rate.
    info_font = pygame.font.SysFont("Arial", 30)  # Font used for on-screen text.

    # Select the map using a helper function and load the map image.
    global_map_path = select_map(screen, info_font)
    try:
        # Load the display map for rendering.
        display_map = pygame.image.load(global_map_path).convert_alpha()
    except Exception as e:
        print("Error loading map image:", e)
        sys.exit(1)

    # Load the collision map, set its colorkey and create a collision mask.
    collision_map = pygame.image.load(global_map_path).convert_alpha()
    Lightgreen = (144, 238, 144)
    collision_map.set_colorkey(Lightgreen)
    collision_mask = pygame.mask.from_surface(collision_map)

    # Allow the user to choose a starting position by dragging and dropping on the map.
    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)

    # Create a car object with the chosen starting position.
    car = Car(initial_pos=starting_position.copy())
    car.speed = 0
    car.angle = 0

    # Define control parameters for the car's movement.
    acceleration = 0.2  # How fast the car speeds up when moving forward.
    brake_deceleration = 0.1  # How quickly the car slows down when braking.
    friction = 0.01  # Natural deceleration when no key is pressed.
    max_speed = 15  # Maximum forward speed.
    max_reverse_speed = -10  # Maximum reverse speed.
    angular_velocity = 0.0  # The current turning speed.
    turning_acceleration = 0.2  # How quickly the car starts turning.
    turning_deceleration = 0.1  # How quickly the turning slows down.
    max_turning_rate = 5  # The maximum rate at which the car can turn.

    running = True
    while running:
        # Fill the background with a light green color.
        screen.fill((144, 238, 144))

        # Process events such as quitting the game.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get the current state of all keyboard keys.
        keys = pygame.key.get_pressed()

        # Handle forward (W key) and backward (S key) movement.
        if keys[pygame.K_w]:
            car.speed += acceleration
            if car.speed > max_speed:
                car.speed = max_speed
        elif keys[pygame.K_s]:
            if car.speed > 0:
                car.speed -= brake_deceleration
            else:
                car.speed -= acceleration
            if car.speed < max_reverse_speed:
                car.speed = max_reverse_speed
        else:
            # Apply friction to gradually reduce the car's speed.
            if car.speed > 0:
                car.speed = max(car.speed - friction, 0)
            elif car.speed < 0:
                car.speed = min(car.speed + friction, 0)

        # Handle turning with A (left) and D (right) keys.
        if keys[pygame.K_a]:
            angular_velocity += turning_acceleration
        elif keys[pygame.K_d]:
            angular_velocity -= turning_acceleration
        else:
            # Gradually reduce the turning speed when no key is pressed.
            if angular_velocity > 0:
                angular_velocity = max(angular_velocity - turning_deceleration, 0)
            elif angular_velocity < 0:
                angular_velocity = min(angular_velocity + turning_deceleration, 0)

        # Limit the angular velocity to the maximum turning rate.
        if angular_velocity > max_turning_rate:
            angular_velocity = max_turning_rate
        elif angular_velocity < -max_turning_rate:
            angular_velocity = -max_turning_rate

        # Update the car's direction and position.
        car.angle += angular_velocity
        car.update(display_map, collision_mask)
        # print(f"Car Position: {car.pos}, Speed: {car.speed}")

        # Check for collisions. If the car has collided, show a message and reset.
        if not car.get_alive():
            msg = info_font.render("Collision! Restarting...", True, (255, 0, 0))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(1000)
            car = Car(initial_pos=starting_position.copy())
            car.speed = 0
            car.angle = 0
            angular_velocity = 0.0

        # Camera logic: center the view on the car.
        offset_x = car.center[0] - SCREEN_WIDTH // 2
        offset_y = car.center[1] - SCREEN_HEIGHT // 2
        camera_rect = pygame.Rect(offset_x, offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        # Draw the visible portion of the map.
        screen.blit(display_map, (0, 0), camera_rect)

        # Draw the car on the screen, adjusting for camera offset.
        car.draw(screen, info_font, offset=(offset_x, offset_y), draw_radars=False)

        # Draw the map selection button and the mode switch button.
        map_button_rect = draw_map_button(screen, info_font)
        switch_button_rect = draw_switch_button(screen, info_font)

        # Handle mouse clicks on the buttons.
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            # Check if the map button was clicked.
            if map_button_rect.collidepoint(mouse_pos):
                new_map = dropdown_map_selection(screen, info_font)
                if new_map:
                    global_map_path = new_map
                    try:
                        display_map = pygame.image.load(global_map_path).convert_alpha()
                    except Exception as e:
                        print("Error loading map image:", e)
                        sys.exit(1)
                    # Reload the collision map for the new map.
                    collision_map = pygame.image.load(global_map_path).convert_alpha()
                    collision_map.set_colorkey(Lightgreen)
                    collision_mask = pygame.mask.from_surface(collision_map)
                    # Allow the user to set a new starting position on the new map.
                    starting_position = drag_and_drop_starting_position(screen, info_font, collision_mask, display_map)
                    car.pos = starting_position.copy()
                    car.center = [
                        int(car.pos[0] + car.surface.get_width() / 2),
                        int(car.pos[1] + car.surface.get_height() / 2)
                    ]
            # Check if the switch button was clicked (to switch to automatic mode).
            if switch_button_rect.collidepoint(mouse_pos):
                pygame.quit()
                os.system('python main.py')
                sys.exit()

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Limit the frame rate to 60 frames per second


if __name__ == "__main__":
    main()
