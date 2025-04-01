#!/bin/bash
# HELP: RomM muOS client to download games wirelessly from your server
# ICON: romm

. /opt/muos/script/var/func.sh # trunk-ignore(shellcheck/SC1091)

echo app >/tmp/act_go

ROOT_DIR="$(GET_VAR "device" "storage/rom/mount")"
APP_DIR="${ROOT_DIR}/MUOS/application/RomM"
LOG_DIR="${APP_DIR}/logs"
ICON_DIR=/opt/muos/default/MUOS/theme/active/glyph/muxapp/
FONTS_DIR="/usr/share/fonts/romm"

mkdir -p "${LOG_DIR}"

# Copy app icon
cp "${APP_DIR}/resources/romm.png" "${ICON_DIR}/romm.png"

# Copy app fonts
mkdir -p "${FONTS_DIR}"
cp "${APP_DIR}/fonts/romm.ttf" "${FONTS_DIR}/romm.ttf"
cd "${APP_DIR}" || exit

# trunk-ignore(shellcheck/SC1091)
source "${ROOT_DIR}/MUOS/PortMaster/muos/control.txt"
get_controls

# trunk-ignore(shellcheck/SC2155)
export LOG_FILE="${LOG_DIR}/$(date +'%Y-%m-%d_%H-%M-%S').log"
export PYSDL2_DLL_PATH="/usr/lib"
export LD_LIBRARY_PATH="${APP_DIR}/libs:${LD_LIBRARY_PATH}"

python3 -u main.py >"${LOG_FILE}" 2>&1

SCREEN_TYPE="internal"
DEVICE_MODE="$(GET_VAR "global" "boot/device_mode")"
if [[ ${DEVICE_MODE} -eq 1 ]]; then
	SCREEN_TYPE="external"
fi

DEVICE_WIDTH="$(GET_VAR "device" "screen/${SCREEN_TYPE}/width")"
DEVICE_HEIGHT="$(GET_VAR "device" "screen/${SCREEN_TYPE}/height")"
FB_SWITCH "${DEVICE_WIDTH}" "${DEVICE_HEIGHT}" 32
