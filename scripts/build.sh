#!/bin/bash
# Usage: ./scripts/build.sh --key <private_key_path> --ip <device_ip> --password <device_password>

GLYPH_DIR=opt/muos/default/MUOS/theme/active/glyph/muxapp
FONTS_DIR=usr/share/fonts/romm
ZIP_BASE_NAME="RomM Installer"

NO_VERSION=0
VERSION=$(grep -oP '(?<=version = ")[^"]*' RomM/__version__.py)
# If version not set, use branch name
if [[ ${VERSION} == "<version>" ]]; then
	VERSION=$(git rev-parse --abbrev-ref HEAD)
	NO_VERSION=1
fi
VERSION=${VERSION//\//_} # Replace slashes with underscores

PRIVATE_KEY_PATH=""
DEVICE_IP=""
PASSWORD=""

while [[ $1 != "" ]]; do
	case $1 in
	--key)
		shift
		PRIVATE_KEY_PATH=$1
		;;
	--password)
		shift
		PASSWORD=$1
		;;
	--ip)
		shift
		DEVICE_IP=$1
		;;
	*)
		echo "Invalid argument"
		exit 1
		;;
	esac
	shift
done

mkdir -p .build
mkdir -p .dist

rsync -av --exclude='__pycache__' --exclude='fonts' --exclude='.env' RomM/ .build/RomM/
if [[ ${NO_VERSION} -eq 1 ]]; then
	sed -i "s/<version>/-${VERSION}/" .build/RomM/__version__.py
fi

# mkdir -p .build/"${GLYPH_DIR}"
# cp RomM/resources/romm.png .build/"${GLYPH_DIR}"

# mkdir -p .build/"${FONTS_DIR}"
# cp RomM/fonts/romm.ttf .build/"${FONTS_DIR}"

(cd .build && zip -r "../${ZIP_BASE_NAME} ${VERSION}.muxapp" ./*)

mv "${ZIP_BASE_NAME} ${VERSION}.muxapp" .dist/"${ZIP_BASE_NAME} ${VERSION}.muxapp"
rm -rf .build

if [[ -z ${DEVICE_IP} ]]; then
	echo "No DEVICE_IP provided, skipping SCP upload"
	exit 0
fi

if [[ -n ${PRIVATE_KEY_PATH} ]]; then
	echo "Uploading to ${DEVICE_IP}"
	scp -i "${PRIVATE_KEY_PATH}" .dist/"${ZIP_BASE_NAME} ${VERSION}.muxapp" root@"${DEVICE_IP}":/mnt/mmc/ARCHIVE
elif [[ -n ${PASSWORD} ]]; then
	echo "Uploading to ${DEVICE_IP}"
	sshpass -p "${PASSWORD}" scp .dist/"${ZIP_BASE_NAME} ${VERSION}.muxapp" root@"${DEVICE_IP}":/mnt/mmc/ARCHIVE
else
	echo "No --key or --password provided, skipping SCP upload"
	exit 0
fi
