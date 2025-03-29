import os
import sys

# Add the PIL and dotenv dependencies to the path
base_path = os.path.dirname(os.path.abspath(__file__))
libs_path = os.path.join(base_path, "deps")
sys.path.insert(0, libs_path)

import sdl2
from dotenv import load_dotenv

# Load .env file from one folder above
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.stdout = open(os.environ.get("LOG_FILE", "./logs/log.txt"), "w", buffering=1)


def main():
    import ui
    from romm import RomM

    # Initialize SDL2 with video and game controller support
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER) < 0:
        print(f"SDL2 initialization failed: {sdl2.SDL_GetError()}")
        sys.exit(1)
    sdl2.SDL_GameControllerEventState(sdl2.SDL_ENABLE)

    # Setup the UI
    ui.query_display()
    ui.draw_start()
    ui.screen_reset()
    ui.draw_active(ui.create_image())

    romm = RomM()
    romm.start()

    while True:
        romm.update()
        # Add a small sleep to prevent 100% CPU usage
        sdl2.SDL_Delay(16)  # ~60 FPS


if __name__ == "__main__":
    main()
