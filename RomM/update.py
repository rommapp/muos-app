import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import sdl2
from glyps import glyphs
from ui import UserInterface


class Update:

    REPO = "rommapp/muos-app"

    def __init__(self, romm):
        self.ui = UserInterface()
        self.status = romm.status
        self.current_version = self.get_current_version()
        self.download_percent = 0.0
        self.update_filename = ""
        self.total_size = 0

    def get_current_version(self):
        """Read the version from __version__.py in the current directory."""
        version_file = "__version__.py"
        if not os.path.exists(version_file):
            print("__version__.py not found")
            return "0.0.0"

        with open(version_file, "r") as f:
            content = f.read()
            match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                return match.group(1)
            else:
                print("Failed to read version from __version__.py")
                return "0.0.0"

    def compare_versions(self, v1, v2):
        """Compare two version strings (e.g., '0.3.0' < '0.4.0')."""
        v1_parts = [int(x) for x in v1.split(".")]
        v2_parts = [int(x) for x in v2.split(".")]
        for i in range(max(len(v1_parts), len(v2_parts))):
            part1 = v1_parts[i] if i < len(v1_parts) else 0
            part2 = v2_parts[i] if i < len(v2_parts) else 0
            if part1 < part2:
                print(f"Current version: {v1}, Latest version: {v2}")
                return -1
            elif part1 > part2:
                print(f"Current version: {v1}, Latest version: {v2}")
                return 1
        print(f"Current version: {v1}, Latest version: {v2}")
        return 0

    def get_latest_release_info(self):
        url = f"https://api.github.com/repos/{self.REPO}/releases/latest"
        try:
            request = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urlopen(request, timeout=10) as response:  # trunk-ignore(bandit/B310)
                data = response.read().decode("utf-8")
                import json

                return json.loads(data)
        except (HTTPError, URLError) as e:
            print(f"Failed to fetch latest release info: {e}")
            return None

    def download_update(self, url):
        self.update_filename = os.path.basename(url)
        filepath = self.update_filename

        try:
            request = Request(url)
            with urlopen(request) as response:  # trunk-ignore(bandit/B310)
                self.total_size = int(response.getheader("Content-Length", 0)) or 1
                self.download_percent = 0.0
                downloaded_bytes = 0
                chunk_size = 1024

                with open(filepath, "wb") as out_file:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded_bytes += len(chunk)
                        self.download_percent = min(
                            100.0, (downloaded_bytes / self.total_size) * 100
                        )
                        self.ui.draw_loader(self.download_percent)
                        self.ui.draw_log(
                            text_line_1="Downloading update...",
                            text_line_2=f"{self.download_percent:.2f} / 100 % | ( {glyphs.download} {filepath})",
                            background=True,
                        )
                        self.ui.render_to_screen()
                        sdl2.SDL_Delay(16)

                self.status.updating.clear()
                return True

        except (HTTPError, URLError) as e:
            print(f"Update download failed: {e}")
            self.status.updating.clear()
            if os.path.exists(filepath):
                os.remove(filepath)
            return False
