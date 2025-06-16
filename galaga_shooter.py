#!/usr/bin/env python3
"""
Enhanced Galaga-inspired Space Shooter Game
A 2D space shooter with advanced player and enemy mechanics, improved visuals,
animations, sound effects, and authentic ship capture/combination mechanics.
"""

import pygame
import random
import sys
import math
import os
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize sound mixer

# Game constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 800
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (173, 216, 230)

# Create the game window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Galaga Clone')
clock = pygame.time.Clock()

# Sound effects - generate simple beeps for retro feel
def create_beep_sound(freq, duration=0.1, volume=0.5):
    """Create a simple beep sound with the given frequency"""
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate))
    
    # Setup our numpy array to handle 16 bit ints, which is what we set our mixer to use
    buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
    max_sample = 2**(16 - 1) - 1
    
    for s in range(n_samples):
        t = float(s) / sample_rate    # Time in seconds
        
        # Sine wave calculations for both channels
        buf[s][0] = int(round(max_sample * volume * math.sin(2 * math.pi * freq * t)))
        buf[s][1] = int(round(max_sample * volume * math.sin(2 * math.pi * freq * t)))
    
    return pygame.sndarray.make_sound(buf)

# Try to create sound effects
try:
    import numpy
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    
    # Create sound effects with different frequencies
    shoot_sound = create_beep_sound(880, 0.05)  # Higher pitch for shooting
    explosion_sound = create_beep_sound(220, 0.2)  # Lower pitch for explosions
    hit_sound = create_beep_sound(440, 0.1)  # Medium pitch for hits
    capture_sound = create_beep_sound(330, 0.3)  # Special sound for capture
    rescue_sound = create_beep_sound(660, 0.2)  # Special sound for rescue
    wave_complete_sound = create_beep_sound(550, 0.5, 0.7)  # Longer sound for wave completion
except:
    # If sound creation fails, create dummy sound objects
    class DummySound:
        def play(self): pass
    
    shoot_sound = DummySound()
    explosion_sound = DummySound()
    hit_sound = DummySound()
    capture_sound = DummySound()
    rescue_sound = DummySound()
    wave_complete_sound = DummySound()

# High score file path
HIGH_SCORE_FILE = "galaga_high_score.txt"

# Function to load high score from file
def load_high_score():
    """
    Load the high score from a local text file.
    If the file doesn't exist or there's an error, return 0.
    """
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                return int(f.read().strip())
        return 0
    except:
        return 0

# Function to save high score to file
def save_high_score(score):
    """
    Save the high score to a local text file.
    Only save if the score is higher than the current high score.
    """
    current_high_score = load_high_score()
    if score > current_high_score:
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                f.write(str(score))
            return True  # Successfully saved new high score
        except:
            return False  # Failed to save
    return False  # No new high score

# Explosion animation class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.size = size
        self.images = []
        
        # Create explosion animation frames
        # We'll use expanding circles with fading colors for a simple explosion effect
        num_frames = 8
        max_radius = size * 1.5
        
        for i in range(num_frames):
            # Calculate radius for this frame
            radius = int((i + 1) * max_radius / num_frames)
            
            # Create a surface for this frame
            frame = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            
            # Calculate color with fading alpha
            alpha = 255 - int(255 * i / num_frames)
            
            # Draw outer explosion circle (orange/yellow)
            pygame.draw.circle(frame, (255, 165, 0, alpha), (size * 3 // 2, size * 3 // 2), radius)
            
            # Draw inner explosion circle (brighter)
            if i < num_frames - 2:
                pygame.draw.circle(frame, (255, 255, 200, alpha), 
                                  (size * 3 // 2, size * 3 // 2), radius // 2)
            
            self.images.append(frame)
        
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
    
    def update(self):
        # Update explosion animation
        self.counter += 1
        
        if self.counter >= 2:  # Control animation speed
            self.counter = 0
            self.index += 1
            
            if self.index >= len(self.images):
                self.kill()  # Remove explosion when animation is complete
            else:
                self.image = self.images[self.index]

# Scrolling starfield background
class StarField:
    def __init__(self):
        # Create multiple layers of stars with different speeds and sizes
        self.stars = []
        
        # Distant stars (small and slow)
        for _ in range(50):
            self.stars.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': 1,
                'speed': random.uniform(0.2, 0.5),
                'color': (150, 150, 150)
            })
        
        # Mid-distance stars (medium size and speed)
        for _ in range(30):
            self.stars.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': 2,
                'speed': random.uniform(0.5, 1.0),
                'color': (200, 200, 200)
            })
        
        # Close stars (larger and faster)
        for _ in range(20):
            self.stars.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': 3,
                'speed': random.uniform(1.0, 2.0),
                'color': (255, 255, 255)
            })
    
    def update(self):
        # Move stars downward to create scrolling effect
        for star in self.stars:
            star['y'] += star['speed']
            
            # Reset stars that go off screen
            if star['y'] > WINDOW_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, WINDOW_WIDTH)
    
    def draw(self, surface):
        # Draw all stars
        for star in self.stars:
            pygame.draw.circle(
                surface, 
                star['color'], 
                (int(star['x']), int(star['y'])), 
                star['size']
            )

