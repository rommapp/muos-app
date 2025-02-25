#!/bin/bash
# HELP: RomM muOS client to download roms directly from your RomM server
# ICON: romm

. /opt/muos/script/var/func.sh

echo app >/tmp/act_go

ROOT_DIR="$(GET_VAR "device" "storage/rom/mount")/MUOS/application/.romm"
LOG_DIR="${ROOT_DIR}/logs"

mkdir -p "${LOG_DIR}"

# Ensure pip is installed
command -v pip3 >/dev/null || python3 -m ensurepip --default-pip

# Install dependencies if missing
python3 -c "import PIL" 2>/dev/null || pip3 install --no-cache-dir pillow
python3 -c "import dotenv" 2>/dev/null || pip3 install --no-cache-dir python-dotenv

cd "${ROOT_DIR}" || exit

ENTRYPOINT="python3 romm.py"
LOG_FILE="${LOG_DIR}/$(date +'%Y-%m-%d_%H-%M-%S').log"

# Use muxstart to launch the app, ensuring it runs in its own session
muxstart -n romm -d "${ROOT_DIR}" -s "${ENTRYPOINT}" >"${LOG_FILE}" 2>&1
