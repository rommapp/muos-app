#!/bin/bash
# HELP: RomM muOS client to download roms directly from your RomM server
# ICON: romm

. /opt/muos/script/var/func.sh

echo app >/tmp/act_go

ROOT_DIR="$(GET_VAR "device" "storage/rom/mount")/MUOS/application/.romm"
LOG_DIR="${ROOT_DIR}/logs"
ICON_DIR=/opt/muos/default/MUOS/theme/active/glyph/muxapp/
FONTS_DIR="/usr/share/fonts/romm"

mkdir -p "${LOG_DIR}"

# Copy app icon
cp "${ROOT_DIR}/resources/romm.png" "${ICON_DIR}/romm.png"

# Copy app fonts
mkdir -p "${FONTS_DIR}"
cp "${ROOT_DIR}/fonts/romm.ttf" "${FONTS_DIR}/romm.ttf"

# Ensure pip is installed
command -v pip3 >/dev/null || python3 -m ensurepip --default-pip

# Install dependencies if missing
python3 -c "import PIL" 2>/dev/null || pip3 install --no-cache-dir pillow
python3 -c "import dotenv" 2>/dev/null || pip3 install --no-cache-dir python-dotenv

cd "${ROOT_DIR}" || exit

LOG_FILE="${LOG_DIR}/$(date +'%Y-%m-%d_%H-%M-%S').log"

python3 romm.py >"${LOG_FILE}" 2>&1
