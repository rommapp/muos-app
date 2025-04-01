# trunk-ignore-all(ruff/E402)

import ctypes
import os
import sys

# Add the PIL and dotenv dependencies to the path
base_path = os.path.dirname(os.path.abspath(__file__))
libs_path = os.path.join(base_path, "deps")
sys.path.insert(0, libs_path)

import sdl2
import sdl2.ext
from dotenv import load_dotenv

# Load .env file from one folder above
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.stdout = open(os.environ.get("LOG_FILE", "./logs/log.txt"), "w", buffering=1)


def main():
    from romm import RomM
    from ui import UserInterface

    # Initialize SDL2 with video and joystick support
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK) < 0:
        print(f"SDL2 initialization failed: {sdl2.SDL_GetError()}")
        sys.exit(1)
    sdl2.SDL_GameControllerEventState(sdl2.SDL_ENABLE)

    # Create a fullscreen window
    window = sdl2.SDL_CreateWindow(
        "RomM".encode("utf-8"),
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        sdl2.SDL_WINDOWPOS_UNDEFINED,
        0,
        0,  # Size ignored in fullscreen mode
        sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP | sdl2.SDL_WINDOW_SHOWN,
    )
    if not window:
        print(f"Failed to create window: {sdl2.SDL_GetError()}")
        sys.exit(1)

    renderer = sdl2.SDL_CreateRenderer(window, -1, sdl2.SDL_RENDERER_ACCELERATED)
    if not renderer:
        print(f"Failed to create renderer: {sdl2.SDL_GetError()}")
        sys.exit(1)

    # Fixed base resolution for UI rendering
    base_width = 640
    base_height = 480

    ui = UserInterface()
    # Ensure UI uses fixed base resolution
    ui.screen_width = base_width
    ui.screen_height = base_height
    romm = RomM()
    romm.start()

    while romm.running:
        # Render directly to the screen
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        ui.draw_start()  # Render at 640x480
        romm.update()  # Draw content

        # Convert PIL image to SDL2 texture at base resolution
        image = ui.get_image()
        rgba_data = image.tobytes()
        surface = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            rgba_data,
            base_width,
            base_height,
            32,
            base_width * 4,
            sdl2.SDL_PIXELFORMAT_RGBA32,
        )
        texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
        sdl2.SDL_FreeSurface(surface)

        # Get current window size for scaling
        window_width = ctypes.c_int()
        window_height = ctypes.c_int()
        sdl2.SDL_GetWindowSize(
            window, ctypes.byref(window_width), ctypes.byref(window_height)
        )
        window_width, window_height = window_width.value, window_height.value

        # Calculate scaling to fit fullscreen while preserving 4:3 aspect ratio
        scale = min(window_width / base_width, window_height / base_height)
        dst_width = int(base_width * scale)
        dst_height = int(base_height * scale)
        dst_x = (window_width - dst_width) // 2
        dst_y = (window_height - dst_height) // 2
        dst_rect = sdl2.SDL_Rect(dst_x, dst_y, dst_width, dst_height)

        sdl2.SDL_RenderCopy(renderer, texture, None, dst_rect)
        sdl2.SDL_RenderPresent(renderer)
        sdl2.SDL_DestroyTexture(texture)

        # Add a small sleep to prevent 100% CPU usage
        sdl2.SDL_Delay(16)

    # Cleanup
    print("Exiting...")
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    sys.stdout.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
