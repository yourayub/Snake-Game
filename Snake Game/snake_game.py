import pygame
import random
import sys
import os
import math
import webbrowser
try:
    from PIL import Image, ImageFilter
except ImportError:
    Image = None
    ImageFilter = None

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1600, 900
CELL_SIZE = 50

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 80, 80)
BLACK = (0, 0, 0)
BG_DARK = (15, 18, 35)
PANEL = (25, 30, 50)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

FRUIT_EMOJIS = ["🍎", "🍌", "🍉", "🍇", "🍓", "🍍", "🍒", "🥝", "🍑", "🍋"]
FRUIT_NAMES = {
    "🍎": "Apple",
    "🍌": "Banana",
    "🍉": "Watermelon",
    "🍇": "Grapes",
    "🍓": "Strawberry",
    "🍍": "Pineapple",
    "🍒": "Cherry",
    "🥝": "Kiwi",
    "🍑": "Peach",
    "🍋": "Lemon",
}
DIFFICULTY_SPEEDS = {
    "easy": 200,
    "medium": 150,
    "hard": 100,
}

def random_position():
    x = random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
    y = random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
    return (x, y)


def random_food_position(snake):
    food = random_position()
    while food in snake:
        food = random_position()
    return food


def load_blurred_background(image_path, blur_radius, fallback_color=BG_DARK):
    """Load and blur an image when Pillow/file is available, else return fallback surface."""
    fallback = pygame.Surface((WIDTH, HEIGHT))
    fallback.fill(fallback_color)

    if Image is None or ImageFilter is None or not os.path.exists(image_path):
        return fallback

    try:
        bg_img = Image.open(image_path).resize((WIDTH, HEIGHT)).filter(ImageFilter.GaussianBlur(radius=blur_radius))
        bg_img = bg_img.convert("RGB")
        return pygame.image.fromstring(bg_img.tobytes(), bg_img.size, "RGB")
    except Exception:
        return fallback

def draw_button(screen, rect, text, font, base_color, hover_color, border_color, text_color, mouse_pos, scale=1.0, glow=False, glow_color=(255,255,100), border_radius=32):
    is_hovered = rect.collidepoint(mouse_pos)
    # Scale the button
    scaled_rect = rect.copy()
    center = rect.center
    scaled_rect.width = int(rect.width * scale)
    scaled_rect.height = int(rect.height * scale)
    scaled_rect.center = center
    color = hover_color if is_hovered else base_color
    # Draw everything on a surface for proper clipping
    button_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
    # Glow inside the button
    if glow and is_hovered:
        glow_rect = pygame.Rect(0, 0, scaled_rect.width, scaled_rect.height)
        pygame.draw.rect(button_surf, (*glow_color, 80), glow_rect, border_radius=border_radius)
    # Draw button background
    pygame.draw.rect(button_surf, color, button_surf.get_rect(), border_radius=border_radius)
    # Draw border
    pygame.draw.rect(button_surf, border_color, button_surf.get_rect(), width=3, border_radius=border_radius)
    # Draw text
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=button_surf.get_rect().center)
    button_surf.blit(text_surf, text_rect)
    # Blit the button surface to the screen
    screen.blit(button_surf, button_surf.get_rect(center=center))
    return is_hovered, scaled_rect


