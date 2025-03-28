import os
import time
import sys
import shutil
from typing import Optional, Tuple, List, Dict, Any

# Redirect stdout to log file
sys.stdout = open('log.txt', 'w', buffering=1)

# Add the PIL and dotenv dependencies to the path
base_path = os.path.dirname(os.path.abspath(__file__))

# Add the PIL and dotenv dependencies to the path
base_path = os.path.dirname(os.path.abspath(__file__))
libs_path = os.path.join(base_path, "deps")
sys.path.insert(0, libs_path)
    
from PIL import Image, ImageDraw, ImageFont
import sdl2
import sdl2.ext
import sdl2.sdlimage
    
from filesystem import Filesystem
from glyps import glyphs
from status import Status

screen_width = 0 
screen_height = 0 
bytes_per_pixel = 4
screen_size = 0

fontFile = {}
fontFile[15] = ImageFont.truetype(os.path.join(os.getcwd(), "fonts/romm.ttf"), 16)

colorViolet = "#ad3c6b"
colorGreen = "#41aa3b"
colorDarkGreen = "#3d6b39"
colorRed = "#3c3cad"
colorBlue = "#bb7200"
colorYellow = "#3b80aa"
colorGrayL1 = "#383838"
colorGrayD2 = "#141414"

activeImage: Image.Image
activeDraw: ImageDraw.ImageDraw

fs = Filesystem()
status = Status()
backend = None

def query_display():
    """Query the display resolution using SDL2."""
    global screen_width, screen_height, screen_size
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) < 0:
        print(f"SDL2 init failed for display query: {sdl2.SDL_GetError()}")
        screen_width, screen_height = 640, 480  # Fallback
    else:
        display_index = 0  # Use primary display
        rect = sdl2.SDL_Rect()
        if sdl2.SDL_GetDisplayBounds(display_index, rect) == 0:
            screen_width = rect.w
            screen_height = rect.h
        else:
            print(f"Failed to get display bounds: {sdl2.SDL_GetError()}")
            screen_width, screen_height = 640, 480  # Fallback
        sdl2.SDL_Quit()  # Clean up init for now; draw_start will re-init
    screen_size = screen_width * screen_height * bytes_per_pixel

def screen_reset():
    if backend and backend.renderer:
        sdl2.SDL_RenderClear(backend.renderer)
        sdl2.SDL_RenderPresent(backend.renderer)

def draw_start():
    global backend
    backend = SDL2Backend(screen_width, screen_height)
    backend.start()

def draw_end():
    global backend
    if backend:
        backend.end()

def crate_image():
    return Image.new("RGBA", (screen_width, screen_height), color="black")

def draw_active(image):
    global activeImage, activeDraw
    activeImage = image
    activeDraw = ImageDraw.Draw(activeImage)

def draw_update():
    global backend, activeImage
    if backend and activeImage:
        rgba_data = activeImage.tobytes()
        surface = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            rgba_data, screen_width, screen_height, 32, screen_width * 4,
            sdl2.SDL_PIXELFORMAT_RGBA32
        )
        if not surface:
            print(f"Surface creation failed: {sdl2.SDL_GetError()}")
            return
        texture = sdl2.SDL_CreateTextureFromSurface(backend.renderer, surface)
        sdl2.SDL_FreeSurface(surface)
        if not texture:
            print(f"Texture creation failed: {sdl2.SDL_GetError()}")
            return
        sdl2.SDL_RenderClear(backend.renderer)
        sdl2.SDL_RenderCopy(backend.renderer, texture, None, None)
        sdl2.SDL_RenderPresent(backend.renderer)
        sdl2.SDL_DestroyTexture(texture)

def draw_clear():
    activeDraw.rectangle([0, 0, screen_width, screen_height], fill="black")

def draw_text(position, text, font=15, color="white", **kwargs):
    activeDraw.text(position, text, font=fontFile[font], fill=color, **kwargs)

def draw_rectangle(position, fill=None, outline=None, width=1):
    activeDraw.rectangle(position, fill=fill, outline=outline, width=width)

def draw_rectangle_r(position, radius, fill=None, outline=None):
    activeDraw.rounded_rectangle(position, radius, fill=fill, outline=outline)

def row_list(
    text,
    pos,
    width,
    height,
    selected,
    fill=colorViolet,
    outline=None,
    append_icon_path=None,
):
    try:
        icon = Image.open(append_icon_path) if append_icon_path else None
    except (FileNotFoundError, AttributeError):
        icon = None
    radius = 5
    margin_left_text = 12 + (35 if icon else 0)
    margin_top_text = 8
    draw_rectangle_r(
        [pos[0], pos[1], pos[0] + width, pos[1] + height],
        radius,
        fill=(fill if selected else colorGrayL1),
        outline=outline,
    )
    if icon:
        margin_left_icon = 10
        margin_top_icon = 5
        activeImage.paste(
            icon,
            (pos[0] + margin_left_icon, pos[1] + margin_top_icon),
            mask=icon if icon.mode == "RGBA" else None,
        )
    draw_text((pos[0] + margin_left_text, pos[1] + margin_top_text), text)

