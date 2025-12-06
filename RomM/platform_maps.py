import json
import os
from pathlib import Path

# Manual mapping of RomM slugs to device folder names and platform icons for es systems
# This is sometimes needed to match custom system folders with defaults, for example ES-DE uses roms/gc and some Batocera forks use roms/gamecube
# https://gitlab.com/es-de/emulationstation-de/-/blob/master/resources/systems/unix/es_systems.xml

# ============================================================================
# FALLBACK CONSTANTS (used if JSON file is missing or invalid)
# ============================================================================

# EmulationStation custom folder map (fallback)
_FALLBACK_ES_FOLDER_MAP = {
    # "slug": ("es-system", "icon"),
    "ngc": ("gamecube", "ngc"),  # Nintendo GameCube
    "n3ds": ("3ds", "3ds"),  # Nintendo 3DS
    "genesis": ("genesis", "genesis"),  # Sega Genesis / Megadrive
    "megadrive": ("megadrive", "genesis"),  # Sega Genesis / Megadrive
    "mastersystem": ("mastersystem", "sms"),  # Sega Mastersystem
}

# Manual mapping of RomM slugs for MuOS default platforms (fallback)
_FALLBACK_MUOS_SUPPORTED_PLATFORMS_FS_MAP = {
    "acpc": "Amstrad",
    "arcade": "Arcade",
    "arduboy": "Arduboy",
    "atari2600": "Atari 2600",
    "atari5200": "Atari 5200",
    "atari7800": "Atari 7800",
    "jaguar": "Atari Jaguar",
    "lynx": "Atari Lynx",
    "atari-st": "Atari ST-STE-TT-Falcon",
    "wonderswan": "Bandai WonderSwan-Color",
    "wonderswan-color": "Book Reader",
    "cave-story": "Cave Story",
    "chailove": "ChaiLove",
    "chip-8": "CHIP-8",
    "colecovision": "ColecoVision",
    "amiga": "Commodore Amiga",
    "c128": "Commodore C128",
    "c64": "Commodore C64",
    "cbm-ii": "Commodore CBM-II",
    "cpet": "Commodore PET",
    "vic-20": "Commodore VIC-20",
    "dos": "DOS",
    "doom": "Doom",
    "ports": "External - Ports",
    "fairchild-channel-f": "Fairchild ChannelF",
    "vectrex": "GCE - Vectrex",
    "galaksija": "Galaksija Retro Computer",
    "g-and-w": "Handheld Electronic - Game and Watch",
    "j2me": "Java J2ME",
    "karaoke": "Karaoke",
    "lowres": "Lowres NX",
    "lua": "Lua Engine",
    "odyssey--1": "Magnavox Odyssey - VideoPac",
    "intellivision": "Mattel - Intellivision",
    "media-player": "Media Player",
    "mega-duck-slash-cougar-boy": "Mega Duck",
    "msx": "Microsoft - MSX",
    "turbografx-cd": "NEC PC Engine CD",
    "tg16": "NEC PC Engine",
    "supergrafx": "NEC PC Engine SuperGrafx",
    "pc-8000": "NEC PC-8000 - PC-8800 series",
    "pc-fx": "NEC PC-FX",
    "pc-9800-series": "NEC PC98",
    "nds": "Nintendo DS",
    "fds": "Nintendo FDS",
    "gba": "Nintendo Game Boy Advance",
    "gbc": "Nintendo Game Boy Color",
    "gb": "Nintendo Game Boy",
    "n64": "Nintendo N64",
    "nes": "Nintendo NES-Famicom",
    "famicom": "Nintendo NES-Famicom",
    "snes": "Nintendo SNES-SFC",
    "sfam": "Nintendo SNES-SFC",
    "pokemon-mini": "Nintendo Pokemon Mini",
    "virtualboy": "Nintendo Virtual Boy",
    "onscripter": "Onscripter",
    "openbor": "OpenBOR",
    "pico-8": "PICO-8",
    "philips-cd-i": "Philips CDi",
    "quake": "Quake",
    "rpg-maker": "RPG Maker 2000 - 2003",
    "neogeoaes": "SNK Neo Geo",
    "neogeomvs": "SNK Neo Geo",
    "neo-geo-cd": "SNK Neo Geo CD",
    "neo-geo-pocket": "SNK Neo Geo Pocket - Color",
    "neo-geo-pocket-color": "SNK Neo Geo Pocket - Color",
    "scummvm": "ScummVM",
    "sega32": "Sega 32X",
    "naomi": "Sega Atomiswave Naomi",
    "dc": "Sega Dreamcast",
    "gamegear": "Sega Game Gear",
    "sega-master-system": "Sega Master System",
    "genesis": "Sega Mega Drive - Genesis",
    "sega-pico": "Sega Pico",
    "segacd": "Sega Mega CD - Sega CD",
    "sg1000": "Sega SG-1000",
    "saturn": "Sega Saturn",
    "x1": "Sharp X1",
    "sharp-x68000": "Sharp X68000",
    "sinclair-zx81": "Sinclair ZX 81",
    "zxs": "Sinclair ZX Spectrum",
    "psx": "Sony Playstation",
    "psp": "Sony Playstation Portable",
    "tic-80": "TIC-80",
    "ti-83": "Texas Instruments TI-83",
    "3do": "The 3DO Company - 3DO",
    "uzebox": "Uzebox",
    "vemulator": "VeMUlator",
    "vircon-32": "Vircon32",
    "wasm-4": "WASM-4",
    "watara-slash-quickshot-supervision": "Watara Supervision",
    "wolfenstein-3d": "Wolfenstein 3D",
}

