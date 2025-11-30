# Importar todas las librerías necesarias
import pygame
import os
import math
import time
from pygame import mixer
import tkinter as tk
from tkinter import filedialog

# Inicializar todos los módulos de pygame
pygame.init()
mixer.init() 

# Configurar la ventana principal
WIDTH, HEIGHT = 900, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reproductor de Música")

# --- Paleta de Colores y Fuentes (AJUSTADA PARA 3D) ---
BACKGROUND = (25, 20, 35)      # Color de fondo principal (azul oscuro)
PRIMARY = (118, 75, 162)       # Color primario (púrpura)
SECONDARY = (58, 175, 169)     # Color secundario (verde azulado)
ACCENT = (239, 71, 111)        # Color de acento (rosa)
TEXT_COLOR = (240, 240, 250)   # Color del texto (blanco grisáceo)

# Colores Base para Botones 3D
BUTTON_BASE = (70, 45, 120)    # Color base del botón (Púrpura Oscuro)
BUTTON_HIGHLIGHT = (100, 75, 150) # Color de la luz (borde superior e izquierdo)
BUTTON_SHADOW = (40, 25, 65)   # Color de la sombra (borde inferior y derecho)
BUTTON_ACTIVE = (50, 30, 80)   # Color cuando el botón está presionado

# Configurar diferentes tamaños de fuentes
font_small = pygame.font.SysFont("sans-serif", 16)
font_medium = pygame.font.SysFont("sans-serif", 20)
font_large = pygame.font.SysFont("sans-serif", 32, bold=True)

# --- Variables de estado del reproductor ---
songs = []
current_song_index = 0
paused = False
music_playing = False
volume = 1.0
current_time = 0
song_length = 1

# --- Variables para el scroll de la playlist ---
playlist_scroll_offset = 0
MAX_PLAYLIST_ITEMS = 4
is_dragging_volume = False # Nuevo: Indica si el control de volumen está siendo arrastrado

# --- Definir áreas rectangulares (Rects) para los botones ---

# Botón "Cargar Canciones"
load_button_rect = pygame.Rect(20, 20, 180, 40)

# Configuración para botones de control (play, pause, next, prev)
button_size = 60
button_spacing = 20
total_controls_width = (button_size * 3) + (button_spacing * 2)
controls_start_x = (WIDTH - total_controls_width) / 2
controls_y = 350

# Crear rectángulos para los botones de control
prev_button_rect = pygame.Rect(controls_start_x, controls_y, button_size, button_size)
play_pause_button_rect = pygame.Rect(controls_start_x + button_size + button_spacing, controls_y, button_size, button_size)
next_button_rect = pygame.Rect(controls_start_x + (button_size + button_spacing) * 2, controls_y, button_size, button_size)

# Área de la playlist para detectar el scroll del mouse
playlist_area = pygame.Rect(50, 480, WIDTH - 100, 120)

# --- FIN DE AJUSTES DE VARIABLES DE CONFIGURACIÓN ---

def load_songs():
    """ Abre un diálogo para que el usuario seleccione archivos de audio """
    global songs, current_song_index, playlist_scroll_offset
    
    root = tk.Tk()
    root.withdraw()
    
    file_paths = filedialog.askopenfilenames(
        title="Selecciona tus canciones",
        filetypes=(("Archivos de Audio", "*.mp3 *.wav *.ogg *.flac"), ("Todos los archivos", "*.*"))
    )
    
    if not file_paths:
        return False

    songs = []
    
    for path in file_paths:
        file_name = os.path.basename(path)
        songs.append({
            "title": os.path.splitext(file_name)[0],
            "artist": "Artista Desconocido",
            "file": path,
            "length": 0
        })
    
    root.destroy()
    
    current_song_index = 0
    playlist_scroll_offset = 0 
    
    return len(songs) > 0

