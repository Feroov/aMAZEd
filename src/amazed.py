import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Get screen dimensions
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h

CELL_SIZE = 32  # Changed to match the texture size
PLAYER_SIZE = 30
FPS = 60
VISIBILITY_RADIUS = 200
FADE_RADIUS = 50
LIGHT_LEVEL = 150  # Base level of light intensity

# Colors for fire/torch effect
FIRE_COLORS = [
    (241, 124, 116),  # #f17c74
    (239, 102, 93),   # #ef665d
    (237, 81, 69),    # #ed5145
    (235, 64, 52),    # #eb4034
    (234, 59, 46),    # #ea3b2e
    (232, 37, 23)     # #e82517
]
BLUE = (255, 50, 0)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("aMAZEd")
clock = pygame.time.Clock()

# Load wall texture
wall_texture = pygame.image.load(os.path.join('assets', 'wall.png')).convert_alpha()
# Load floor texture
floor_texture = pygame.image.load(os.path.join('assets', 'floor.png')).convert_alpha()
# Load background image from assets folder
background_image = pygame.image.load(os.path.join('assets', 'mainmenu.png')).convert()

hover_sound = pygame.mixer.Sound(os.path.join('assets', 'hover.wav'))
select_sound = pygame.mixer.Sound(os.path.join('assets', 'select.wav'))  # Load select sound

# Create a fog surface
fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3

    def move(self, keys, maze):
        dx = (keys[controls['right']] - keys[controls['left']])
        dy = (keys[controls['down']] - keys[controls['up']])
        
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Check horizontal movement
        if not any(maze.is_wall(new_x + x, self.y) or maze.is_wall(new_x + x, self.y + PLAYER_SIZE - 1) for x in [0, PLAYER_SIZE - 1]):
            self.x = new_x

        # Check vertical movement
        if not any(maze.is_wall(self.x, new_y + y) or maze.is_wall(self.x + PLAYER_SIZE - 1, new_y + y) for y in [0, PLAYER_SIZE - 1]):
            self.y = new_y

    def draw(self, camera_x, camera_y):
        pygame.draw.rect(screen, (255, 50, 0), (self.x - camera_x, self.y - camera_y, PLAYER_SIZE, PLAYER_SIZE))