# Manual mapping of RomM slugs for SpruceOS default platforms (fallback)
_FALLBACK_SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP = {
    "amiga": "AMIGA",
    "acpc": "CPC",
    "arcade": "ARCADE",
    "arduboy": "ARDUBOY",
    "atari2600": "ATARI",
    "atari8bit": "EIGHTHUNDRED",
    "atari5200": "FIFTYTWOHUNDRED",
    "atari7800": "SEVENTYEIGHTHUNDRED",
    "lynx": "LYNX",
    "sufami": "SUFAMI",
    "wonderswan": "WS",
    "wonderswan-color": "WSC",
    "cps1": "CPS1",
    "cps2": "CPS2",
    "cps3": "CPS3",
    "colecovision": "COLECO",
    "c64": "COMMODORE",
    "vic-20": "VIC20",
    "doom": "DOOM",
    "fairchild-channel-f": "FAIRCHILD",
    "fds": "FDS",
    "g-and-w": "GW",
    "vectrex": "VECTREX",
    "odyssey-2-slash-videopac-g7000": "ODYSSEY",
    "mame2003plus": "MAME2003PLUS",
    "intellivision": "INTELLIVISION",
    "mega-duck-slash-cougar-boy": "MEGADUCK",
    "dos": "DOS",
    "msx": "MSX",
    "msx2": "MSX",  # same folder for both MSX and MSX2
    "supergrafx": "SGFX",
    "turbografx-cd": "PCECD",
    "tg16": "PCE",
    "n64": "N64",
    "nds": "NDS",
    "nes": "FC",
    "gba": "GBA",
    "gbc": "GBC",
    "gb": "GB",
    "pokemon-mini": "POKE",
    "satellaview": "SATELLAVIEW",
    "sgb": "SGB",
    "snes": "SFC",
    "virtualboy": "VB",
    "openbor": "OPENBOR",
    "fake08": "FAKE08",
    "pico": "PICO8",
    "psp": "PSP",
    "quake": "QUAKE",
    "scummvm": "SCUMMVM",
    "sega32": "THIRTYTWOX",
    "segacd": "SEGACD",
    "dc": "DC",
    "gamegear": "GG",
    "msumd": "MSUMD",
    "genesis": "MD",
    "mastersystem": "MS",
    "sg1000": "SEGASGONE",
    "sharp-x68000": "X68000",
    "zxspectrum": "ZXS",
    "msu1": "MSU1",
    "neo-geo-cd": "NEOCD",
    "ngp": "NGP",
    "ngpc": "NGPC",
    "neogeoaes": "NEOGEO",
    "neogeomvs": "NEOCD",
    "psx": "PS",
    "saturn": "SATURN",
    "tic80": "TIC",
    "videopac-g7400": "VIDEOPAC",
    "supervision": "SUPERVISION",
    "wolf3d": "WOLF",
}

