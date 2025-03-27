# To-Do

## Necessities

- Test on various platforms, especially muOS to ensure compatibility is retained.
- Test extended features to verify working order (buttons may have been missed, missing menu w/ platform info, etc).
- SD is hardcoded based on where romM client was run (backs out two directories). Regain ability to choose SD2.
- GPTOKEYB enviroment variable is still used, which is a PortMaster dependency. Either bundle gptokeyb with the package or implement SDL2 gamecontrollerdb detection.

- Scale font and buttons better for high dpi displays such as the Retroid Pocket Mini (3.7" AMOLED 1280x960).

## Ideas

- Allow a config file for `platform_maps.py` or compose maps from `es_systems.xml` file if present.
- Allow a config file for users to change the color and text of the UI buttons to customize to their device.