def draw_circle(position, radius, fill=None, outline="white"):
    activeDraw.ellipse(
        [
            position[0] - radius,
            position[1] - radius,
            position[0] + radius,
            position[1] + radius,
        ],
        fill=fill,
        outline=outline,
    )

def button_circle(pos, button, text, color=colorViolet):
    radius = 10
    btn_text_offset = 1
    label_margin_l = 20
    draw_circle(pos, radius, fill=color, outline=None)
    draw_text((pos[0] + btn_text_offset, pos[1] + btn_text_offset), button, anchor="mm")
    draw_text(
        (pos[0] + label_margin_l, pos[1] + btn_text_offset), text, font=15, anchor="lm"
    )

def draw_log(
    text_line_1="",
    text_line_2="",
    fill="black",
    outline="black",
    text_color="white",
    background=True,
):
    margin_bg = 5
    margin_bg_bottom = 40
    radius_bg = 5
    max_len_text = 65
    margin_left_text = 15
    margin_text_bottom = 28
    margin_text_bottom_multiline_line_1 = 38
    margin_text_bottom_multiline_line_2 = 21
    if background:
        draw_rectangle_r(
            [
                margin_bg,
                screen_height - margin_bg_bottom,
                screen_width - margin_bg,
                screen_height - margin_bg,
            ],
            radius_bg,
            fill=fill,
            outline=outline,
        )
    draw_text(
        (
            margin_left_text,
            (
                screen_height - margin_text_bottom
                if not text_line_2
                else screen_height - margin_text_bottom_multiline_line_1
            ),
        ),
        (
            text_line_1
            if len(text_line_1) <= max_len_text
            else text_line_1[:max_len_text] + "..."
        ),
        color=text_color,
    )
    if text_line_2:
        draw_text(
            (margin_left_text, screen_height - margin_text_bottom_multiline_line_2),
            (
                text_line_2
                if len(text_line_2) <= max_len_text
                else text_line_2[:max_len_text] + "..."
            ),
            color=text_color,
        )

def draw_loader(percent, color=colorDarkGreen):
    margin = 10
    margin_top = 38
    margin_bottom = 4
    radius = 2
    draw_rectangle_r(
        [
            margin,
            screen_height - margin_top,
            margin + (screen_width - 2 * margin) * (percent / 100),
            screen_height - margin_bottom,
        ],
        radius,
        fill=color,
        outline=None,
    )

def draw_header(host, username):
    username = username if len(username) <= 22 else username[:19] + "..."
    logo = Image.open(os.path.join(os.getcwd(), "resources/romm.png"))
    pos_logo = [15, 7]
    pos_text = [55, 9]
    activeImage.paste(
        logo, (pos_logo[0], pos_logo[1]), mask=logo if logo.mode == "RGBA" else None
    )
    
    roms_path = fs.get_roms_storage_path()
    total, used, free = shutil.disk_usage(roms_path)

    # Convert to GB
    total_gb = total / (1024 ** 3)
    used_gb = used / (1024 ** 3)

    # Calculate percentage
    used_percentage = (used / total) * 100

    draw_text(
        (pos_text[0], pos_text[1]),
        f"{glyphs.host} {host} | {glyphs.user} {username}\n"
        f"{glyphs.microsd} {roms_path} ({used_gb:.1f}/{total_gb:.1f} GB, {used_percentage:.1f}% used)"
    )
    if status.profile_pic_path:
        profile_pic = Image.open(status.profile_pic_path)
        margin_right_profile_pic = 45
        margin_top_profile_pic = 5
        pos_profile_pic = [
            screen_width - margin_right_profile_pic,
            margin_top_profile_pic,
        ]
        activeImage.paste(
            profile_pic,
            (pos_profile_pic[0], pos_profile_pic[1]),
            mask=profile_pic if profile_pic.mode == "RGBA" else None,
        )

def draw_platforms_list(
    platforms_selected_position, max_n_platforms, platforms, fill=colorViolet
):
    draw_rectangle_r([10, 70, screen_width - 10, screen_height - 43], 5, fill=colorGrayD2, outline=None)
    start_idx = int(platforms_selected_position / max_n_platforms) * max_n_platforms
    end_idx = start_idx + max_n_platforms
    for i, p in enumerate(platforms[start_idx:end_idx]):
        is_selected = i == (platforms_selected_position % max_n_platforms)
        row_text = (
            f"{p.display_name} ({p.rom_count})"
            if len(p.display_name) <= 55
            else p.display_name[:55] + f"... ({p.rom_count})"
        )
        row_list(
            row_text,
            (20, 90 + (i * 35)),
            screen_width - 40,
            32,
            is_selected,
            fill=fill,
            append_icon_path=f"{fs.resources_path}/{p.slug}.ico",
        )