# ============================================================================
# JSON LOADING FUNCTIONS
# ============================================================================


def _load_json_maps() -> dict:
    """
    Load platform mappings from platform_maps.json in project root.
    Falls back to hardcoded constants if JSON file is missing or invalid.
    """
    # Define fallback maps once for reuse
    fallback_maps = {
        "es_folder_map": _FALLBACK_ES_FOLDER_MAP,
        "muos": _FALLBACK_MUOS_SUPPORTED_PLATFORMS_FS_MAP,
        "spruceos": _FALLBACK_SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP,
    }

    # Calculate path: Go up from RomM/ to project root
    json_path = Path(__file__).parent.parent / "platform_maps.json"

    if not json_path.exists():
        print(f"Warning: {json_path} not found, using hardcoded defaults")
        return fallback_maps

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        # Validate required keys exist, falling back for each if missing
        for key, default_value in fallback_maps.items():
            if key not in loaded:
                loaded[key] = default_value

        return loaded

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading or parsing platform_maps.json: {e}")
        print("Falling back to hardcoded defaults")
        return fallback_maps


def _convert_json_arrays_to_tuples(es_map: dict) -> dict:
    """
    Convert JSON arrays like ["folder", "icon"] to Python tuples.
    This is needed for ES_FOLDER_MAP which uses tuple format.
    """
    return {k: tuple(v) if isinstance(v, list) else v for k, v in es_map.items()}


def _load_env_maps() -> dict[str, str]:
    """
    Load custom maps from CUSTOM_MAPS environment variable.
    Returns empty dict if not set or invalid JSON.
    """
    raw = os.getenv("CUSTOM_MAPS")
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
        return loaded
    except json.JSONDecodeError as e:
        print(f"Error: CUSTOM_MAPS is an invalid JSON format: {e}")
        return {}
    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        return {}


# ============================================================================
# MODULE-LEVEL STATE
# ============================================================================

_env_maps = None
_env_platforms = None


def init_env_maps():
    """
    Initialize custom map overrides from the CUSTOM_MAPS environment variable.
    This function is called from main.py on startup.
    """
    global _env_maps, _env_platforms

    # Load env var overrides (highest priority)
    if _env_maps is None:
        _env_maps = _load_env_maps()

    if _env_platforms is None:
        _env_platforms = frozenset(_env_maps.keys())


# ============================================================================
# MODULE-LEVEL EXPORTS (Backward Compatibility)
# ============================================================================

# Lazy initialization on first import
_temp_maps = _load_json_maps()

# Convert JSON arrays to tuples for ES_FOLDER_MAP
ES_FOLDER_MAP = _convert_json_arrays_to_tuples(_temp_maps.get("es_folder_map", {}))

# Load platform maps directly from JSON
MUOS_SUPPORTED_PLATFORMS_FS_MAP = _temp_maps.get("muos", {})
SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP = _temp_maps.get("spruceos", {})

# Create frozensets for efficient platform lookups
MUOS_SUPPORTED_PLATFORMS = frozenset(MUOS_SUPPORTED_PLATFORMS_FS_MAP.keys())
MUOS_SUPPORTED_PLATFORMS_FS = frozenset(MUOS_SUPPORTED_PLATFORMS_FS_MAP.values())
SPRUCEOS_SUPPORTED_PLATFORMS = frozenset(SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.keys())
SPRUCEOS_SUPPORTED_PLATFORMS_FS = frozenset(
    SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.values()
)