# Player class with improved visuals
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Create player ship with improved visuals (white triangle with red accents)
        self.original_image = pygame.Surface((30, 40), pygame.SRCALPHA)
        
        # Main ship body (white triangle)
        pygame.draw.polygon(self.original_image, WHITE, [(15, 0), (0, 40), (30, 40)])
        
        # Red accents
        pygame.draw.polygon(self.original_image, RED, [(15, 10), (10, 30), (20, 30)])
        pygame.draw.rect(self.original_image, RED, (5, 35, 20, 5))
        
        # Engine glow (blue)
        pygame.draw.polygon(self.original_image, LIGHT_BLUE, [(10, 40), (20, 40), (15, 45)])
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = WINDOW_WIDTH // 2
        self.rect.bottom = WINDOW_HEIGHT - 20
        self.speed = 8
        self.shoot_delay = 250  # milliseconds
        self.last_shot = pygame.time.get_ticks()
        self.lives = 3
        
        # Ship combination mechanics
        self.combined_ships = 1  # Start with 1 ship (can go up to 2 when combined)
        self.max_combined_ships = 2  # Maximum number of ships that can be combined
        
        # Invincibility mechanics
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 2000  # 2 seconds of invincibility
        self.flash_counter = 0
        
        # Capture mechanics
        self.is_captured = False
        self.captured_by = None
        self.has_double_fire = False
        
        # Engine animation
        self.engine_anim_counter = 0
        
    def update(self):
        # Handle invincibility
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_timer > self.invincible_duration:
                self.invincible = False
            
            # Flash effect during invincibility
            self.flash_counter += 1
            if self.flash_counter % 10 < 5:  # Toggle visibility every 5 frames
                # Show appropriate ship image based on combined status
                if self.combined_ships == 2:
                    self.draw_combined_ship()
                else:
                    self.image = self.original_image.copy()
            else:
                self.image = pygame.Surface((30, 40), pygame.SRCALPHA)  # Transparent
        else:
            # Show appropriate ship image based on combined status
            if self.combined_ships == 2:
                self.draw_combined_ship()
            else:
                self.image = self.original_image.copy()
        
        # Animate engine glow
        if not self.is_captured and not self.invincible:
            self.engine_anim_counter += 1
            if self.engine_anim_counter % 10 < 5:
                # Draw pulsing engine glow
                pygame.draw.polygon(self.image, LIGHT_BLUE, [(10, 40), (20, 40), (15, 48)])
                # Draw second engine if combined
                if self.combined_ships == 2:
                    pygame.draw.polygon(self.image, LIGHT_BLUE, [(30, 40), (40, 40), (35, 48)])
        
        # If captured, don't process movement
        if self.is_captured:
            return
            
        # Get keyboard input
        keys = pygame.key.get_pressed()
        if keys[K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.right < WINDOW_WIDTH:
            self.rect.x += self.speed
    
    def draw_combined_ship(self):
        """Draw the combined ship (two ships side by side)"""
        # Create a wider surface for the combined ships
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        
        # Draw first ship
        pygame.draw.polygon(self.image, WHITE, [(15, 0), (0, 40), (30, 40)])
        pygame.draw.polygon(self.image, RED, [(15, 10), (10, 30), (20, 30)])
        pygame.draw.rect(self.image, RED, (5, 35, 20, 5))
        
        # Draw second ship (slightly offset)
        pygame.draw.polygon(self.image, WHITE, [(35, 0), (20, 40), (50, 40)])
        pygame.draw.polygon(self.image, RED, [(35, 10), (30, 30), (40, 30)])
        pygame.draw.rect(self.image, RED, (25, 35, 20, 5))

    def shoot(self):
        if self.is_captured:
            return
            
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            
            # Play shoot sound
            shoot_sound.play()
            
            # Create primary bullet
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            
            # Create additional bullets based on ship configuration
            if self.combined_ships == 2:
                # Two ships combined - fire from both positions
                bullet2 = Bullet(self.rect.centerx - 20, self.rect.top)
                all_sprites.add(bullet2)
                bullets.add(bullet2)
                
                bullet3 = Bullet(self.rect.centerx + 20, self.rect.top)
                all_sprites.add(bullet3)
                bullets.add(bullet3)
            elif self.has_double_fire:
                # Single ship with double fire power
                bullet2 = Bullet(self.rect.centerx - 20, self.rect.top)
                all_sprites.add(bullet2)
                bullets.add(bullet2)
    
    def hit(self):
        """Handle player being hit by enemy or bullet"""
        if not self.invincible and not self.is_captured:
            hit_sound.play()
            
            # If ships are combined, lose one combined ship first
            if self.combined_ships > 1:
                self.combined_ships -= 1
                self.has_double_fire = True  # Maintain double fire even after losing a combined ship
                
                # Update the ship appearance
                if self.rect.width > 30:
                    # Adjust hitbox size back to single ship
                    center_x = self.rect.centerx
                    self.rect = self.original_image.get_rect()
                    self.rect.centerx = center_x
                    self.rect.bottom = WINDOW_HEIGHT - 20
                
                # Start invincibility period
                self.invincible = True
                self.invincible_timer = pygame.time.get_ticks()
                self.flash_counter = 0
            else:
                # No combined ships left, lose a life
                self.lives -= 1
                
                if self.lives > 0:
                    # Start invincibility period
                    self.invincible = True
                    self.invincible_timer = pygame.time.get_ticks()
                    self.flash_counter = 0
    
    def get_captured(self, captor):
        """
        Player is captured by a boss enemy
        
        This is the classic Galaga capture mechanic where a boss enemy
        can capture the player's ship and carry it at the top of the screen.
        If the player has remaining lives, they can continue playing with
        a new ship while the captured one is held by the boss.
        """
        # Only allow capture if player isn't already captured and isn't invincible
        if not self.invincible and not self.is_captured:
            # Only allow capture if the player doesn't already have 2 combined ships
            if self.combined_ships < self.max_combined_ships:
                capture_sound.play()
                
                # Set capture state
                self.is_captured = True
                self.captured_by = captor
                
                # Reduce lives by 1
                self.lives -= 1
                
                # If player has lives remaining, spawn a new ship
                if self.lives > 0:
                    # The boss will visually carry the player ship
                    # Player continues with a new ship (handled in game loop)
                    pass
                else:
                    # Game over will be handled in the main game loop
                    pass
    
    def rescue(self):
        """
        Player ship is rescued after destroying the captor boss
        
        When the player destroys the boss that captured their ship,
        the captured ship returns to the player, combining with the
        current ship for enhanced firepower (up to 2 ships max).
        """
        rescue_sound.play()
        self.is_captured = False
        self.captured_by = None
        
        # Combine ships if not already at maximum
        if self.combined_ships < self.max_combined_ships:
            self.combined_ships += 1
            
            # Update hitbox for combined ships
            if self.combined_ships == 2:
                center_x = self.rect.centerx
                self.rect = pygame.Rect(0, 0, 50, 40)  # Wider hitbox for combined ships
                self.rect.centerx = center_x
                self.rect.bottom = WINDOW_HEIGHT - 20
        
        # Always enable double fire when rescued
        self.has_double_fire = True
        
        # Start invincibility period after rescue
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        self.flash_counter = 0
# Enemy class with improved visuals
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type):
        super().__init__()
        self.enemy_type = enemy_type
        
        # Different enemy types with distinct appearances and point values
        if enemy_type == "small":
            # Small bug (green with details)
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            # Main body
            pygame.draw.rect(self.image, GREEN, (0, 0, 20, 20))
            # Details
            pygame.draw.line(self.image, BLACK, (10, 0), (10, 20), 2)  # Center line
            pygame.draw.circle(self.image, YELLOW, (5, 5), 3)  # Left eye
            pygame.draw.circle(self.image, YELLOW, (15, 5), 3)  # Right eye
            
            self.points = 100
            self.health = 1
            self.speed_factor = 1.2
            self.can_capture = False
            
        elif enemy_type == "medium":
            # Medium wasp (yellow with details)
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            # Main body
            pygame.draw.polygon(self.image, YELLOW, [(15, 0), (0, 30), (30, 30)])
            # Details
            pygame.draw.line(self.image, BLACK, (15, 5), (15, 25), 2)  # Center line
            pygame.draw.circle(self.image, RED, (10, 15), 3)  # Left eye
            pygame.draw.circle(self.image, RED, (20, 15), 3)  # Right eye
            pygame.draw.line(self.image, BLACK, (5, 25), (25, 25), 2)  # Bottom line
            
            self.points = 200
            self.health = 2
            self.speed_factor = 1.0
            self.can_capture = False
            
        else:  # "large" - boss
            # Boss enemy (red with details)
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            # Main body
            pygame.draw.circle(self.image, RED, (20, 20), 20)
            # Details
            pygame.draw.circle(self.image, WHITE, (20, 20), 15)  # Inner circle
            pygame.draw.circle(self.image, RED, (20, 20), 10)  # Core
            pygame.draw.circle(self.image, YELLOW, (12, 15), 4)  # Left eye
            pygame.draw.circle(self.image, YELLOW, (28, 15), 4)  # Right eye
            pygame.draw.arc(self.image, BLACK, (10, 20, 20, 10), 0, math.pi, 2)  # Mouth
            
            self.points = 400
            self.health = 3
            self.speed_factor = 0.8
            self.can_capture = True  # Only boss enemies can capture the player
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.base_x = x  # Store original x position for wave movement
        self.base_speed = 2 * self.speed_factor
        self.speed_x = self.base_speed
        
        # Sinusoidal movement parameters
        self.wave_amplitude = random.randint(20, 40)
        self.wave_speed = random.uniform(0.05, 0.1)
        self.wave_offset = random.uniform(0, 2 * math.pi)
        self.time = random.uniform(0, 2 * math.pi)  # Starting phase
        
        # Downward movement timing
        self.last_move_down = pygame.time.get_ticks()
        self.move_down_interval = 5000  # 5 seconds
        
        # Diving behavior
        self.is_diving = False
        self.dive_path = []
        self.dive_index = 0
        self.original_pos = (x, y)
        
        # Capture mechanics
        self.has_captured_player = False
        self.captured_player_offset = (0, 40)  # Position offset for captured player ship
        self.captured_player_image = None  # Store the captured player's image
        
        # Shooting mechanics
        self.can_shoot = True
        self.shoot_delay = random.randint(3000, 8000)  # Random delay between shots
        self.last_shot = pygame.time.get_ticks() - random.randint(0, 2000)  # Randomize initial shot time
        
        # Animation
        self.anim_counter = 0
        self.original_image = self.image.copy()
        self.alt_image = self.image.copy()
        
        # Create alternate animation frame
        if enemy_type == "small":
            # Alternate eyes for small bug
            pygame.draw.circle(self.alt_image, WHITE, (5, 5), 3)
            pygame.draw.circle(self.alt_image, WHITE, (15, 5), 3)
        elif enemy_type == "medium":
            # Alternate wings for medium wasp
            pygame.draw.polygon(self.alt_image, ORANGE, [(15, 0), (0, 30), (30, 30)])
            pygame.draw.line(self.alt_image, BLACK, (15, 5), (15, 25), 2)
            pygame.draw.circle(self.alt_image, RED, (10, 15), 3)
            pygame.draw.circle(self.alt_image, RED, (20, 15), 3)
        else:  # "large"
            # Alternate eyes for boss
            pygame.draw.circle(self.alt_image, RED, (12, 15), 4)
            pygame.draw.circle(self.alt_image, RED, (28, 15), 4)

    def update(self):
        # Animate enemy
        self.anim_counter += 1
        if self.anim_counter % 30 < 15:  # Switch animation frame every 15 frames
            self.image = self.original_image
        else:
            self.image = self.alt_image
        
        # Check if it's time to shoot
        if self.can_shoot:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.shoot()
                self.last_shot = now
                self.shoot_delay = random.randint(3000, 8000)  # Randomize next shot delay
        
        if self.is_diving:
            # Follow pre-calculated dive path
            if self.dive_index < len(self.dive_path):
                self.rect.x, self.rect.y = self.dive_path[self.dive_index]
                self.dive_index += 1
                
                # Check for capture opportunity during dive
                if self.can_capture and not self.has_captured_player and self.dive_index > len(self.dive_path) // 2:
                    # Try to capture player if close enough
                    if player.rect.colliderect(self.rect) and not player.invincible and not player.is_captured:
                        player.get_captured(self)
                        self.has_captured_player = True
                        # Immediately return to formation after capture
                        self.is_diving = False
                        self.rect.y = 50
                        self.rect.x = random.randint(50, WINDOW_WIDTH - 50)
                        self.base_x = self.rect.x
            else:
                # Return to normal behavior after dive
                self.is_diving = False
                # Place back at a reasonable position if dive completed
                if self.rect.y > WINDOW_HEIGHT:
                    self.rect.y = 50
                    self.rect.x = random.randint(50, WINDOW_WIDTH - 50)
                    self.base_x = self.rect.x
        else:
            # Normal sinusoidal movement
            self.time += self.wave_speed
            
            # Calculate new position with sinusoidal wave pattern
            self.rect.x = self.base_x + int(self.wave_amplitude * math.sin(self.time + self.wave_offset))
            
            # Change direction and adjust base_x when hitting the edge
            if self.rect.right > WINDOW_WIDTH:
                self.base_x = WINDOW_WIDTH - self.rect.width - self.wave_amplitude
                self.speed_x = -abs(self.speed_x)
            elif self.rect.left < 0:
                self.base_x = self.wave_amplitude
                self.speed_x = abs(self.speed_x)
            
            # Move base_x position
            self.base_x += self.speed_x
            
            # Check if it's time to move down
            now = pygame.time.get_ticks()
            if now - self.last_move_down > self.move_down_interval:
                self.rect.y += 20
                self.last_move_down = now
        
        # Update position of captured player ship if this enemy has captured one
        if self.has_captured_player:
            player.rect.x = self.rect.x + self.captured_player_offset[0]
            player.rect.y = self.rect.y + self.captured_player_offset[1]
            
            # Draw the captured player ship
            if self.captured_player_image is None:
                # Create a captured player ship image (slightly smaller)
                self.captured_player_image = pygame.Surface((25, 35), pygame.SRCALPHA)
                pygame.draw.polygon(self.captured_player_image, WHITE, [(12, 0), (0, 35), (25, 35)])
                pygame.draw.polygon(self.captured_player_image, RED, [(12, 10), (8, 25), (16, 25)])

    def start_dive(self, target_x, target_y):
        """
        Initiate a diving attack toward the player
        """
        # Only allow diving if not already carrying a captured player
        if self.has_captured_player:
            return
            
        self.is_diving = True
        self.dive_index = 0
        self.original_pos = (self.rect.x, self.rect.y)
        
        # Calculate a curved path for diving
        self.dive_path = []
        start_x, start_y = self.rect.x, self.rect.y
        
        # Create a bezier curve for diving
        control_x = start_x + random.randint(-100, 100)
        control_y = (start_y + target_y) // 2 - 50
        
        # Generate points along the curve
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier curve formula
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * target_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * target_y
            self.dive_path.append((int(x), int(y)))
    
    def shoot(self):
        """Enemy shoots a bullet toward the player"""
        if random.random() < 0.3:  # 30% chance to actually fire
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

