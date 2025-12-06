"""
Unit tests for platform_maps module.

Tests verify:
- JSON loading from platform_maps.json
- Backward compatibility with existing code
- Fallback behavior when JSON is missing/invalid
- CUSTOM_MAPS environment variable override
- Module exports and interfaces
"""

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add RomM to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "RomM"))


class TestPlatformMapsImports:
    """Test module imports and exports."""

    def test_module_imports(self):
        """Test that platform_maps module can be imported."""
        import platform_maps

        assert platform_maps is not None

    def test_required_exports_exist(self):
        """Test that all required module exports exist."""
        import platform_maps

        required_exports = [
            "ES_FOLDER_MAP",
            "MUOS_SUPPORTED_PLATFORMS_FS_MAP",
            "SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP",
            "MUOS_SUPPORTED_PLATFORMS",
            "MUOS_SUPPORTED_PLATFORMS_FS",
            "SPRUCEOS_SUPPORTED_PLATFORMS",
            "SPRUCEOS_SUPPORTED_PLATFORMS_FS",
            "init_env_maps",
            "_env_maps",
            "_env_platforms",
        ]

        for export in required_exports:
            assert hasattr(platform_maps, export), f"Missing export: {export}"


class TestESFolderMap:
    """Test ES_FOLDER_MAP structure and behavior."""

    def test_es_folder_map_is_dict(self):
        """Test that ES_FOLDER_MAP is a dictionary."""
        import platform_maps

        assert isinstance(platform_maps.ES_FOLDER_MAP, dict)

    def test_es_folder_map_not_empty(self):
        """Test that ES_FOLDER_MAP contains entries."""
        import platform_maps

        assert len(platform_maps.ES_FOLDER_MAP) > 0

    def test_es_folder_map_values_are_tuples(self):
        """Test that ES_FOLDER_MAP values are tuples."""
        import platform_maps

        for key, value in platform_maps.ES_FOLDER_MAP.items():
            assert isinstance(
                value, tuple
            ), f"ES_FOLDER_MAP[{key}] should be tuple, got {type(value)}"
            assert (
                len(value) == 2
            ), f"ES_FOLDER_MAP[{key}] should have 2 elements, got {len(value)}"

    def test_es_folder_map_get_method(self):
        """Test ES_FOLDER_MAP.get() with tuple unpacking."""
        import platform_maps

        # Test existing key
        if "ngc" in platform_maps.ES_FOLDER_MAP:
            folder, icon = platform_maps.ES_FOLDER_MAP.get("ngc", ("default", "default"))
            assert folder == "gamecube"
            assert icon == "ngc"

        # Test non-existing key with default
        folder, icon = platform_maps.ES_FOLDER_MAP.get(
            "nonexistent", ("default", "default")
        )
        assert folder == "default"
        assert icon == "default"

    def test_es_folder_map_expected_entries(self):
        """Test that ES_FOLDER_MAP contains expected platform entries."""
        import platform_maps

        # These should exist based on platform_maps.json
        expected_platforms = ["ngc", "n3ds", "genesis", "megadrive", "mastersystem"]

        for platform in expected_platforms:
            assert (
                platform in platform_maps.ES_FOLDER_MAP
            ), f"Missing expected platform: {platform}"


