import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Fixed screen dimensions
WIDTH, HEIGHT = 1000, 800

CELL_SIZE = 32  
PLAYER_SIZE = 30
FPS = 60
VISIBILITY_RADIUS = 200
FADE_RADIUS = 50
LIGHT_LEVEL = 150  # Base level of light intensity

BUTTON_PARTICLE_COLORS = [
    (241, 124, 116),  # #f17c74
    (239, 102, 93),   # #ef665d
    (237, 81, 69),    # #ed5145
    (235, 64, 52),    # #eb4034
    (234, 59, 46),    # #ea3b2e
    (232, 37, 23)     # #e82517
]


BLUE = (255, 50, 0)

game_music_tracks = [
    os.path.join('assets', 'gamemusic1.mp3'),
    os.path.join('assets', 'gamemusic2.mp3'),
    os.path.join('assets', 'gamemusic3.mp3')
]
current_game_track = None

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Amazed")
clock = pygame.time.Clock()


# Load wall texture
wall_texture = pygame.image.load(os.path.join('assets', 'wall.png')).convert_alpha()
# Load floor texture
floor_texture = pygame.image.load(os.path.join('assets', 'floor.png')).convert_alpha()
# Load background image from assets folder
background_image = pygame.image.load(os.path.join('assets', 'mainmenu.png')).convert()

VOLUME = 1.0  # 1.0 is full volume, 0.0 is muted
all_sounds = []

hover_sound = pygame.mixer.Sound(os.path.join('assets', 'hover.wav'))
hover2_sound = pygame.mixer.Sound(os.path.join('assets', 'hover2.wav'))
select_sound = pygame.mixer.Sound(os.path.join('assets', 'select.wav'))
select2_sound = pygame.mixer.Sound(os.path.join('assets', 'select2.wav'))
pygame.mixer.music.load(os.path.join('assets', 'music1.wav'))
back_sound = pygame.mixer.Sound(os.path.join('assets', 'back.wav'))
all_sounds.append(back_sound)
back_sound.set_volume(VOLUME)


# Add all sounds to the global list
all_sounds.extend([hover_sound, hover2_sound, select_sound, select2_sound])

# Set initial volume for all sounds
for sound in all_sounds:
    sound.set_volume(VOLUME)



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

class MenuParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)
        self.color = random.choice([(51, 206, 161), (45, 185, 144), (40, 164, 128), (35, 144, 112)])
        self.vel = pygame.Vector2(0, -random.uniform(1, 3))  # Vertical movement only
        self.lifetime = random.randint(40, 500)

    def update(self):
        self.x += self.vel.x
        self.y += self.vel.y
        self.lifetime -= 1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)


class Particle:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)
        self.color = random.choice(BUTTON_PARTICLE_COLORS
    )
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

def draw_text_options(text, size, x, y, text_color=(90, 216, 168), outline_color=(0, 0, 0)):
    font = pygame.font.Font(None, size + 4)  # Larger font size for the outline
    text_surface = font.render(text, True, outline_color)  # Render with outline color
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    screen.blit(text_surface, text_rect)

    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, text_color)  # Render with custom text color
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

def play_main_menu_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.mixer.music.load(os.path.join('assets', 'music1.wav'))
    pygame.mixer.music.play(loops=-1)

def stop_main_menu_music():
    pygame.mixer.music.stop()

def play_random_game_music():
    global current_game_track
    if current_game_track is not None:
        pygame.mixer.music.unload()
    current_game_track = random.choice(game_music_tracks)
    pygame.mixer.music.load(current_game_track)
    pygame.mixer.music.play()

def stop_game_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()


def main_menu(particle_system):
    play_main_menu_music()

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
    start_y = HEIGHT // 2 + 200  

    buttons = [
        pygame.Rect(start_x, start_y, button_width, button_height),
        pygame.Rect(start_x + button_width + button_margin, start_y, button_width, button_height),
        pygame.Rect(start_x + 2 * (button_width + button_margin), start_y, button_width, button_height)
    ]

    button_texts = ["Play", "Options", "Quit"]

    hovered_button = None  # Variable to track currently hovered button
    selected_button = 0
    menu_particles = []
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

        for particle in menu_particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                menu_particles.remove(particle)

        # Emit new menu particles periodically
        if random.random() < 0.4:  # Adjust emission rate as needed
            x = random.randint(0, WIDTH)
            y = HEIGHT
            particle = MenuParticle(x, y)
            menu_particles.append(particle)

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
                            options_menu()  # Navigate to options menu
                        elif i == 2:
                            pygame.quit()
                            return "quit"

        particle_system.update_and_draw(screen)  # Update and draw particles

        pygame.display.flip()
        clock.tick(FPS)