# Bullet classes with improved visuals
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Create a glowing bullet effect
        self.image = pygame.Surface((6, 12), pygame.SRCALPHA)
        
        # Main bullet (white dot with glow)
        pygame.draw.circle(self.image, WHITE, (3, 6), 3)
        pygame.draw.circle(self.image, (100, 255, 100, 128), (3, 6), 5)  # Green glow
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10  # Negative because it moves upward

    def update(self):
        self.rect.y += self.speed
        # Remove bullet if it goes off screen
        if self.rect.bottom < 0:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Create a glowing enemy bullet effect
        self.image = pygame.Surface((6, 12), pygame.SRCALPHA)
        
        # Main bullet (red dot with glow)
        pygame.draw.circle(self.image, RED, (3, 6), 3)
        pygame.draw.circle(self.image, (255, 100, 100, 128), (3, 6), 5)  # Red glow
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = 7  # Positive because it moves downward

    def update(self):
        self.rect.y += self.speed
        # Remove bullet if it goes off screen
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

# Function to draw player lives as ship icons
def draw_lives(surface, x, y, lives, image):
    for i in range(lives):
        img_rect = image.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surface.blit(image, img_rect)

# Wave management
def create_enemies_formation(formation):
    """
    Create a wave of enemies in different formations
    """
    enemies.empty()  # Clear any existing enemies
    
    enemy_types = ["small", "medium", "large"]
    
    if formation == "grid":
        # Standard grid formation
        cols, rows = 5, 2
        for row in range(rows):
            for col in range(cols):
                # Mix of enemy types
                enemy_type = enemy_types[random.randint(0, 2)]
                enemy = Enemy(col * 80 + 100, row * 60 + 50, enemy_type)
                all_sprites.add(enemy)
                enemies.add(enemy)
    
    elif formation == "diamond":
        # Diamond formation
        positions = [
            (WINDOW_WIDTH // 2, 50),  # Top
            (WINDOW_WIDTH // 2 - 80, 100),  # Left
            (WINDOW_WIDTH // 2 + 80, 100),  # Right
            (WINDOW_WIDTH // 2, 150),  # Bottom
            (WINDOW_WIDTH // 2 - 40, 75),  # Top-left
            (WINDOW_WIDTH // 2 + 40, 75),  # Top-right
            (WINDOW_WIDTH // 2 - 40, 125),  # Bottom-left
            (WINDOW_WIDTH // 2 + 40, 125),  # Bottom-right
            (WINDOW_WIDTH // 2 - 120, 150),  # Far left
            (WINDOW_WIDTH // 2 + 120, 150),  # Far right
        ]
        
        for i, pos in enumerate(positions):
            enemy_type = enemy_types[i % 3]
            enemy = Enemy(pos[0], pos[1], enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)
    
    elif formation == "arc":
        # Arc formation
        center_x = WINDOW_WIDTH // 2
        radius = 150
        count = 10
        
        for i in range(count):
            angle = math.pi * i / (count - 1)  # Angle from 0 to π
            x = center_x + int(radius * math.cos(angle))
            y = 100 + int(radius * math.sin(angle))
            
            enemy_type = enemy_types[i % 3]
            enemy = Enemy(x, y, enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)
    
    elif formation == "v_shape":
        # V-shaped formation
        center_x = WINDOW_WIDTH // 2
        count = 10
        spacing = 40
        
        for i in range(count // 2):
            # Left side of V
            enemy_type = enemy_types[i % 3]
            enemy = Enemy(center_x - (i + 1) * spacing, 50 + i * 30, enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)
            
            # Right side of V
            enemy_type = enemy_types[(i + 1) % 3]
            enemy = Enemy(center_x + (i + 1) * spacing, 50 + i * 30, enemy_type)
            all_sprites.add(enemy)
            enemies.add(enemy)

# Function to draw text
def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

# Function to show start screen
def show_start_screen():
    """
    Display the start screen with game title and instructions
    """
    # Create starfield background
    starfield = StarField()
    
    # Main game loop for start screen
    waiting = True
    while waiting:
        clock.tick(FPS)
        
        # Process events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    waiting = False  # Start the game when Enter is pressed
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Update starfield
        starfield.update()
        
        # Draw background
        window.fill(BLACK)
        starfield.draw(window)
        
        # Draw title and instructions
        draw_text(window, "GALAGA CLONE", 64, WINDOW_WIDTH // 2, 100)
        draw_text(window, "Arrow keys to move, Space to shoot", 22, WINDOW_WIDTH // 2, 300)
        draw_text(window, "Press ENTER to start", 18, WINDOW_WIDTH // 2, 350)
        draw_text(window, "High Score: " + str(load_high_score()), 22, WINDOW_WIDTH // 2, 400)
        
        # Draw a sample player ship
        sample_ship = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.polygon(sample_ship, WHITE, [(15, 0), (0, 40), (30, 40)])
        pygame.draw.polygon(sample_ship, RED, [(15, 10), (10, 30), (20, 30)])
        pygame.draw.rect(sample_ship, RED, (5, 35, 20, 5))
        window.blit(sample_ship, (WINDOW_WIDTH // 2 - 15, 200))
        
        pygame.display.flip()

# Function to show game over screen
def show_game_over_screen(score):
    """
    Display the game over screen with final score and options to restart or quit
    """
    # Check if we have a new high score
    is_new_high_score = save_high_score(score)
    high_score = load_high_score()
    
    # Create starfield background
    starfield = StarField()
    
    # Main game loop for game over screen
    waiting = True
    while waiting:
        clock.tick(FPS)
        
        # Process events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_r:
                    waiting = False  # Restart the game when R is pressed
                elif event.key == K_q or event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Update starfield
        starfield.update()
        
        # Draw background
        window.fill(BLACK)
        starfield.draw(window)
        
        # Draw game over text and score
        draw_text(window, "GAME OVER", 64, WINDOW_WIDTH // 2, 100, RED)
        draw_text(window, f"Final Score: {score}", 36, WINDOW_WIDTH // 2, 200)
        
        if is_new_high_score:
            draw_text(window, "NEW HIGH SCORE!", 36, WINDOW_WIDTH // 2, 250, YELLOW)
        
        draw_text(window, f"High Score: {high_score}", 28, WINDOW_WIDTH // 2, 300)
        draw_text(window, "Press R to restart", 22, WINDOW_WIDTH // 2, 400)
        draw_text(window, "Press Q to quit", 22, WINDOW_WIDTH // 2, 430)
        
        pygame.display.flip()
    
    return True  # Return True to indicate we want to restart the game
# Main game function
def run_game():
    # Create sprite groups
    global all_sprites, enemies, bullets, enemy_bullets, player, explosions
    
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    
    # Create player
    player = Player()
    all_sprites.add(player)
    
    # Create starfield background
    starfield = StarField()
    
    # Wave management
    current_wave = 0
    wave_formations = ["grid", "diamond", "arc", "v_shape"]
    
    # Create initial wave of enemies
    create_enemies_formation("grid")
    
    # Game loop variables
    score = 0
    font = pygame.font.Font(None, 36)
    last_dive_time = pygame.time.get_ticks()
    dive_interval = 3000  # Time between enemy dives (3 seconds)
    
    # Create a small ship icon for lives display
    life_icon = pygame.Surface((20, 25), pygame.SRCALPHA)
    pygame.draw.polygon(life_icon, WHITE, [(10, 0), (0, 25), (20, 25)])
    pygame.draw.polygon(life_icon, RED, [(10, 5), (5, 20), (15, 20)])
    
    # Main game loop
    running = True
    
    # Track if player is currently respawning after capture
    respawning = False
    respawn_timer = 0
    respawn_delay = 1000  # 1 second delay before respawning
    
    while running:
        # Keep the game running at the right speed
        clock.tick(FPS)
        
        # Process events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    player.shoot()
        
        # Handle player respawning after capture
        if respawning:
            current_time = pygame.time.get_ticks()
            if current_time - respawn_timer > respawn_delay:
                respawning = False
                player.invincible = True
                player.invincible_timer = current_time
                player.flash_counter = 0
        
        # Update all game objects
        all_sprites.update()
        starfield.update()
        
        # Check for bullet-enemy collisions
        hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for bullet, hit_enemies in hits.items():
            for enemy in hit_enemies:
                enemy.health -= 1
                if enemy.health <= 0:
                    # Check if this enemy had captured the player
                    if enemy.has_captured_player:
                        player.rescue()  # Rescue the player's ship
                    
                    # Create explosion animation
                    explosion = Explosion(enemy.rect.centerx, enemy.rect.centery, enemy.rect.width)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    
                    # Play explosion sound
                    explosion_sound.play()
                    
                    # Add points based on enemy type
                    score += enemy.points
                    enemy.kill()
        
        # Check for enemy bullet-player collisions
        if not player.is_captured and not player.invincible:
            if pygame.sprite.spritecollide(player, enemy_bullets, True):
                player.hit()
                # Create small explosion for hit effect
                hit_explosion = Explosion(player.rect.centerx, player.rect.top, 15)
                all_sprites.add(hit_explosion)
                explosions.add(hit_explosion)
        
        # Check for enemy-player collisions (only if player is not invincible and not captured)
        if not player.is_captured and not player.invincible:
            enemy_collisions = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in enemy_collisions:
                # Only bosses can capture, and only if they don't already have a captured ship
                # and the player doesn't already have 2 combined ships
                if enemy.can_capture and not enemy.has_captured_player and player.combined_ships < player.max_combined_ships and random.random() < 0.3:
                    player.get_captured(enemy)
                    enemy.has_captured_player = True
                    
                    # Start respawn timer if player has lives left
                    if player.lives > 0:
                        respawning = True
                        respawn_timer = pygame.time.get_ticks()
                        
                        # Reset player position for next life
                        player.rect.centerx = WINDOW_WIDTH // 2
                        player.rect.bottom = WINDOW_HEIGHT - 20
                else:
                    player.hit()
                    # Create explosion for collision
                    collision_explosion = Explosion(enemy.rect.centerx, enemy.rect.centery, enemy.rect.width)
                    all_sprites.add(collision_explosion)
                    explosions.add(collision_explosion)
                    enemy.kill()  # Enemy is destroyed in collision
        
        # Check if all enemies are destroyed - create new wave with different formation
        if len(enemies) == 0:
            # Play wave completion sound
            wave_complete_sound.play()
            
            current_wave += 1
            formation = wave_formations[current_wave % len(wave_formations)]
            create_enemies_formation(formation)
        
        # Randomly select enemies to dive toward the player
        now = pygame.time.get_ticks()
        if now - last_dive_time > dive_interval and len(enemies) > 0:
            last_dive_time = now
            
            # Select 1-2 enemies to dive
            dive_count = min(random.randint(1, 2), len(enemies))
            diving_enemies = random.sample(list(enemies), dive_count)
            
            for enemy in diving_enemies:
                if not enemy.is_diving and not enemy.has_captured_player:
                    # Target slightly ahead of the player
                    target_x = player.rect.centerx + random.randint(-50, 50)
                    target_y = WINDOW_HEIGHT + 50  # Just below the screen
                    enemy.start_dive(target_x, target_y)
        
        # Check for game over
        if player.lives <= 0:
            running = False
        
        # Draw everything
        window.fill(BLACK)  # Clear the screen
        
        # Draw starfield background
        starfield.draw(window)
        
        # Draw all sprites
        all_sprites.draw(window)
        
        # Draw score in top-right corner
        score_text = font.render(f"Score: {score}", True, WHITE)
        score_rect = score_text.get_rect()
        score_rect.topright = (WINDOW_WIDTH - 10, 10)
        window.blit(score_text, score_rect)
        
        # Draw high score
        high_score = load_high_score()
        high_score_text = font.render(f"High: {high_score}", True, WHITE)
        high_score_rect = high_score_text.get_rect()
        high_score_rect.topright = (WINDOW_WIDTH - 10, 50)
        window.blit(high_score_text, high_score_rect)
        
        # Draw lives as ship icons
        draw_lives(window, 10, 10, player.lives, life_icon)
        
        # Draw wave number
        wave_text = font.render(f"Wave: {current_wave + 1}", True, WHITE)
        wave_rect = wave_text.get_rect()
        wave_rect.topleft = (10, 50)
        window.blit(wave_text, wave_rect)
        
        # Draw combined ships indicator if applicable
        if player.combined_ships > 1:
            combined_text = font.render(f"Combined: {player.combined_ships}", True, YELLOW)
            combined_rect = combined_text.get_rect()
            combined_rect.topleft = (10, 90)
            window.blit(combined_text, combined_rect)
        
        # Draw captured ship indicator if player is captured
        if player.is_captured:
            captured_text = font.render("SHIP CAPTURED!", True, RED)
            captured_rect = captured_text.get_rect()
            captured_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50)
            window.blit(captured_text, captured_rect)
        
        # Update the display
        pygame.display.flip()
    
    # Game over - show game over screen and return whether to restart
    return show_game_over_screen(score)

# Main game loop with menu system
def main():
    # Show start screen
    show_start_screen()
    
    # Run game loop until player quits
    while True:
        restart = run_game()
        if not restart:
            break

# Start the game
if __name__ == "__main__":
    main()
