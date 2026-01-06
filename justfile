set dotenv-load

default: clean copy build-dev upload
update: copy upload-update
release: clean copy build-prod muxapp portmaster

clean:
	@echo "Cleaning..."
	rm -rf .build
	rm -rf .dist

version := `
	bash -c 'VERSION=$(grep -o "\"[^\"]*\"" RomM/__version__.py | tr -d "\"")
	if [[ ${VERSION} == "<version>" ]]; then
		VERSION=$(git rev-parse --abbrev-ref HEAD)
	fi
	VERSION=${VERSION//\//_}
	echo ${VERSION}'
`

copy:
	@echo "Copying files..."

	mkdir -p .build
	rsync -a --exclude={__pycache__,.venv,.env,.DS_Store,.build,.dist} RomM/ .build/RomM/

	# Platform-independent approach
	sed "s/<version>/{{ version }}/" .build/RomM/__version__.py > .build/RomM/__version__.py.new
	mv .build/RomM/__version__.py.new .build/RomM/__version__.py

build-dev:
	@echo "Building..."

	uv pip freeze > .build/requirements.txt
	pip install --no-cache-dir --platform manylinux_2_28_aarch64 --only-binary=:all: --implementation cp -r .build/requirements.txt --upgrade --target=.build/RomM/deps
	rm .build/requirements.txt

	mv .build/RomM/deps/pillow.libs .build/RomM/libs
	just cleanup

build-prod:
	#!/usr/bin/env bash
	set -euxo pipefail
	echo "Building..."

	uv venv
	. .venv/bin/activate
	uv python install
	uv sync --all-extras --dev
	uv pip freeze > .build/requirements.txt

	pip install --no-cache-dir --platform manylinux_2_28_aarch64 --only-binary=:all: --implementation cp -r .build/requirements.txt --upgrade --target=.build/RomM/deps
	rm .build/requirements.txt

	mv .build/RomM/deps/pillow.libs .build/RomM/libs
	just cleanup

cleanup:
	# Remove unnecessary files
	@echo "Cleaning up..."
	find .build/RomM/deps -name "*.dist-info" -type d -exec rm -rf {} \; 2>/dev/null || true
	find .build/RomM/deps -name "*__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
	rm -r .build/RomM/deps/pip
	rm -r .build/RomM/deps/sdl2/examples 
	rm -r .build/RomM/deps/sdl2/test

muxapp:
	mkdir -p .dist
	cd .build && zip -r "../RomM muOS {{ version }}.muxapp" ./RomM
	mv "RomM muOS {{ version }}.muxapp" .dist/"RomM.muOS.{{ version }}.muxapp"

portmaster:
	mkdir -p .dist
	cp "RomM App.sh" ./.build
	cd .build && zip -r "../RomM PortMaster {{ version }}.zip" .
	mv "RomM PortMaster {{ version }}.zip" .dist/"RomM.PortMaster.{{ version }}.zip"

connect:
	@echo "Uploading files..."
	@echo "DEVICE_IP_ADDRESS=$DEVICE_IP_ADDRESS"
	@echo "PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH"
	@echo "SSH_PASSWORD=****"

	DEVICE_IP_ADDRESS=$DEVICE_IP_ADDRESS
	PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH
	SSH_PASSWORD=$SSH_PASSWORD

	if [[ -z $DEVICE_IP_ADDRESS ]]; then echo "Cannot upload: no DEVICE_IP_ADDRESS set in environment"; exit 1; fi
	if [[ -z $PRIVATE_KEY_PATH ]] && [[ -z $SSH_PASSWORD ]]; then echo "Cannot upload: no PRIVATE_KEY_PATH or SSH_PASSWORD set in environment"; exit 1; fi

upload:
    just connect
    if [[ -n $PRIVATE_KEY_PATH ]]; then rsync -avz --no-owner --no-group -e "ssh -i \"$PRIVATE_KEY_PATH\"" .build/RomM root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/MUOS/application/; echo "Upload successful"; exit 0; fi
    if [[ -n $SSH_PASSWORD ]]; then sshpass -p "$SSH_PASSWORD" rsync -avz --no-owner --no-group -e ssh .build/RomM root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/MUOS/application/; echo "Upload successful"; exit 0; fi

upload-app:
    just connect
    if [[ -n $PRIVATE_KEY_PATH ]]; then rsync -avz --no-owner --no-group -e "ssh -i \"$PRIVATE_KEY_PATH\"" .dist/"RomM muOS {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE/; echo "Upload successful"; exit 0; fi
    if [[ -n $SSH_PASSWORD ]]; then sshpass -p "$SSH_PASSWORD" rsync -avz --no-owner --no-group -e ssh  .dist/"RomM muOS {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE/; echo "Upload successful"; exit 0; fi

upload-update:
    just connect
    if [[ -n $PRIVATE_KEY_PATH ]]; then rsync -avz --no-owner --no-group --exclude 'deps/*' --exclude 'libs/*' -e "ssh -i \"$PRIVATE_KEY_PATH\"" .build/RomM root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/MUOS/application/; echo "Upload successful"; exit 0; fi
    if [[ -n $SSH_PASSWORD ]]; then sshpass -p "$SSH_PASSWORD" rsync -avz --no-owner --no-group --exclude 'deps/*' --exclude 'libs/*' -e ssh .build/RomM root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/MUOS/application/; echo "Upload successful"; exit 0; fi