def options_menu():
    global controls, VOLUME, all_sounds
    running = True
    selected_option = 0
    awaiting_keypress = False
    options = ['up', 'down', 'left', 'right', 'volume']

    background_image = pygame.image.load(os.path.join('assets', 'optionmenu.png')).convert()
    hover_sound_options = pygame.mixer.Sound(os.path.join('assets', 'hover2.wav'))
    select_sound = pygame.mixer.Sound(os.path.join('assets', 'select.wav'))
    select2_sound = pygame.mixer.Sound(os.path.join('assets', 'select2.wav'))

    all_sounds.extend([hover_sound_options, select_sound, select2_sound])
    for sound in [hover_sound_options, select_sound, select2_sound]:
        sound.set_volume(VOLUME)

    text_color = (255, 255, 255)
    highlight_color = (90, 216, 168)
    update_volume()

    while running:
        screen.blit(background_image, (0, 0))

        for i, option in enumerate(options):
            if option == 'volume':
                text = f"Volume: {int(VOLUME * 100)}%"
            else:
                text = f"Move {option.capitalize()}: {pygame.key.name(controls[option])}"

            y_position = HEIGHT // 2 - 100 + i * 50  # Adjust this value to move options higher or lower
            if selected_option == i:
                if awaiting_keypress and option != 'volume':
                    text = f"Move {option.capitalize()}: Press a key..."
                draw_text_options(text, 36, WIDTH // 2, y_position, text_color=highlight_color, outline_color=(0, 0, 0))
            else:
                draw_text_options(text, 36, WIDTH // 2, y_position, text_color=text_color, outline_color=(0, 0, 0))

        draw_text_options("Press ESC to go back", 24, WIDTH // 2, HEIGHT - 100, text_color=text_color, outline_color=(0, 0, 0))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    back_sound.play()  # Play back sound
                    running = False
                elif awaiting_keypress and selected_option != 4:
                    controls[options[selected_option]] = event.key
                    select2_sound.play()
                    awaiting_keypress = False
                else:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                        hover_sound_options.play()
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                        hover_sound_options.play()
                    elif event.key == pygame.K_RETURN:
                        if selected_option != 4:  # Not volume
                            awaiting_keypress = True
                            select_sound.play()
                    elif event.key == pygame.K_LEFT and selected_option == 4:
                        VOLUME = max(0, VOLUME - 0.1)
                        update_volume()
                        select_sound.play()
                    elif event.key == pygame.K_RIGHT and selected_option == 4:
                        VOLUME = min(1, VOLUME + 0.1)
                        update_volume()
                        select_sound.play()

            elif event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

    update_volume()
    return "resume"




def update_volume():
    global all_sounds
    pygame.mixer.music.set_volume(VOLUME)
    for sound in all_sounds:
        sound.set_volume(VOLUME)

def pause_menu():
    global controls, VOLUME, all_sounds

    running = True
    selected_option = 0  # Track the currently selected option (0 for resume)

    # Load sounds
    hover_sound_pause = pygame.mixer.Sound(os.path.join('assets', 'hover2.wav'))
    select_sound_pause = pygame.mixer.Sound(os.path.join('assets', 'select.wav'))

    all_sounds.extend([hover_sound_pause, select_sound_pause])
    for sound in [hover_sound_pause, select_sound_pause]:
        sound.set_volume(VOLUME)

    previous_selected_option = None  # To track the previously selected option

    while running:
        screen.fill((0, 0, 0, 180))  # Semi-transparent black overlay

        draw_text_options("Paused", 60, WIDTH // 2, HEIGHT // 4, text_color=(90, 216, 168), outline_color=(0, 0, 0))

        options = ["Resume", "Options", "Main Menu"]
        for i, option in enumerate(options):
            if selected_option == i:
                draw_text_options(option, 36, WIDTH // 2, HEIGHT // 2 + i * 50, text_color=(90, 216, 168), outline_color=(0, 0, 0))
            else:
                draw_text_options(option, 36, WIDTH // 2, HEIGHT // 2 + i * 50, text_color=(200, 200, 200), outline_color=(0, 0, 0))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    back_sound.play()  # Play back sound
                    select_sound_pause.play()
                    return "resume"
                elif event.key == pygame.K_RETURN:
                    select_sound_pause.play()
                    if selected_option == 0:
                        return "resume"
                    elif selected_option == 1:
                        options_menu()
                    elif selected_option == 2:
                        stop_game_music()
                        return "main_menu"
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for i, option in enumerate(options):
                    if HEIGHT // 2 + i * 50 - 18 < mouse_y < HEIGHT // 2 + i * 50 + 18:
                        selected_option = i
                        select_sound_pause.play()

            elif event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

        # Play hover sound when the selection changes
        if previous_selected_option is not None and previous_selected_option != selected_option:
            hover_sound_pause.play()

        previous_selected_option = selected_option

    return "resume"



def main():
    particle_system = ParticleSystem()
    update_volume() 

    while True:
        play_main_menu_music()
        choice = main_menu(particle_system)
        if choice == "play":
            stop_main_menu_music()
            play_random_game_music()
            maze_width = 25 
            maze_height = 25
            fog = create_fog_of_war()

            maze = Maze(maze_width, maze_height)
            player = Player(CELL_SIZE + CELL_SIZE // 2 - PLAYER_SIZE // 2, CELL_SIZE + CELL_SIZE // 2 - PLAYER_SIZE // 2)
            
            paused = False
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if paused:
                                paused = False
                                play_random_game_music()
                            else:
                                paused = True
                                stop_game_music()
                                pause_choice = pause_menu()
                                if pause_choice == "resume":
                                    paused = False
                                    play_random_game_music()
                                elif pause_choice == "main_menu":
                                    running = False  # Exit the current game loop to return to main menu
                                    break  # Exit the event loop
                
                if not paused and not pygame.mixer.music.get_busy():
                    play_random_game_music()
                if not paused:
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
            stop_game_music()        
            play_main_menu_music()
        elif choice == "quit":
            pygame.quit()
            return


if __name__ == "__main__":
    main()
