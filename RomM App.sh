#!/bin/bash

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
	controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
	controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
	controlfolder="$XDG_DATA_HOME/PortMaster"
else
	controlfolder="/roms/ports/PortMaster"
fi

source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

# Variables
GAMEDIR="/$directory/ports/RomM"

# CD and set log
cd $GAMEDIR
>"$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1

export PYSDL2_DLL_PATH="/usr/lib"
export LD_LIBRARY_PATH="$GAMEDIR/libs:$LD_LIBRARY_PATH"
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"

# Run the app
$GPTOKEYB "python" -c "config/romm.gptk" &
pm_platform_helper "python" >dev/null
python main.py

# Cleanup
pm_finish