class TestMuOSPlatformMaps:
    """Test MuOS platform mapping structures."""

    def test_muos_map_is_dict(self):
        """Test that MUOS_SUPPORTED_PLATFORMS_FS_MAP is a dictionary."""
        import platform_maps

        assert isinstance(platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP, dict)

    def test_muos_map_not_empty(self):
        """Test that MUOS map contains entries."""
        import platform_maps

        assert len(platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP) > 0

    def test_muos_platforms_is_frozenset(self):
        """Test that MUOS_SUPPORTED_PLATFORMS is a frozenset."""
        import platform_maps

        assert isinstance(platform_maps.MUOS_SUPPORTED_PLATFORMS, frozenset)

    def test_muos_platforms_fs_is_frozenset(self):
        """Test that MUOS_SUPPORTED_PLATFORMS_FS is a frozenset."""
        import platform_maps

        assert isinstance(platform_maps.MUOS_SUPPORTED_PLATFORMS_FS, frozenset)

    def test_muos_frozensets_match_dict(self):
        """Test that frozensets are derived from the dict correctly."""
        import platform_maps

        # Keys should match MUOS_SUPPORTED_PLATFORMS
        assert platform_maps.MUOS_SUPPORTED_PLATFORMS == frozenset(
            platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.keys()
        )

        # Values should match MUOS_SUPPORTED_PLATFORMS_FS
        assert platform_maps.MUOS_SUPPORTED_PLATFORMS_FS == frozenset(
            platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.values()
        )

    def test_muos_platform_lookup(self):
        """Test looking up a specific MuOS platform."""
        import platform_maps

        # Test a known platform
        if "psx" in platform_maps.MUOS_SUPPORTED_PLATFORMS:
            dir_name = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get("psx")
            assert dir_name == "Sony Playstation"

    def test_muos_expected_platforms(self):
        """Test that MuOS map contains expected platforms."""
        import platform_maps

        # Sample of expected platforms
        expected_platforms = ["psx", "n64", "nes", "snes", "arcade"]

        for platform in expected_platforms:
            assert (
                platform in platform_maps.MUOS_SUPPORTED_PLATFORMS
            ), f"Missing MuOS platform: {platform}"


class TestSpruceOSPlatformMaps:
    """Test SpruceOS platform mapping structures."""

    def test_spruceos_map_is_dict(self):
        """Test that SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP is a dictionary."""
        import platform_maps

        assert isinstance(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP, dict)

    def test_spruceos_map_not_empty(self):
        """Test that SpruceOS map contains entries."""
        import platform_maps

        assert len(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP) > 0

    def test_spruceos_platforms_is_frozenset(self):
        """Test that SPRUCEOS_SUPPORTED_PLATFORMS is a frozenset."""
        import platform_maps

        assert isinstance(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS, frozenset)

    def test_spruceos_platforms_fs_is_frozenset(self):
        """Test that SPRUCEOS_SUPPORTED_PLATFORMS_FS is a frozenset."""
        import platform_maps

        assert isinstance(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS, frozenset)

    def test_spruceos_frozensets_match_dict(self):
        """Test that frozensets are derived from the dict correctly."""
        import platform_maps

        # Keys should match SPRUCEOS_SUPPORTED_PLATFORMS
        assert platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS == frozenset(
            platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.keys()
        )

        # Values should match SPRUCEOS_SUPPORTED_PLATFORMS_FS
        assert platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS == frozenset(
            platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.values()
        )

    def test_spruceos_expected_platforms(self):
        """Test that SpruceOS map contains expected platforms."""
        import platform_maps

        # Sample of expected platforms
        expected_platforms = ["psx", "n64", "nes", "snes", "arcade"]

        for platform in expected_platforms:
            assert (
                platform in platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS
            ), f"Missing SpruceOS platform: {platform}"