def ensure_song_is_visible(index):
    """ Ajusta el scroll para que la canción en el índice dado sea visible """
    global playlist_scroll_offset
    
    if index < playlist_scroll_offset:
        playlist_scroll_offset = index
    elif index >= playlist_scroll_offset + MAX_PLAYLIST_ITEMS:
        playlist_scroll_offset = index - MAX_PLAYLIST_ITEMS + 1

def load_and_play_song(index):
    """ Carga y reproduce la canción en el índice especificado """
    global music_playing, paused, current_time, song_length, current_song_index
    
    if 0 <= index < len(songs):
        current_song_index = index
        ensure_song_is_visible(index)
        
        try:
            mixer.music.load(songs[index]["file"])
            mixer.music.play()
            mixer.music.set_volume(volume)
            
            sound = mixer.Sound(songs[index]["file"])
            song_length = sound.get_length()
            songs[index]["length"] = song_length
            
            music_playing = True
            paused = False
            current_time = 0
            return True
            
        except Exception as e:
            print(f"Error al cargar la canción: {e}")
            return False
    return False

def format_time(seconds):
    """ Convierte segundos a formato minutos:segundos (MM:SS) """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

# --- NUEVA FUNCIÓN PARA EL BOTÓN 3D ---
def draw_3d_button(surface, rect, text_label, is_hovering, is_pressed=False):
    """
    Dibuja un botón rectangular con efecto 3D/relieve.
    """
    relief = 4
    
    # 1. Definir los colores basados en el estado
    base_color = BUTTON_ACTIVE if is_pressed else BUTTON_BASE
    light_color = BUTTON_SHADOW if is_pressed else BUTTON_HIGHLIGHT
    shadow_color = BUTTON_HIGHLIGHT if is_pressed else BUTTON_SHADOW
    
    # 2. Dibujar la sombra (borde inferior y derecho)
    pygame.draw.rect(surface, shadow_color, (rect.x + relief, rect.y + relief, rect.width, rect.height), border_radius=5)
    
    # 3. Dibujar la luz (borde superior e izquierdo)
    if not is_pressed:
        pygame.draw.rect(surface, light_color, (rect.x, rect.y, rect.width - relief, rect.height - relief), border_radius=5)
    
    # 4. Dibujar el cuerpo principal
    body_x = rect.x + relief if is_pressed else rect.x
    body_y = rect.y + relief if is_pressed else rect.y
    body_rect = pygame.Rect(body_x, body_y, rect.width - relief, rect.height - relief)
    pygame.draw.rect(surface, base_color, body_rect, border_radius=5)
    
    # 5. Dibujar el texto
    text_surface = font_medium.render(text_label, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=body_rect.center)
    surface.blit(text_surface, text_rect)
# --- FIN DE draw_3d_button ---

def draw_window():
    """ Función principal que dibuja todos los elementos en la ventana """
    window.fill(BACKGROUND)
    
    draw_visualization()
    draw_album_art_placeholder()
    draw_song_info()
    draw_controls()
    draw_progress_bar()
    draw_volume_control()
    draw_playlist()
    draw_scrollbar()
    
    pygame.display.update()

def draw_visualization():
    """ Dibuja efectos visuales que reaccionan al audio (ondas de sonido) """
    bar_width = 8
    num_bars = WIDTH // bar_width
    
    for i in range(num_bars):
        amplitude = 50 * volume + 25
        frequency = 0.05
        movement = math.sin(time.time() * 2 + i * frequency) * amplitude
        height = 5 + abs(movement)
        
        if not music_playing or paused:
            height = 5
            
        x = i * bar_width
        
        color_factor = abs(movement) / amplitude
        color = (
            int(PRIMARY[0] * (1 - color_factor) + ACCENT[0] * color_factor),
            int(PRIMARY[1] * (1 - color_factor) + ACCENT[1] * color_factor),
            int(PRIMARY[2] * (1 - color_factor) + ACCENT[2] * color_factor)
        )
        
        pygame.draw.rect(window, color, (x, 150 - height, bar_width - 2, height * 2))

