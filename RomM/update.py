import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import sdl2
from filesystem import Filesystem
from glyps import glyphs
from semver import Version
from status import Status


class Update:
    github_repo = "rommapp/muos-app"

    def __init__(self, ui):
        self.ui = ui
        self.status = Status()
        self.filesystem = Filesystem()
        self.current_version = self.get_current_version()
        self.download_percent = 0.0
        self.total_size = 0

    def get_current_version(self) -> str:
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

    def update_available(self, v1, v2) -> bool:
        v1 = Version.parse(v1)
        v2 = Version.parse(v2)

        return v1 < v2

    def get_latest_release_info(self) -> dict | None:
        url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        try:
            request = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urlopen(request, timeout=5) as response:  # trunk-ignore(bandit/B310)
                data = response.read().decode("utf-8")
                import json

                return json.loads(data)
        except (HTTPError, URLError) as e:
            print(f"Failed to fetch latest release info: {e}")
            return None

    def download_update(self, url) -> bool:
        update_filename = os.path.basename(url)
        try:
            request = Request(url)
            with urlopen(request) as response:  # trunk-ignore(bandit/B310)
                self.total_size = int(response.getheader("Content-Length", 0)) or 1
                self.download_percent = 0.0
                downloaded_bytes = 0
                chunk_size = 1024

                with open(update_filename, "wb") as out_file:
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
                            text_line_2=f"{self.download_percent:.2f} / 100 % | ( {glyphs.download} {update_filename})",
                            background=True,
                        )
                        self.ui.render_to_screen()
                        sdl2.SDL_Delay(16)

                self.status.updating.clear()
                return True

        except (HTTPError, URLError) as e:
            print(f"Update download failed: {e}")
            self.status.updating.clear()
            if os.path.exists(update_filename):
                os.remove(update_filename)
            return False