class TestJSONLoading:
    """Test JSON file loading behavior."""

    def test_json_file_exists(self):
        """Test that platform_maps.json exists."""
        json_path = Path(__file__).parent.parent / "platform_maps.json"
        assert json_path.exists(), "platform_maps.json should exist"

    def test_json_file_valid(self):
        """Test that platform_maps.json is valid JSON."""
        json_path = Path(__file__).parent.parent / "platform_maps.json"
        with open(json_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_json_file_structure(self):
        """Test that platform_maps.json has required keys."""
        json_path = Path(__file__).parent.parent / "platform_maps.json"
        with open(json_path, "r") as f:
            data = json.load(f)

        required_keys = ["es_folder_map", "muos", "spruceos"]
        for key in required_keys:
            assert key in data, f"Missing required key in JSON: {key}"

    def test_json_es_folder_map_arrays(self):
        """Test that es_folder_map values are arrays in JSON."""
        json_path = Path(__file__).parent.parent / "platform_maps.json"
        with open(json_path, "r") as f:
            data = json.load(f)

        es_map = data.get("es_folder_map", {})
        for key, value in es_map.items():
            assert isinstance(
                value, list
            ), f"es_folder_map[{key}] should be array in JSON"
            assert len(value) == 2, f"es_folder_map[{key}] should have 2 elements"

    def test_maps_loaded_from_json(self):
        """Test that module loads data from JSON file."""
        import platform_maps

        # Verify some platforms exist (they should come from JSON)
        assert len(platform_maps.ES_FOLDER_MAP) >= 5
        assert len(platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP) >= 90
        assert len(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP) >= 70


class TestInitEnvMaps:
    """Test init_env_maps function."""

    def test_init_env_maps_callable(self):
        """Test that init_env_maps can be called."""
        import platform_maps

        # Should not raise any exceptions
        platform_maps.init_env_maps()

    def test_init_env_maps_sets_globals(self):
        """Test that init_env_maps sets global variables."""
        import platform_maps

        platform_maps.init_env_maps()

        assert platform_maps._env_maps is not None
        assert platform_maps._env_platforms is not None
        assert isinstance(platform_maps._env_maps, dict)
        assert isinstance(platform_maps._env_platforms, frozenset)


class TestCustomMapsEnvVar:
    """Test CUSTOM_MAPS environment variable behavior."""

    def test_custom_maps_empty_by_default(self):
        """Test that _env_maps is empty when CUSTOM_MAPS not set."""
        # Ensure CUSTOM_MAPS is not set
        with mock.patch.dict(os.environ, {}, clear=False):
            if "CUSTOM_MAPS" in os.environ:
                del os.environ["CUSTOM_MAPS"]

            # Reload module to test
            import platform_maps
            from importlib import reload

            reload(platform_maps)

            platform_maps.init_env_maps()
            assert platform_maps._env_maps == {}

    def test_custom_maps_loads_from_env(self):
        """Test that CUSTOM_MAPS env var is loaded."""
        custom_maps = '{"test_platform": "test_dir"}'

        with mock.patch.dict(os.environ, {"CUSTOM_MAPS": custom_maps}):
            import platform_maps
            from importlib import reload

            reload(platform_maps)

            platform_maps.init_env_maps()
            assert "test_platform" in platform_maps._env_maps
            assert platform_maps._env_maps["test_platform"] == "test_dir"

    def test_custom_maps_invalid_json(self):
        """Test that invalid JSON in CUSTOM_MAPS is handled gracefully."""
        invalid_json = "{'invalid': json}"

        with mock.patch.dict(os.environ, {"CUSTOM_MAPS": invalid_json}):
            import platform_maps
            from importlib import reload

            reload(platform_maps)

            # Should not crash, should fallback to empty dict
            platform_maps.init_env_maps()
            assert platform_maps._env_maps == {}


class TestFallbackBehavior:
    """Test fallback to hardcoded constants."""

    def test_fallback_constants_exist(self):
        """Test that fallback constants are defined."""
        import platform_maps

        assert hasattr(platform_maps, "_FALLBACK_ES_FOLDER_MAP")
        assert hasattr(platform_maps, "_FALLBACK_MUOS_SUPPORTED_PLATFORMS_FS_MAP")
        assert hasattr(platform_maps, "_FALLBACK_SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP")

    def test_fallback_constants_not_empty(self):
        """Test that fallback constants contain data."""
        import platform_maps

        assert len(platform_maps._FALLBACK_ES_FOLDER_MAP) > 0
        assert len(platform_maps._FALLBACK_MUOS_SUPPORTED_PLATFORMS_FS_MAP) > 0
        assert len(platform_maps._FALLBACK_SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP) > 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_dict_get_interface(self):
        """Test that .get() method works as expected."""
        import platform_maps

        # ES_FOLDER_MAP with tuple unpacking
        folder, icon = platform_maps.ES_FOLDER_MAP.get("ngc", ("default", "default"))
        assert isinstance(folder, str)
        assert isinstance(icon, str)

        # MUOS map
        dir_name = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get("psx", "default")
        assert isinstance(dir_name, str)

        # SpruceOS map
        dir_name = platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.get(
            "psx", "default"
        )
        assert isinstance(dir_name, str)

    def test_in_operator_works(self):
        """Test that 'in' operator works on all collections."""
        import platform_maps

        # Test with dicts
        if len(platform_maps.ES_FOLDER_MAP) > 0:
            first_key = list(platform_maps.ES_FOLDER_MAP.keys())[0]
            assert first_key in platform_maps.ES_FOLDER_MAP

        # Test with frozensets
        if len(platform_maps.MUOS_SUPPORTED_PLATFORMS) > 0:
            first_platform = list(platform_maps.MUOS_SUPPORTED_PLATFORMS)[0]
            assert first_platform in platform_maps.MUOS_SUPPORTED_PLATFORMS

    def test_iteration_works(self):
        """Test that iteration over collections works."""
        import platform_maps

        # Iterate over dict keys
        count = 0
        for key in platform_maps.ES_FOLDER_MAP:
            count += 1
            assert isinstance(key, str)
        assert count > 0

        # Iterate over frozenset
        count = 0
        for platform in platform_maps.MUOS_SUPPORTED_PLATFORMS:
            count += 1
            assert isinstance(platform, str)
        assert count > 0

    def test_filesystem_module_usage(self):
        """Test usage pattern from filesystem.py."""
        import platform_maps

        # Simulate filesystem.py usage pattern
        platform = "psx"

        # ES map check (filesystem.py line 87)
        platform_dir = platform_maps.ES_FOLDER_MAP.get(platform, platform)
        if isinstance(platform_dir, tuple):
            platform_dir = platform_dir[0]
        assert isinstance(platform_dir, str)

        # MuOS override (filesystem.py lines 94-97)
        platform_dir = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get(
            platform, platform_dir
        )
        assert isinstance(platform_dir, str)

        # SpruceOS override (filesystem.py lines 99-102)
        platform_dir = platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.get(
            platform, platform_dir
        )
        assert isinstance(platform_dir, str)

    def test_api_module_usage(self):
        """Test usage pattern from api.py."""
        import platform_maps

        # Simulate api.py usage pattern (line 160-162)
        platform_slug = "ngc"
        mapped_slug, icon_filename = platform_maps.ES_FOLDER_MAP.get(
            platform_slug.lower(), (platform_slug, platform_slug)
        )

        assert isinstance(mapped_slug, str)
        assert isinstance(icon_filename, str)

        # Test platform existence checks (api.py lines 265-292)
        test_platform = "psx"
        if test_platform in platform_maps._env_platforms:
            # Has custom mapping
            pass
        elif test_platform in platform_maps.MUOS_SUPPORTED_PLATFORMS:
            # Is MuOS platform
            assert test_platform in platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP


class TestPlatformCounts:
    """Test expected platform counts."""

    def test_es_folder_map_count(self):
        """Test ES_FOLDER_MAP has expected number of entries."""
        import platform_maps

        # Should have at least 5 entries from JSON
        assert len(platform_maps.ES_FOLDER_MAP) >= 5

    def test_muos_map_count(self):
        """Test MUOS maps have expected number of entries."""
        import platform_maps

        # Should have around 92 entries from JSON
        assert len(platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP) >= 90
        assert len(platform_maps.MUOS_SUPPORTED_PLATFORMS) >= 90

    def test_spruceos_map_count(self):
        """Test SpruceOS maps have expected number of entries."""
        import platform_maps

        # Should have around 72 entries from JSON
        assert len(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP) >= 70
        assert len(platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS) >= 70