def draw_album_art_placeholder():
    """ Dibuja un placeholder para la portada del álbum """
    album_art_size = 180
    x = (WIDTH - album_art_size) / 2
    y = 170
    
    rect = pygame.Rect(x, y, album_art_size, album_art_size)
    pygame.draw.rect(window, BUTTON_BASE, rect, border_radius=15)
    
    note_font = pygame.font.SysFont("arial", 100)
    note_text = note_font.render("♪", True, BACKGROUND)
    text_rect = note_text.get_rect(center=rect.center)
    window.blit(note_text, text_rect)

def draw_song_info():
    """ Dibuja el título y artista de la canción actual """
    if songs:
        song = songs[current_song_index]
        
        title = font_large.render(song["title"], True, TEXT_COLOR)
        artist = font_medium.render(song["artist"], True, SECONDARY)
        
        window.blit(title, (WIDTH / 2 - title.get_width() / 2, 20))
        window.blit(artist, (WIDTH / 2 - artist.get_width() / 2, 65))

def draw_controls():
    """ Dibuja todos los botones de control (cargar, play/pause, next, prev) """
    mouse_pos = pygame.mouse.get_pos()
    
    # --- Botón "Cargar Canciones" (USANDO FUNCIÓN 3D) ---
    is_pressed = load_button_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]
    draw_3d_button(window, load_button_rect, "Cargar Canciones", load_button_rect.collidepoint(mouse_pos), is_pressed)
    
    # --- Botón "Anterior" ---
    color = BUTTON_HIGHLIGHT if prev_button_rect.collidepoint(mouse_pos) else BUTTON_BASE
    pygame.draw.circle(window, color, prev_button_rect.center, button_size // 2)
    
    pygame.draw.polygon(window, TEXT_COLOR, [
        (prev_button_rect.centerx - 5, prev_button_rect.centery),
        (prev_button_rect.centerx + 10, prev_button_rect.centery - 12),
        (prev_button_rect.centerx + 10, prev_button_rect.centery + 12)
    ])
    pygame.draw.line(window, TEXT_COLOR, 
                     (prev_button_rect.centerx - 12, prev_button_rect.centery - 12), 
                     (prev_button_rect.centerx - 12, prev_button_rect.centery + 12), 3)
    
    # --- Botón "Play/Pause" ---
    is_active = play_pause_button_rect.collidepoint(mouse_pos) or music_playing
    color = ACCENT if is_active else BUTTON_BASE
    pygame.draw.circle(window, color, play_pause_button_rect.center, button_size // 2)
    
    if paused or not music_playing:
        pygame.draw.polygon(window, TEXT_COLOR, [
            (play_pause_button_rect.centerx - 10, play_pause_button_rect.centery - 15),
            (play_pause_button_rect.centerx - 10, play_pause_button_rect.centery + 15),
            (play_pause_button_rect.centerx + 15, play_pause_button_rect.centery)
        ])
    else:
        pygame.draw.rect(window, TEXT_COLOR, 
                         (play_pause_button_rect.centerx - 12, play_pause_button_rect.centery - 12, 8, 24))
        pygame.draw.rect(window, TEXT_COLOR, 
                         (play_pause_button_rect.centerx + 4, play_pause_button_rect.centery - 12, 8, 24))
    
    # --- Botón "Siguiente" ---
    color = BUTTON_HIGHLIGHT if next_button_rect.collidepoint(mouse_pos) else BUTTON_BASE
    pygame.draw.circle(window, color, next_button_rect.center, button_size // 2)
    
    pygame.draw.polygon(window, TEXT_COLOR, [
        (next_button_rect.centerx + 5, next_button_rect.centery),
        (next_button_rect.centerx - 10, next_button_rect.centery - 12),
        (next_button_rect.centerx - 10, next_button_rect.centery + 12)
    ])
    pygame.draw.line(window, TEXT_COLOR, 
                     (next_button_rect.centerx + 12, next_button_rect.centery - 12), 
                     (next_button_rect.centerx + 12, next_button_rect.centery + 12), 3)

def draw_progress_bar():
    """ Dibuja la barra de progreso de la canción actual """
    global current_time
    
    bar_y = 440
    bar_start_x = 50
    bar_width = WIDTH - 100
    
    if music_playing and not paused:
        current_time = mixer.music.get_pos() / 1000.0
    
    progress_ratio = current_time / song_length if song_length > 0 else 0
    progress_px = bar_width * progress_ratio
    
    pygame.draw.rect(window, (60, 60, 70), (bar_start_x, bar_y, bar_width, 8), border_radius=4)
    pygame.draw.rect(window, PRIMARY, (bar_start_x, bar_y, progress_px, 8), border_radius=4)
    pygame.draw.circle(window, ACCENT, (int(bar_start_x + progress_px), bar_y + 4), 10)
    
    current_text = font_small.render(format_time(current_time), True, TEXT_COLOR)
    total_text = font_small.render(format_time(song_length), True, TEXT_COLOR)
    window.blit(current_text, (bar_start_x, bar_y + 15))
    window.blit(total_text, (bar_start_x + bar_width - total_text.get_width(), bar_y + 15))

def draw_volume_control():
    """ Dibuja el control deslizante de volumen (Posición Ajustada) """
    # COORDENADAS AJUSTADAS PARA ALEJARLO DE LA PLAYLIST
    bar_y = 85 
    bar_width = 100 
    bar_x = WIDTH - 120 

    pygame.draw.rect(window, (60, 60, 70), (bar_x, bar_y, bar_width, 6), border_radius=3)
    pygame.draw.rect(window, SECONDARY, (bar_x, bar_y, volume * bar_width, 6), border_radius=3)
    
    volume_thumb_pos = (bar_x + volume * bar_width, bar_y + 3)
    pygame.draw.circle(window, TEXT_COLOR, (int(volume_thumb_pos[0]), int(volume_thumb_pos[1])), 8)
    
    volume_text = font_small.render("Volumen", True, TEXT_COLOR)
    window.blit(volume_text, (bar_x, bar_y - 20))

def draw_playlist():
    """ Dibuja la lista de reproducción con scroll """
    if not songs:
        no_songs = font_medium.render("Haz clic en 'Cargar Canciones' para empezar", True, TEXT_COLOR)
        window.blit(no_songs, (WIDTH/2 - no_songs.get_width()/2, 500))
        return

    playlist_title = font_medium.render("Lista de Reproducción:", True, SECONDARY)
    window.blit(playlist_title, (50, 480))
    
    start_idx = playlist_scroll_offset
    end_idx = min(len(songs), start_idx + MAX_PLAYLIST_ITEMS)
    
    for i in range(start_idx, end_idx):
        y_pos = 510 + (i - start_idx) * 25
        
        is_current = (i == current_song_index)
        color = ACCENT if is_current else TEXT_COLOR
        
        prefix = "▶ " if is_current else "   "
        song_text_str = f'{prefix}{i+1}. {songs[i]["title"]}'
        song_text = font_small.render(song_text_str, True, color)
        window.blit(song_text, (50, y_pos))

def draw_scrollbar():
    """ Dibuja la barra de scroll para la playlist """
    if len(songs) <= MAX_PLAYLIST_ITEMS:
        return 

    scrollbar_x = WIDTH - 60
    playlist_y_start = 510
    playlist_height = MAX_PLAYLIST_ITEMS * 25
    scrollbar_height = playlist_height - 10

    pygame.draw.rect(window, (60, 60, 70), (scrollbar_x, playlist_y_start, 8, scrollbar_height), border_radius=4)
    
    thumb_height = max(20, (MAX_PLAYLIST_ITEMS / len(songs)) * scrollbar_height)
    scrollable_range = len(songs) - MAX_PLAYLIST_ITEMS
    scroll_ratio = playlist_scroll_offset / scrollable_range if scrollable_range > 0 else 0
    thumb_y = playlist_y_start + scroll_ratio * (scrollbar_height - thumb_height)
    
    pygame.draw.rect(window, SECONDARY, (scrollbar_x, thumb_y, 8, thumb_height), border_radius=4)


def handle_drag(pos):
    """ Maneja el arrastre del mouse (MOUSEMOTION) para el control de volumen. """
    global volume, is_dragging_volume
    
    bar_y = 85 
    bar_width = 100
    bar_x = WIDTH - 120 

    if is_dragging_volume:
        new_volume_x = pos[0]
        
        volume = (new_volume_x - bar_x) / bar_width
        volume = max(0, min(1, volume))
        
        mixer.music.set_volume(volume)

def handle_click(pos):
    """ Maneja todos los clics del mouse en la interfaz (MOUSEBUTTONDOWN) """
    global paused, volume, songs, is_dragging_volume

    if load_button_rect.collidepoint(pos):
        if load_songs():
            load_and_play_song(0)
            
    elif play_pause_button_rect.collidepoint(pos):
        if music_playing:
            if paused:
                mixer.music.unpause()
                paused = False
            else:
                mixer.music.pause()
                paused = True
        elif songs:
            load_and_play_song(current_song_index)
            
    elif prev_button_rect.collidepoint(pos) and songs:
        next_index = (current_song_index - 1) % len(songs)
        load_and_play_song(next_index)
        
    elif next_button_rect.collidepoint(pos) and songs:
        next_index = (current_song_index + 1) % len(songs)
        load_and_play_song(next_index)
        
    elif 50 <= pos[0] <= WIDTH - 50 and 435 <= pos[1] <= 445 and music_playing:
        progress_ratio = (pos[0] - 50) / (WIDTH - 100)
        seek_time = song_length * progress_ratio
        mixer.music.play(start=seek_time)
        global current_time
        current_time = seek_time
        if paused:
            mixer.music.pause()
            
    # --- Detección de clic inicial para ARRASTRE DE VOLUMEN ---
    bar_x = WIDTH - 120
    bar_width = 100
    bar_y = 85
    
    if bar_x <= pos[0] <= bar_x + bar_width and bar_y - 10 <= pos[1] <= bar_y + 10:
        is_dragging_volume = True
        handle_drag(pos) # Aplica volumen inmediatamente al hacer clic
            
    # --- Clic en la Playlist (seleccionar canción) ---
    elif playlist_area.collidepoint(pos) and songs:
        # 510 es la posición Y de la primera línea de texto de la lista
        clicked_index = playlist_scroll_offset + (pos[1] - 510) // 25 
        if 0 <= clicked_index < len(songs):
            load_and_play_song(clicked_index)

def main():
    """ Función principal del programa - Bucle principal del reproductor """
    global playlist_scroll_offset, is_dragging_volume
    clock = pygame.time.Clock()
    running = True
    
    SONG_END = pygame.USEREVENT + 1
    mixer.music.set_endevent(SONG_END)
    
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == SONG_END and songs:
                next_index = (current_song_index + 1) % len(songs)
                load_and_play_song(next_index)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    handle_click(event.pos)
                    
            # Fin del arrastre de volumen
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_dragging_volume = False
                    
            # Arrastre de volumen activo
            elif event.type == pygame.MOUSEMOTION:
                if is_dragging_volume:
                    handle_drag(event.pos)
            
            # Scroll de la playlist
            elif event.type == pygame.MOUSEWHEEL:
                if playlist_area.collidepoint(pygame.mouse.get_pos()) and songs:
                    playlist_scroll_offset -= event.y
                    
                    max_scroll = max(0, len(songs) - MAX_PLAYLIST_ITEMS)
                    playlist_scroll_offset = max(0, min(playlist_scroll_offset, max_scroll))

        draw_window()
    
    pygame.quit()
    mixer.quit()

if __name__ == "__main__":
    main()