class Button:
    def __init__(self, image, pos, text, font, base_color, hover_color):
        # Store the button image and position
        self.image = image
        self.x = pos[0]
        self.y = pos[1]

        # Store font and colors
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_input = text

        # Create text surface with the base color
        self.text = self.font.render(self.text_input, True, self.base_color)

        # If no image is given, use the text itself as the button
        if self.image is None:
            self.image = self.text

        # Get rectangles for image and text to place them on screen
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.text_rect = self.text.get_rect(center=(self.x, self.y))

    # This function draws the button on the screen
    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    # This checks if the mouse clicked inside the button
    def checkForInput(self, mouse_pos):
        if mouse_pos[0] in range(self.rect.left, self.rect.right) and mouse_pos[1] in range(self.rect.top,
                                                                                            self.rect.bottom):
            return True
        return False

    # This changes the text color when hovering over the button
    def changeColor(self, mouse_pos):
        if mouse_pos[0] in range(self.rect.left, self.rect.right) and mouse_pos[1] in range(self.rect.top,
                                                                                            self.rect.bottom):
            # Change to hover color
            self.text = self.font.render(self.text_input, True, self.hover_color)
        else:
            # Change back to base color
            self.text = self.font.render(self.text_input, True, self.base_color)
