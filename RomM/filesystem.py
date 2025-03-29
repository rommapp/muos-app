import os
from typing import Optional

import platform_maps
from models import Rom


class Filesystem:
    _instance: Optional["Filesystem"] = None
    # Base path: Go up two levels from the script's directory (e.g., from roms/ports/romm to roms/)
    _base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # Resources path: Use current working directory + "resources"
    resources_path = os.path.join(os.getcwd(), "resources")
    # Check if running on muOS
    _is_muOS = os.path.exists(os.path.join(_base_path, "MUOS"))

    # ROMs storage path: Default to ../../ (the roms directory), overridable via environment variable
    # If running on muOS, change the path
    if _is_muOS:
        _roms_storage_path = os.path.join(
            _base_path, "ROMS"
        )  # You can adjust the path as needed
    else:
        _roms_storage_path = os.environ.get("ROMS_STORAGE_PATH", _base_path)

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Filesystem, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Optionally ensure resources directory exists (not required for roms dir)
        if not os.path.exists(self.resources_path):
            os.makedirs(self.resources_path, exist_ok=True)

    def get_roms_storage_path(self) -> str:
        """Return the base ROMs storage path."""
        return self._roms_storage_path

    def get_storage_platform_path(self, platform: str) -> str:
        """Return the platform-specific storage path, using MUOS mapping if on muOS,
        or using ES mapping if available."""

        # First check if the platform has an entry in the ES map
        platform_dir = platform_maps._ES_FOLDER_MAP.get(platform, platform)

        # If the ES map returns a tuple, use the first element of the tuple
        if isinstance(platform_dir, tuple):
            platform_dir = platform_dir[0]

        # If running on muOS, override the platform_dir with the MUOS mapping
        if self._is_muOS:
            platform_dir = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get(
                platform, platform_dir
            )

        # Return the final path using the appropriate platform directory
        return os.path.join(self._roms_storage_path, platform_dir)

    def is_rom_in_device(self, rom: Rom) -> bool:
        """Check if a ROM exists in the storage path."""
        rom_path = os.path.join(
            self.get_storage_platform_path(rom.platform_slug),
            rom.fs_name if not rom.multi else f"{rom.fs_name}.m3u",
        )
        return os.path.exists(rom_path)
