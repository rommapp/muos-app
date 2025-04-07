# trunk-ignore-all(ruff/E402)

import os
import sys
import zipfile

# Add dependencies to path
base_path = os.path.dirname(os.path.abspath(__file__))
libs_path = os.path.join(base_path, "deps")
sys.path.insert(0, libs_path)

def apply_update() -> bool:
    # The archive contains a RomM folder with the contents inside
    # We want to extract to the folder above the current one so it overwrites our application correctly
    update_path = os.path.abspath(os.path.join(base_path, ".."))
    update_files = [f for f in os.listdir(base_path) if f.endswith(".muxapp")]
    if not update_files:
        return False

    update_file = os.path.join(base_path, update_files[0])
    try:
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall(update_path)
        os.remove(update_file)
        os.execv(sys.executable, [sys.executable] + sys.argv)
        return True
    except (zipfile.BadZipFile, OSError) as e:
        print(f"Failed to apply update: {e}", file=sys.stderr)
        return False

# Check for update before initializing since it may overwrite our dependencies
if not apply_update():
    from dotenv import load_dotenv
    import sdl2
    from romm import RomM
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    sys.stdout = open(os.environ.get("LOG_FILE", "./logs/log.txt"), "w", buffering=1)

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
            romm.ui.draw_start()  # Render at 640x480
            romm.update()  # Draw content
            romm.ui.render_to_screen()  # Render to the screen
            romm.input.clear_pressed()  # Clear pressed keys

            # Add a small sleep to prevent 100% CPU usage
            sdl2.SDL_Delay(16)
    except RuntimeError:
        cleanup(romm, 1)

    # Cleanup
    print("Exiting...")
    cleanup(romm, 0)


if __name__ == "__main__":
    main()