def draw_collections_list(
    collections_selected_position, max_n_collections, collections, fill=colorViolet
):
    draw_rectangle_r([10, 75, screen_width - 10, screen_height - 43], 5, fill=colorGrayD2, outline=None)
    start_idx = (
        int(collections_selected_position / max_n_collections) * max_n_collections
    )
    end_idx = start_idx + max_n_collections
    max_len_text = 60
    for i, c in enumerate(collections[start_idx:end_idx]):
        is_selected = i == (collections_selected_position % max_n_collections)
        row_text = c.name
        if len(row_text) > max_len_text:
            row_text = row_text + " "  # add empty space for the rotation
        shift_offset = (int(time.time() * 2)) % len(
            row_text
        )  # Calculate shift offset based on time
        row_text = (
            row_text[shift_offset:] + row_text[:shift_offset]
            if len(row_text) > max_len_text
            else row_text
        )  # Shift text
        row_text = (
            f"{row_text} ({c.rom_count})"
            if len(row_text) <= max_len_text
            else row_text[:max_len_text] + f" ({c.rom_count})"
        )
        row_list(
            row_text,
            (20, 45 + (i * 35)),
            screen_width - 40,
            32,
            is_selected,
            fill=fill,
        )

def draw_roms_list(
    roms_selected_position,
    max_n_roms,
    roms,
    header_text,
    header_color,
    multi_selected_roms,
    prepend_platform_slug=False,
):
    draw_rectangle_r([10, 50, screen_width - 10, 100], 5, outline=colorGrayD2)
    draw_text(
        (screen_width / 2, 60),
        header_text,
        color=header_color,
        anchor="mm",
    )
    draw_rectangle_r([10, 70, screen_width - 10, screen_height - 43], 0, fill=colorGrayD2, outline=None)
    start_idx = int(roms_selected_position / max_n_roms) * max_n_roms
    end_idx = min(start_idx + max_n_roms, len(roms))
    
    # Adjust max text length to reserve space for file size and padding
    padding = 4  # Additional padding in characters
    max_len_text = int((screen_width - 71) / 11) - (4 if prepend_platform_slug else 0) - padding

    for i, r in enumerate(roms[start_idx:end_idx]):
        is_selected = i == (roms_selected_position % max_n_roms)
        is_in_device = fs.is_rom_in_device(r)
        sync_flag_text = f"{glyphs.cloud_sync}" if is_in_device else ""
        
        # Build base row text
        row_text = r.name
        row_text += f" ({','.join(r.languages)})" if r.languages else ""
        row_text += f" ({','.join(r.regions)})" if r.regions else ""
        row_text += f" ({','.join(r.revision)})" if r.revision else ""
        row_text += f" ({','.join(r.tags)})" if r.tags else ""
        
        # Handle text scrolling
        if len(row_text) > max_len_text:
            row_text = row_text + " "
            shift_offset = (int(time.time() * 2)) % len(row_text)
            row_text = row_text[shift_offset:] + row_text[:shift_offset]
        
        # Truncate base text and append file size with padding
        size_text = f"[{r.fs_size[0]}{r.fs_size[1]}] {sync_flag_text}"
        if len(row_text) > max_len_text:
            row_text = row_text[:max_len_text]
        row_text = f"{row_text} {size_text}"
        
        # Add checkbox
        row_text = f"{glyphs.checkbox_selected if r in multi_selected_roms else glyphs.checkbox} {row_text}"
        
        row_list(
            row_text,
            (20, 80 + (i * 35)),
            screen_width - 40,
            32,
            is_selected,
            fill=header_color,
            outline=header_color if r in multi_selected_roms else None,
            append_icon_path=(
                f"{fs.resources_path}/{r.platform_slug}.ico"
                if prepend_platform_slug
                else ""
            ),
        )

def draw_menu_background(
    pos,
    width,
    n_options,
    option_height,
    gap,
    padding,
    extra_top_offset=0,
    extra_bottom_offset=0,
):
    draw_rectangle_r(
        [
            pos[0],
            pos[1] - extra_top_offset,
            pos[0] + width + padding * 2,
            pos[1]
            + n_options * (option_height + gap)
            + padding * 2
            - gap
            + extra_bottom_offset,
        ],
        5,
        fill=colorGrayD2,
        outline=colorViolet,
    )

class SDL2Backend:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.window = None
        self.renderer = None

    def start(self):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) < 0:
            raise RuntimeError(f"SDL2 init failed: {sdl2.SDL_GetError()}")
        self.window = sdl2.SDL_CreateWindow(
            b"Retro UI",
            sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED,
            self.width, self.height,
            sdl2.SDL_WINDOW_SHOWN
        )
        if not self.window:
            raise RuntimeError(f"Window creation failed: {sdl2.SDL_GetError()}")
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
        )
        if not self.renderer:
            raise RuntimeError(f"Renderer creation failed: {sdl2.SDL_GetError()}")
        print("SDL2 backend started")

    def end(self):
        if self.renderer:
            sdl2.SDL_DestroyRenderer(self.renderer)
        if self.window:
            sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()
        print("SDL2 backend closed.")

# Query display and initialize
query_display()
draw_start()
screen_reset()
imgMain = crate_image()
draw_active(imgMain)