def draw_gameplay(
    screen, bg, overlay, snake, food, fruit_emoji, score, high_score,
    game_font, emoji_font, animation_time_ms, popup_animation
):
    screen.blit(bg, (0, 0))
    screen.blit(overlay, (0, 0))

    # Draw boundary
    boundary_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
    pygame.draw.rect(screen, (80, 110, 170), boundary_rect, width=4, border_radius=6)

    # Draw snake
    total_segments = len(snake)
    max_size = CELL_SIZE - 2
    min_size = max(12, CELL_SIZE // 2)
    for i, segment in enumerate(snake):
        if total_segments > 1:
            ratio = (total_segments - 1 - i) / (total_segments - 1)
            size = int(max_size - (max_size - min_size) * ratio)
        else:
            size = max_size
        offset = (CELL_SIZE - size) // 2
        color = (100, 255, 150) if i == 0 else GREEN
        pygame.draw.rect(screen, color, (segment[0] + offset, segment[1] + offset, size, size), border_radius=12)

    # Draw fruit emoji with subtle continuous "tiptip" zoom animation.
    fruit_surf = emoji_font.render(fruit_emoji, True, WHITE)
    pulse = 1.0 + 0.08 * math.sin(animation_time_ms / 220.0)
    scaled_width = max(18, int(fruit_surf.get_width() * pulse))
    scaled_height = max(18, int(fruit_surf.get_height() * pulse))
    fruit_zoom = pygame.transform.smoothscale(fruit_surf, (scaled_width, scaled_height))
    fruit_rect = fruit_zoom.get_rect(center=(food[0] + CELL_SIZE // 2, food[1] + CELL_SIZE // 2))
    screen.blit(fruit_zoom, fruit_rect)

    score_text = game_font.render(f"Score: {score}", True, WHITE)
    high_score_text = game_font.render(f"Best: {high_score}", True, (255, 215, 0))
    screen.blit(score_text, (18, 16))
    screen.blit(high_score_text, (18, 58))

    # Animated fruit name popup when a fruit is eaten.
    if popup_animation["active"]:
        elapsed = animation_time_ms - popup_animation["start_time"]
        duration = popup_animation["duration"]
        if elapsed >= duration:
            popup_animation["active"] = False
        else:
            progress = elapsed / duration
            alpha = int(255 * (1.0 - progress))
            scale = 1.0 + 0.28 * math.sin(progress * math.pi)
            y_offset = int(65 * progress)
            popup_text = popup_animation["text"]
            popup_color = popup_animation["color"]
            name_surf = game_font.render(f"+1  {popup_text}", True, popup_color)
            popup_w = max(30, int(name_surf.get_width() * scale))
            popup_h = max(20, int(name_surf.get_height() * scale))
            popup_scaled = pygame.transform.smoothscale(name_surf, (popup_w, popup_h))
            popup_scaled.set_alpha(alpha)
            popup_rect = popup_scaled.get_rect(center=(WIDTH // 2, 125 - y_offset))
            screen.blit(popup_scaled, popup_rect)


def welcome_screen(screen):
    bg = load_blurred_background('cover.png', 18)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    title_font = pygame.font.SysFont('arial', 68, bold=True)
    subtitle_font = pygame.font.SysFont('arial', 44, italic=True)
    info_font = pygame.font.SysFont('arial', 28)
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    min_show_ms = 1600

    while True:
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if now - start_time >= min_show_ms:
                    return

        screen.blit(bg, (0, 0))
        screen.blit(overlay, (0, 0))

        title = title_font.render("Welcome to Snake Game For Everyone", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 45))
        screen.blit(title, title_rect)

        subtitle = subtitle_font.render("Let's Play for Enjoying Your Every Moment", True, (210, 225, 255))
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 28))
        screen.blit(subtitle, subtitle_rect)

        hint_alpha = int(140 + 80 * (0.5 + 0.5 * math.sin(now / 260.0)))
        hint = info_font.render("Press any key or click to continue", True, (240, 240, 240))
        hint.set_alpha(hint_alpha)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(hint, hint_rect)

        pygame.display.flip()
        clock.tick(60)

def start_screen(screen, font, high_score):
    # Load and blur background image for start screen
    #cover image

    bg = load_blurred_background('background copy.jpg', 24)
    # Create a darker semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 180/255 alpha for more darkness

    start_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 60, 240, 70)
    about_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 30, 240, 70)
    high_score_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 120, 240, 70)
    contact_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 210, 240, 70)
    exit_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 300, 240, 70)
    button_scales = {'start': 1.0, 'about': 1.0, 'high_score': 1.0, 'contact': 1.0, 'exit': 1.0}
    scale_speed = 0.12
    max_scale = 1.13
    min_scale = 1.0
    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(mouse_pos):
                    return 'start'
                elif about_button_rect.collidepoint(mouse_pos):
                    return 'about'
                elif high_score_button_rect.collidepoint(mouse_pos):
                    return 'high_score'
                elif contact_button_rect.collidepoint(mouse_pos):
                    return 'contact'
                elif exit_button_rect.collidepoint(mouse_pos):
                    return 'exit'
        # Draw blurred, dark background
        screen.blit(bg, (0, 0))
        screen.blit(overlay, (0, 0))
        title = font.render('Snake Game', True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180))
        screen.blit(title, title_rect)
        # Draw Highest Score (text, not button)
        high_score_text = font.render(f'Highest Score: {high_score}', True, (255, 215, 0))
        high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110))
        screen.blit(high_score_text, high_score_rect)
        # Draw Start button
        hovered_start, _ = draw_button(
            screen, start_button_rect, 'Start', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['start'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered_start:
            button_scales['start'] += (max_scale - button_scales['start']) * scale_speed
        else:
            button_scales['start'] += (min_scale - button_scales['start']) * scale_speed
        # Draw About button
        hovered_about, _ = draw_button(
            screen, about_button_rect, 'About', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['about'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered_about:
            button_scales['about'] += (max_scale - button_scales['about']) * scale_speed
        else:
            button_scales['about'] += (min_scale - button_scales['about']) * scale_speed
        # Draw Scores button (was Highest Score)
        hovered_high_score, _ = draw_button(
            screen, high_score_button_rect, 'Scores', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['high_score'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered_high_score:
            button_scales['high_score'] += (max_scale - button_scales['high_score']) * scale_speed
        else:
            button_scales['high_score'] += (min_scale - button_scales['high_score']) * scale_speed
        # Draw Contact button
        hovered_contact, _ = draw_button(
            screen, contact_button_rect, 'Contact', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['contact'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered_contact:
            button_scales['contact'] += (max_scale - button_scales['contact']) * scale_speed
        else:
            button_scales['contact'] += (min_scale - button_scales['contact']) * scale_speed
        # Draw Exit button
        hovered_exit, _ = draw_button(
            screen, exit_button_rect, 'Exit', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['exit'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered_exit:
            button_scales['exit'] += (max_scale - button_scales['exit']) * scale_speed
        else:
            button_scales['exit'] += (min_scale - button_scales['exit']) * scale_speed
        pygame.display.flip()
        clock.tick(60)


def contact_screen(screen, font):
    back_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 120, 200, 60)
    button_scale = 1.0
    scale_speed = 0.12
    max_scale = 1.13
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont('segoeui', 48, bold=True)
    info_font = pygame.font.SysFont('segoeui', 26, bold=True)
    value_font = pygame.font.SysFont('segoeui', 21)
    hint_font = pygame.font.SysFont('segoeui', 18, italic=True)
    status_font = pygame.font.SysFont('segoeui', 18, bold=True)
    profile_links = [
        {"platform": "Facebook", "value": "https://www.facebook.com/yoursayub", "url": "https://www.facebook.com/yoursayub"},
        {"platform": "Instagram", "value": "https://www.instagram.com/yours_ayub", "url": "https://www.instagram.com/yours_ayub"},
        {"platform": "LinkedIn", "value": "www.linkedin.com/in/yourayub", "url": "https://www.linkedin.com/in/yourayub"},
        {"platform": "GitHub", "value": "https://github.com/ayubvai11", "url": "https://github.com/ayubvai11"},
        {"platform": "Gmail", "value": "mdayubvai11@gmail.com", "url": "mailto:mdayubvai11@gmail.com"},
    ]
    status_text = ""
    status_timer = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()
        clickable_rects = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                click_pos = event.pos
                if back_button_rect.collidepoint(click_pos):
                    return
                for link_rect, url in clickable_rects:
                    if link_rect.collidepoint(click_pos):
                        webbrowser.open_new_tab(url)
                        status_text = "Opened in browser"
                        status_timer = 90
                        break

        screen.fill((14, 20, 37))
        card_rect = pygame.Rect(WIDTH // 2 - 620, 115, 1240, 620)
        pygame.draw.rect(screen, (22, 34, 60), card_rect, border_radius=20)

        header_glow_rect = pygame.Rect(WIDTH // 2 - 200, 28, 400, 74)
        header_glow = pygame.Surface((header_glow_rect.width, header_glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(header_glow, (38, 63, 106, 210), header_glow.get_rect(), border_radius=20)
        screen.blit(header_glow, header_glow_rect.topleft)
        title = title_font.render('Contact', True, (238, 245, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 65))
        screen.blit(title, title_rect)

        y = 175
        for link in profile_links:
            row_rect = pygame.Rect(WIDTH // 2 - 560, y, 1120, 76)
            row_hovered = row_rect.collidepoint(mouse_pos)
            row_color = (30, 45, 76) if row_hovered else (27, 41, 70)
            pygame.draw.rect(screen, row_color, row_rect, border_radius=12)

            label_text = info_font.render(link["platform"], True, (182, 224, 248))
            screen.blit(label_text, (row_rect.left + 24, row_rect.top + 10))

            value_color = (237, 242, 251)
            value_text = value_font.render(link["value"], True, value_color)
            value_rect = value_text.get_rect(midleft=(row_rect.left + 240, row_rect.centery))
            screen.blit(value_text, value_rect)
            clickable_rects.append((value_rect.inflate(12, 10), link["url"]))

            y += 88

        hint = hint_font.render("Click any profile or email value to open it.", True, (201, 213, 233))
        hint_rect = hint.get_rect(midtop=(WIDTH // 2, card_rect.bottom - 80))
        screen.blit(hint, hint_rect)
        if status_timer > 0:
            status_color = (147, 255, 171) if "Copied" in status_text else (190, 223, 255)
            status = status_font.render(status_text, True, status_color)
            status_rect = status.get_rect(center=(WIDTH // 2, HEIGHT - 146))
            screen.blit(status, status_rect)
            status_timer -= 1

        hovered, _ = draw_button(
            screen, back_button_rect, 'Back', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(255, 255, 255),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scale,
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered:
            button_scale += (max_scale - button_scale) * scale_speed
        else:
            button_scale += (1.0 - button_scale) * scale_speed

        pygame.display.flip()
        clock.tick(60)


def about_screen(screen, font):
    back_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 120, 200, 60)
    button_scale = 1.0
    scale_speed = 0.12
    max_scale = 1.13
    min_scale = 1.0
    clock = pygame.time.Clock()
    running = True
    rules = [
        "Rules & How to Play:",
        "- Use arrow keys to move the snake.",
        "- Eat the fruit emojis to grow and score points.",
        "- Don't hit the walls or yourself.",
        "- Press 'P' or Pause button to pause/resume.",
        "- Try to beat the highest score!",
        "",
        "THE GAME CREATE BY MOHAMMAD AYUB WITH THE HELP OF CURSOR",
        "",
        "Privacy & Cookie Policy:",
        "- This game does not collect any personal data.",
        "- No cookies or tracking are used.",
        "- All game data is stored locally (high score)."
    ]
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(mouse_pos):
                    return
        screen.fill((30, 30, 60))
        # Draw About Title
        title = font.render('About', True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title, title_rect)
        # Draw rules and info
        info_font = pygame.font.SysFont('arial', 32)
        y = 150
        for line in rules:
            text = info_font.render(line, True, (220, 220, 220))
            text_rect = text.get_rect(center=(WIDTH // 2, y))
            screen.blit(text, text_rect)
            y += 40
        # Draw Back button
        hovered, _ = draw_button(
            screen, back_button_rect, 'Back', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scale,
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered:
            button_scale += (max_scale - button_scale) * scale_speed
        else:
            button_scale += (min_scale - button_scale) * scale_speed
        pygame.display.flip()
        clock.tick(60)

def high_score_screen(screen, font, high_score):
    back_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 120, 200, 60)
    button_scale = 1.0
    scale_speed = 0.12
    max_scale = 1.13
    min_scale = 1.0
    clock = pygame.time.Clock()
    running = True
    # Load all scores
    scores = []
    if os.path.exists('scores.txt'):
        with open('scores.txt', 'r') as f:
            for line in f:
                try:
                    scores.append(int(line.strip()))
                except ValueError:
                    continue
    scores.sort(reverse=True)
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(mouse_pos):
                    return
        screen.fill((30, 30, 60))
        # Draw Highest Score Title
        title = font.render('All Scores', True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title, title_rect)
        # Draw the scores list
        info_font = pygame.font.SysFont('arial', 32)
        y = 150
        if scores:
            max_score = max(scores)
            for i, score in enumerate(scores):
                if score == max_score:
                    color = (255, 215, 0)  # Gold for highest
                else:
                    color = (220, 220, 220)
                text = info_font.render(f"{i+1}. {score}", True, color)
                text_rect = text.get_rect(center=(WIDTH // 2, y))
                screen.blit(text, text_rect)
                y += 40
        else:
            text = info_font.render("No scores yet.", True, (220, 220, 220))
            text_rect = text.get_rect(center=(WIDTH // 2, y))
            screen.blit(text, text_rect)
        # Draw Back button
        hovered, _ = draw_button(
            screen, back_button_rect, 'Back', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scale,
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )
        if hovered:
            button_scale += (max_scale - button_scale) * scale_speed
        else:
            button_scale += (min_scale - button_scale) * scale_speed
        pygame.display.flip()
        clock.tick(60)


def difficulty_screen(screen, font):
    easy_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 60, 240, 70)
    medium_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 30, 240, 70)
    hard_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 120, 240, 70)
    back_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 210, 240, 70)
    button_scales = {'easy': 1.0, 'medium': 1.0, 'hard': 1.0, 'back': 1.0}
    scale_speed = 0.12
    max_scale = 1.13
    min_scale = 1.0
    clock = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button_rect.collidepoint(mouse_pos):
                    return "easy"
                elif medium_button_rect.collidepoint(mouse_pos):
                    return "medium"
                elif hard_button_rect.collidepoint(mouse_pos):
                    return "hard"
                elif back_button_rect.collidepoint(mouse_pos):
                    return None

        screen.fill((30, 30, 60))
        title = font.render('Select Difficulty', True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180))
        screen.blit(title, title_rect)

        hovered_easy, _ = draw_button(
            screen, easy_button_rect, 'Easy', font,
            base_color=(255, 255, 255),
            hover_color=(140, 235, 160),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['easy'],
            glow=True,
            glow_color=(160, 255, 180),
            border_radius=32
        )
        hovered_medium, _ = draw_button(
            screen, medium_button_rect, 'Medium', font,
            base_color=(255, 255, 255),
            hover_color=(255, 225, 140),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['medium'],
            glow=True,
            glow_color=(255, 235, 170),
            border_radius=32
        )
        hovered_hard, _ = draw_button(
            screen, hard_button_rect, 'Hard', font,
            base_color=(255, 255, 255),
            hover_color=(255, 130, 130),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['hard'],
            glow=True,
            glow_color=(255, 160, 160),
            border_radius=32
        )
        hovered_back, _ = draw_button(
            screen, back_button_rect, 'Back', font,
            base_color=(255, 255, 255),
            hover_color=(100, 200, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=button_scales['back'],
            glow=True,
            glow_color=(200, 200, 200),
            border_radius=32
        )

        if hovered_easy:
            button_scales['easy'] += (max_scale - button_scales['easy']) * scale_speed
        else:
            button_scales['easy'] += (min_scale - button_scales['easy']) * scale_speed

        if hovered_medium:
            button_scales['medium'] += (max_scale - button_scales['medium']) * scale_speed
        else:
            button_scales['medium'] += (min_scale - button_scales['medium']) * scale_speed

        if hovered_hard:
            button_scales['hard'] += (max_scale - button_scales['hard']) * scale_speed
        else:
            button_scales['hard'] += (min_scale - button_scales['hard']) * scale_speed

        if hovered_back:
            button_scales['back'] += (max_scale - button_scales['back']) * scale_speed
        else:
            button_scales['back'] += (min_scale - button_scales['back']) * scale_speed

        pygame.display.flip()
        clock.tick(60)

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Snake Game')
    clock = pygame.time.Clock()

    # Load high score
    highscore_file = 'highscore.txt'
    high_score = 0
    if os.path.exists(highscore_file):
        with open(highscore_file, 'r') as f:
            try:
                high_score = int(f.read())
            except ValueError:
                high_score = 0

    snake = []
    direction = RIGHT
    next_direction = RIGHT
    food = (0, 0)
    score = 0
    fruit_emoji = random.choice(FRUIT_EMOJIS)
    eaten_fruit_popup = {
        "active": False,
        "text": "",
        "start_time": 0,
        "duration": 950,
        "color": (255, 225, 120),
    }

    # Load and blur background image using Pillow
    bg = load_blurred_background('background.jpg', 10)

    # Create a semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))

    font = pygame.font.SysFont('arial', 48, bold=True)
    game_font = pygame.font.SysFont('arial', 36, bold=True)
    emoji_font = pygame.font.SysFont('segoe ui emoji', 44)

    game_state = "home"
    game_over_start_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 70, 280, 70)
    game_over_back_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 165, 280, 70)
    pause_button_rect = pygame.Rect(WIDTH - 200, 18, 170, 56)
    paused_resume_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 90, 280, 70)
    paused_back_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 185, 280, 70)
    game_over_scales = {'start': 1.0, 'back': 1.0}
    pause_button_scale = 1.0
    paused_scales = {'resume': 1.0, 'back': 1.0}
    scale_speed = 0.14
    max_scale = 1.12
    min_scale = 1.0
    move_interval_ms = DIFFICULTY_SPEEDS["medium"]
    move_accumulator = 0
    previous_time = pygame.time.get_ticks()

    def reset_game():
        nonlocal snake, direction, next_direction, food, score, fruit_emoji, move_accumulator, eaten_fruit_popup
        center_x = (WIDTH // 2 // CELL_SIZE) * CELL_SIZE
        center_y = (HEIGHT // 2 // CELL_SIZE) * CELL_SIZE
        snake = [
            (center_x, center_y),
            (center_x - CELL_SIZE, center_y),
            (center_x - 2 * CELL_SIZE, center_y),
        ]
        direction = RIGHT
        next_direction = RIGHT
        food = random_food_position(snake)
        fruit_emoji = random.choice(FRUIT_EMOJIS)
        score = 0
        move_accumulator = 0
        eaten_fruit_popup["active"] = False

    welcome_screen(screen)

    while True:
        now = pygame.time.get_ticks()
        dt = now - previous_time
        previous_time = now
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_state == "playing" and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w) and direction != DOWN:
                    next_direction = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s) and direction != UP:
                    next_direction = DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a) and direction != RIGHT:
                    next_direction = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and direction != LEFT:
                    next_direction = RIGHT
                elif event.key == pygame.K_p:
                    game_state = "paused"

            elif game_state == "paused" and event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                game_state = "playing"
                previous_time = pygame.time.get_ticks()

            if game_state in ("playing", "paused") and event.type == pygame.MOUSEBUTTONDOWN:
                if pause_button_rect.collidepoint(mouse_pos):
                    if game_state == "playing":
                        game_state = "paused"
                    else:
                        game_state = "playing"
                        previous_time = pygame.time.get_ticks()
                elif game_state == "paused" and paused_resume_rect.collidepoint(mouse_pos):
                    game_state = "playing"
                    previous_time = pygame.time.get_ticks()
                elif game_state == "paused" and paused_back_rect.collidepoint(mouse_pos):
                    game_state = "home"
                    previous_time = pygame.time.get_ticks()

            if game_state == "game_over" and event.type == pygame.MOUSEBUTTONDOWN:
                if game_over_start_rect.collidepoint(mouse_pos):
                    reset_game()
                    game_state = "playing"
                elif game_over_back_rect.collidepoint(mouse_pos):
                    game_state = "home"

        if game_state == "home":
            action = start_screen(screen, font, high_score)
            if action == 'exit':
                pygame.quit()
                sys.exit()
            elif action == 'about':
                about_screen(screen, font)
            elif action == 'high_score':
                high_score_screen(screen, font, high_score)
            elif action == 'contact':
                contact_screen(screen, font)
            elif action == 'start':
                difficulty = difficulty_screen(screen, font)
                if difficulty is not None:
                    move_interval_ms = DIFFICULTY_SPEEDS[difficulty]
                    reset_game()
                    game_state = "playing"
            previous_time = pygame.time.get_ticks()
            continue

        if game_state == "playing":
            move_accumulator += dt
            while move_accumulator >= move_interval_ms:
                move_accumulator -= move_interval_ms
                direction = next_direction
                head_x, head_y = snake[0]
                dx, dy = direction
                new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)

                hit_boundary = (
                    new_head[0] < 0 or new_head[0] >= WIDTH or
                    new_head[1] < 0 or new_head[1] >= HEIGHT
                )
                hit_self = new_head in snake

                if hit_boundary or hit_self:
                    # Persist score immediately on collision before switching screen.
                    if score > high_score:
                        high_score = score
                        with open(highscore_file, 'w') as f:
                            f.write(str(high_score))

                    scores_file = 'scores.txt'
                    scores = []
                    if os.path.exists(scores_file):
                        with open(scores_file, 'r') as f:
                            for line in f:
                                try:
                                    scores.append(int(line.strip()))
                                except ValueError:
                                    continue
                    scores.append(score)
                    scores = scores[-10:]
                    with open(scores_file, 'w') as f:
                        for s in scores:
                            f.write(str(s) + '\n')

                    game_state = "game_over"
                    break

                snake.insert(0, new_head)
                if new_head == food:
                    score += 1
                    eaten_fruit_popup["active"] = True
                    eaten_fruit_popup["text"] = FRUIT_NAMES.get(fruit_emoji, "Fruit")
                    eaten_fruit_popup["start_time"] = now
                    food = random_food_position(snake)
                    fruit_emoji = random.choice(FRUIT_EMOJIS)
                else:
                    snake.pop()

            draw_gameplay(
                screen, bg, overlay, snake, food, fruit_emoji, score, high_score,
                game_font, emoji_font, now, eaten_fruit_popup
            )
            pause_label = 'Pause'
            hovered_pause, _ = draw_button(
                screen, pause_button_rect, pause_label, game_font,
                base_color=(255, 255, 255),
                hover_color=(130, 220, 255),
                border_color=(128, 128, 128),
                text_color=(0, 0, 0),
                mouse_pos=mouse_pos,
                scale=pause_button_scale,
                glow=True,
                glow_color=(180, 220, 255),
                border_radius=24
            )
            if hovered_pause:
                pause_button_scale += (max_scale - pause_button_scale) * scale_speed
            else:
                pause_button_scale += (min_scale - pause_button_scale) * scale_speed
            pygame.display.flip()
            clock.tick(60)
            continue

        if game_state == "paused":
            draw_gameplay(
                screen, bg, overlay, snake, food, fruit_emoji, score, high_score,
                game_font, emoji_font, now, eaten_fruit_popup
            )

            pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 145))
            screen.blit(pause_overlay, (0, 0))
            pause_text = font.render("Paused", True, WHITE)
            help_text = game_font.render("Press P or use buttons below", True, (220, 220, 220))
            screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            screen.blit(help_text, help_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 42)))

            hovered_resume, _ = draw_button(
                screen, paused_resume_rect, 'Resume', game_font,
                base_color=(255, 255, 255),
                hover_color=(130, 220, 255),
                border_color=(128, 128, 128),
                text_color=(0, 0, 0),
                mouse_pos=mouse_pos,
                scale=paused_scales['resume'],
                glow=True,
                glow_color=(180, 220, 255),
                border_radius=26
            )
            hovered_back_pause, _ = draw_button(
                screen, paused_back_rect, 'Back', game_font,
                base_color=(255, 255, 255),
                hover_color=(130, 220, 255),
                border_color=(128, 128, 128),
                text_color=(0, 0, 0),
                mouse_pos=mouse_pos,
                scale=paused_scales['back'],
                glow=True,
                glow_color=(180, 220, 255),
                border_radius=26
            )

            if hovered_resume:
                paused_scales['resume'] += (max_scale - paused_scales['resume']) * scale_speed
            else:
                paused_scales['resume'] += (min_scale - paused_scales['resume']) * scale_speed

            if hovered_back_pause:
                paused_scales['back'] += (max_scale - paused_scales['back']) * scale_speed
            else:
                paused_scales['back'] += (min_scale - paused_scales['back']) * scale_speed

            pygame.display.flip()
            clock.tick(60)
            continue

        # game_over screen
        draw_gameplay(
            screen, bg, overlay, snake, food, fruit_emoji, score, high_score,
            game_font, emoji_font, now, eaten_fruit_popup
        )
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))

        panel_rect = pygame.Rect(WIDTH // 2 - 270, HEIGHT // 2 - 190, 540, 430)
        pygame.draw.rect(screen, PANEL, panel_rect, border_radius=22)
        pygame.draw.rect(screen, (130, 170, 255), panel_rect, width=3, border_radius=22)

        game_over_title = font.render("Game Over", True, RED)
        title_rect = game_over_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
        screen.blit(game_over_title, title_rect)

        score_text = game_font.render(f"Score: {score}", True, WHITE)
        high_text = game_font.render(f"Best: {high_score}", True, (255, 215, 0))
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 45)))
        screen.blit(high_text, high_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 5)))

        hovered_start, _ = draw_button(
            screen, game_over_start_rect, 'Start', game_font,
            base_color=(255, 255, 255),
            hover_color=(130, 220, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=game_over_scales['start'],
            glow=True,
            glow_color=(180, 220, 255),
            border_radius=26
        )
        hovered_back, _ = draw_button(
            screen, game_over_back_rect, 'Back', game_font,
            base_color=(255, 255, 255),
            hover_color=(130, 220, 255),
            border_color=(128, 128, 128),
            text_color=(0, 0, 0),
            mouse_pos=mouse_pos,
            scale=game_over_scales['back'],
            glow=True,
            glow_color=(180, 220, 255),
            border_radius=26
        )

        if hovered_start:
            game_over_scales['start'] += (max_scale - game_over_scales['start']) * scale_speed
        else:
            game_over_scales['start'] += (min_scale - game_over_scales['start']) * scale_speed

        if hovered_back:
            game_over_scales['back'] += (max_scale - game_over_scales['back']) * scale_speed
        else:
            game_over_scales['back'] += (min_scale - game_over_scales['back']) * scale_speed

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main() 