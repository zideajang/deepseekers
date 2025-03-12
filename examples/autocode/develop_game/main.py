import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plane Shooter Game")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Player settings
player_width = 50
player_height = 50
player_speed = 5
player_x = SCREEN_WIDTH // 2 - player_width // 2
player_y = SCREEN_HEIGHT - player_height - 10

# Enemy settings
enemy_width = 50
enemy_height = 50
enemy_speed = 3
enemies = []

# Bullet settings
bullet_width = 10
bullet_height = 20
bullet_speed = 7
bullets = []

# Score
score = 0

# Game state
game_is_running = True

# Function to draw the player
def draw_player(x, y):
    pygame.draw.rect(screen, WHITE, [x, y, player_width, player_height])

# Function to draw an enemy
def draw_enemy(x, y):
    pygame.draw.rect(screen, RED, [x, y, enemy_width, enemy_height])

# Function to draw a bullet
def draw_bullet(x, y):
    pygame.draw.rect(screen, WHITE, [x, y, bullet_width, bullet_height])

# Function to handle player input
def handle_input():
    global player_x, player_y
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and player_y > 0:
        player_y -= player_speed
    if keys[pygame.K_DOWN] and player_y < SCREEN_HEIGHT - player_height:
        player_y += player_speed
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - player_width:
        player_x += player_speed
    if keys[pygame.K_SPACE]:
        shoot()

# Function to spawn an enemy
def spawn_enemy():
    x = random.randint(0, SCREEN_WIDTH - enemy_width)
    y = 0
    enemies.append((x, y))

# Function to update enemy positions
def update_enemies():
    global game_is_running
    for i, enemy in enumerate(enemies):
        enemy_x, enemy_y = enemy
        enemy_y += enemy_speed
        enemies[i] = (enemy_x, enemy_y)
        if enemy_y > SCREEN_HEIGHT:
            enemies.pop(i)
            break
        # Check collision with player
        if (player_x < enemy_x + enemy_width and
            player_x + player_width > enemy_x and
            player_y < enemy_y + enemy_height and
            player_y + player_height > enemy_y):
            game_over()

# Function to shoot a bullet
def shoot():
    bullet_x = player_x + player_width // 2 - bullet_width // 2
    bullet_y = player_y
    bullets.append((bullet_x, bullet_y))

# Function to update bullet positions
def update_bullets():
    global score
    for i, bullet in enumerate(bullets):
        bullet_x, bullet_y = bullet
        bullet_y -= bullet_speed
        bullets[i] = (bullet_x, bullet_y)
        if bullet_y < 0:
            bullets.pop(i)
            break
        # Check collision with enemies
        for j, enemy in enumerate(enemies):
            enemy_x, enemy_y = enemy
            if (bullet_x < enemy_x + enemy_width and
                bullet_x + bullet_width > enemy_x and
                bullet_y < enemy_y + enemy_height and
                bullet_y + bullet_height > enemy_y):
                bullets.pop(i)
                enemies.pop(j)
                score += 1
                break

# Function to check for game over
def game_over():
    global game_is_running
    print("Game Over! Your score is: " + str(score))
    game_is_running = False

# Main game loop
while game_is_running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_is_running = False

    # Handle input
    handle_input()

    # Spawn enemies
    if random.random() < 0.02:
        spawn_enemy()

    # Update game state
    update_enemies()
    update_bullets()

    # Render game
    screen.fill(BLACK)
    draw_player(player_x, player_y)
    for enemy in enemies:
        draw_enemy(*enemy)
    for bullet in bullets:
        draw_bullet(*bullet)

    # Display score
    font = pygame.font.SysFont(None, 35)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Update display
    pygame.display.flip()

    # Control frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()