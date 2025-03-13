#!/bin/bash
# Usage: ./scripts/build.sh [<PRIVATE_KEY_PATH>] [<DEVICE_IP>]
# If PRIVATE_KEY_PATH and DEVICE_IP are provided, the zip file will be uploaded to the device with scp

APPLICATION_DIR=mnt/mmc/MUOS/application
GLYPH_DIR=opt/muos/default/MUOS/theme/active/glyph/muxapp
FONTS_FIR=usr/share/fonts/romm
ZIP_BASE_NAME=romm_muOS_install
NO_VERSION=0
VERSION=$(grep -oP '(?<=version = ")[^"]*' .romm/__version__.py)
# If version not set, use branch name
if [[ ${VERSION} == "<version>" ]]; then
	VERSION=$(git rev-parse --abbrev-ref HEAD)
	NO_VERSION=1
fi
VERSION=${VERSION//\//_} # Replace slashes with underscores
PRIVATE_KEY_PATH=$1
DEVICE_IP=$2

mkdir -p .dist
mkdir -p .build/"${APPLICATION_DIR}"
cp RomM.sh .build/"${APPLICATION_DIR}"
rsync -av --exclude='__pycache__' --exclude='fonts' --exclude='.env' .romm/ .build/"${APPLICATION_DIR}"/.romm/
if [[ ${NO_VERSION} -eq 1 ]]; then
	sed -i "s/<version>/-${VERSION}/" .build/"${APPLICATION_DIR}"/.romm/__version__.py
fi

mkdir -p .build/"${GLYPH_DIR}"
cp .romm/resources/romm.png .build/"${GLYPH_DIR}"

mkdir -p .build/"${FONTS_FIR}"
cp .romm/fonts/romm.ttf .build/"${FONTS_FIR}"

(cd .build && zip -r "../${ZIP_BASE_NAME}_${VERSION}.zip" ./*)

mv "${ZIP_BASE_NAME}_${VERSION}.zip" .dist/"${ZIP_BASE_NAME}_${VERSION}.zip"
rm -rf .build

if [[ -z ${PRIVATE_KEY_PATH} ]]; then
	echo "No PRIVATE_KEY_PATH provided, skipping SCP upload"
	exit 0
elif [[ -z ${DEVICE_IP} ]]; then
	echo "No DEVICE_IP provided, skipping SCP upload"
	exit 0
else
	echo "Uploading to ${DEVICE_IP}"
	scp -i "${PRIVATE_KEY_PATH}" .dist/"${ZIP_BASE_NAME}_${VERSION}.zip" root@"${DEVICE_IP}":/mnt/mmc/ARCHIVE
fi
