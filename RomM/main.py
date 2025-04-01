# trunk-ignore-all(ruff/E402)

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

from romm import RomM


def cleanup(romm: RomM, exit_code: int):
    romm.ui.cleanup()
    romm.input.cleanup()

    sys.stdout.close()
    sys.exit(exit_code)


def main():
    # Initialize SDL2 with video and joystick support
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_GAMECONTROLLER) < 0:
        print(f"SDL2 initialization failed: {sdl2.SDL_GetError()}")
        sys.exit(1)

    romm = RomM()
    romm.start()

    try:
        while romm.running:
            # Render directly to the screen
            sdl2.SDL_SetRenderDrawColor(romm.ui.renderer, 0, 0, 0, 255)
            sdl2.SDL_RenderClear(romm.ui.renderer)

            romm.ui.draw_start()  # Render at 640x480
            romm.update()  # Draw content
            romm.ui.render_to_screen()  # Render to the screen

            # Add a small sleep to prevent 100% CPU usage
            sdl2.SDL_Delay(16)
    except RuntimeError:
        cleanup(romm, 1)

    # Cleanup
    print("Exiting...")
    cleanup(romm, 0)


if __name__ == "__main__":
    main()