class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]
        self.generate()
        self.set_exit()

    def generate(self):
        # Create border
        for x in range(self.width):
            self.grid[0][x] = 1
            self.grid[self.height-1][x] = 1
        for y in range(self.height):
            self.grid[y][0] = 1
            self.grid[y][self.width-1] = 1

        # Generate maze inside border
        stack = [(1, 1)]
        self.grid[1][1] = 0

        while stack:
            x, y = stack[-1]
            neighbors = [(x+2, y), (x-2, y), (x, y+2), (x, y-2)]
            valid_neighbors = [(nx, ny) for nx, ny in neighbors if 0 < nx < self.width-1 and 0 < ny < self.height-1 and self.grid[ny][nx] == 1]

            if valid_neighbors:
                nx, ny = random.choice(valid_neighbors)
                self.grid[ny][nx] = 0
                self.grid[(y + ny) // 2][(x + nx) // 2] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

    def set_exit(self):
        self.exit = (self.width - 2, self.height - 2)
        self.grid[self.exit[1]][self.exit[0]] = 2

    def is_wall(self, x, y):
        cell_x = int(x // CELL_SIZE)
        cell_y = int(y // CELL_SIZE)
        return cell_x < 0 or cell_x >= self.width or cell_y < 0 or cell_y >= self.height or self.grid[cell_y][cell_x] == 1

    def draw(self, camera_x, camera_y):
        screen.fill((0, 0, 0))  # Fill the screen with black
        
        player_center_x = camera_x + WIDTH // 2
        player_center_y = camera_y + HEIGHT // 2

        for y in range(self.height):
            for x in range(self.width):
                screen_x = x * CELL_SIZE - camera_x
                screen_y = y * CELL_SIZE - camera_y
                if 0 <= screen_x < WIDTH and 0 <= screen_y < HEIGHT:
                    if self.grid[y][x] == 1:
                        lighting = calculate_lighting(player_center_x, player_center_y, screen_x + CELL_SIZE // 2, screen_y + CELL_SIZE // 2)
                        wall_color = (min(255, LIGHT_LEVEL + lighting), min(255, LIGHT_LEVEL + lighting), min(255, LIGHT_LEVEL + lighting))
                        wall_surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
                        wall_surface.fill(wall_color)
                        wall_surface.blit(wall_texture, (0, 0))
                        screen.blit(wall_surface, (screen_x, screen_y))
                    elif self.grid[y][x] == 2:
                        pygame.draw.rect(screen, BLUE, (screen_x, screen_y, CELL_SIZE, CELL_SIZE))
                    elif self.grid[y][x] == 0:
                        screen.blit(floor_texture, (screen_x, screen_y))

def calculate_lighting(player_x, player_y, cell_x, cell_y):
    distance = math.sqrt((player_x - cell_x) ** 2 + (player_y - cell_y) ** 2)
    if distance < VISIBILITY_RADIUS - FADE_RADIUS:
        return 255  # Fully lit inside the visibility radius
    elif distance < VISIBILITY_RADIUS:
        return int(255 * (VISIBILITY_RADIUS - distance) / FADE_RADIUS)
    else:
        return 0  # Fully dark outside the visibility radius

def create_fog_of_war():
    fog_surface.fill((0, 0, 0, 255))  # Completely black and opaque
    
    for x in range(WIDTH):
        for y in range(HEIGHT):
            distance = math.sqrt((x - WIDTH // 2) ** 2 + (y - HEIGHT // 2) ** 2)
            if distance < VISIBILITY_RADIUS - FADE_RADIUS:
                fog_surface.set_at((x, y), (0, 0, 0, 0))  # Completely transparent
            elif distance < VISIBILITY_RADIUS:
                alpha = int(255 * (distance - (VISIBILITY_RADIUS - FADE_RADIUS)) / FADE_RADIUS)
                fog_surface.set_at((x, y), (0, 0, 0, alpha))
    
    return fog_surface

class Particle:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)
        self.color = random.choice(FIRE_COLORS)
        self.vel = pygame.Vector2(direction)
        self.vel.scale_to_length(random.uniform(1, 2))
        self.lifetime = random.randint(10, 40)

    def update(self):
        self.x += self.vel.x
        self.y += self.vel.y
        self.lifetime -= 1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.max_particles = 100  # Limit the maximum number of particles

    def emit(self, x, y, width, height):
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # Right, Down, Left, Up
        for direction in directions:
            for i in range(width + height):
                if len(self.particles) < self.max_particles:  # Limit particle emission
                    if direction in [(1, 0), (-1, 0)]:
                        pos_x = x + direction[0] * i
                        pos_y = y + random.randint(0, height)
                    else:
                        pos_x = x + random.randint(0, width)
                        pos_y = y + direction[1] * i
                    particle = Particle(pos_x, pos_y, direction)
                    self.particles.append(particle)

    def update_and_draw(self, screen):
        for particle in self.particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                self.particles.remove(particle)

def draw_text(text, size, x, y):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, (0, 0, 0)) 
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    screen.blit(text_surface, text_rect)

# Define initial control mappings
controls = {
    'up': pygame.K_w,
    'down': pygame.K_s,
    'left': pygame.K_a,
    'right': pygame.K_d
}

def update_controls(new_controls):
    global controls
    controls = new_controls

def main_menu(particle_system):
    # Define button colors
    button_color = (39, 157, 123)    # #279d7b
    hover_color = (51, 206, 161)     # #33cea1

    # Button properties
    button_width = 200
    button_height = 50
    button_margin = 20  # Space between buttons

    # Calculate total width required for buttons
    total_width = 3 * button_width + 2 * button_margin
    start_x = (WIDTH - total_width) // 2  # Start drawing buttons from this x-coordinate
    start_y = HEIGHT // 2 + 350  # Adjusted to lower the buttons on the screen

    buttons = [
        pygame.Rect(start_x, start_y, button_width, button_height),
        pygame.Rect(start_x + button_width + button_margin, start_y, button_width, button_height),
        pygame.Rect(start_x + 2 * (button_width + button_margin), start_y, button_width, button_height)
    ]

    button_texts = ["Play", "Options", "Quit"]

    hovered_button = None  # Variable to track currently hovered button

    while True:
        screen.fill((255, 255, 255))
        screen.blit(background_image, (0, 0))  # Draw background image

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, button in enumerate(buttons):
            if button.collidepoint(mouse_x, mouse_y):
                if hovered_button != button:  # If mouse enters new button area
                    hovered_button = button
                    try:
                        hover_sound.play()
                    except pygame.error as e:
                        print(f"Error playing hover sound: {e}")
                pygame.draw.rect(screen, hover_color, button)
            else:
                pygame.draw.rect(screen, button_color, button)
                if hovered_button == button:  # If mouse leaves previous button area
                    hovered_button = None  # Reset hovered button
                    hover_sound.stop()

            draw_text(button_texts[i], 40, button.centerx, button.centery)

            # Handle particle emission on button hover
            if button.collidepoint(mouse_x, mouse_y):
                particle_system.emit(button.x, button.y, button.width, button.height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_x, mouse_y):
                        if i == 0:
                            try:
                                select_sound.play()  # Play select sound on button click
                            except pygame.error as e:
                                print(f"Error playing select sound: {e}")
                            return "play"
                        elif i == 1:
                            try:
                                select_sound.play()  # Play select sound on button click
                            except pygame.error as e:
                                print(f"Error playing select sound: {e}")
                            return "options"
                        elif i == 2:
                            pygame.quit()
                            return "quit"

        particle_system.update_and_draw(screen)  # Update and draw particles

        pygame.display.flip()
        clock.tick(FPS)


def options_menu():
    # Placeholder function for options menu handling
    return "controls"

def control_selection():
    global controls
    running = True

    while running:
        screen.fill((255, 255, 255))
        draw_text("Controls", 60, WIDTH // 2, HEIGHT // 4)
        draw_text(f"Move Up: {pygame.key.name(controls['up'])}", 36, WIDTH // 2, HEIGHT // 2 - 50)
        draw_text(f"Move Down: {pygame.key.name(controls['down'])}", 36, WIDTH // 2, HEIGHT // 2)
        draw_text(f"Move Left: {pygame.key.name(controls['left'])}", 36, WIDTH // 2, HEIGHT // 2 + 50)
        draw_text(f"Move Right: {pygame.key.name(controls['right'])}", 36, WIDTH // 2, HEIGHT // 2 + 100)
        draw_text("Press a key to change or ESC to go back", 24, WIDTH // 2, HEIGHT - 100)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    new_key = event.key
                    if new_key not in controls.values():
                        for control in controls:
                            if controls[control] == new_key:
                                controls[control] = None  # Clear old binding
                        for control in controls:
                            if controls[control] is None:
                                controls[control] = new_key
                                break
            elif event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

def main():
    particle_system = ParticleSystem()

    while True:
        choice = main_menu(particle_system)
        if choice == "play":
            maze_width = 25  # Increased to fill the screen with the new cell size
            maze_height = 25
            fog = create_fog_of_war()

            maze = Maze(maze_width, maze_height)
            player = Player(CELL_SIZE + CELL_SIZE // 2 - PLAYER_SIZE // 2, CELL_SIZE + CELL_SIZE // 2 - PLAYER_SIZE // 2)
            
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                keys = pygame.key.get_pressed()
                player.move(keys, maze)

                # Check if player reached the exit
                if (int(player.x // CELL_SIZE), int(player.y // CELL_SIZE)) == maze.exit:
                    running = False

                # Calculate camera position to keep player centered
                camera_x = player.x - WIDTH // 2 + PLAYER_SIZE // 2
                camera_y = player.y - HEIGHT // 2 + PLAYER_SIZE // 2

                screen.fill((255, 255, 255))
                maze.draw(int(camera_x), int(camera_y))
                player.draw(int(camera_x), int(camera_y))
                
                # Apply fog of war
                screen.blit(fog, (0, 0))
                
                pygame.display.flip()
                clock.tick(FPS)

        elif choice == "options":
            option_selected = options_menu()  # Handle options menu
            if option_selected == "controls":
                control_selection()  # Handle control selection

        elif choice == "quit":
            return

if __name__ == "__main__":
    main()
