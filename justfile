set dotenv-load

alias c := clean
alias b := build
alias z := zip
alias p := upload

default: clean build upload
muxapp: clean build zip upload-app

clean:
	@echo "Cleaning..."
	rm -rf .build
	rm -rf .dist

base_name := "RomM Installer"
version := `
	bash -c 'VERSION=$(grep -o "\"[^\"]*\"" RomM/__version__.py | tr -d "\"")
	if [[ ${VERSION} == "<version>" ]]; then
		VERSION=$(git rev-parse --abbrev-ref HEAD)
	fi
	VERSION=${VERSION//\//_}
	echo ${VERSION}'
`

build:
	@echo "Building..."

	mkdir -p .build
	rsync -a --exclude={__pycache__,.venv,.env,.DS_Store,.build,.dist} RomM/ .build/RomM/

	# Platform-independent approach
	sed "s/<version>/{{ version }}/" .build/RomM/__version__.py > .build/RomM/__version__.py.new
	mv .build/RomM/__version__.py.new .build/RomM/__version__.py

	@echo "Copying Python dependencies..."

	uv pip freeze > .build/requirements.txt
	pip install --no-cache-dir --platform manylinux_2_28_aarch64 --only-binary=:all: --implementation cp -r .build/requirements.txt --upgrade --target=.build/RomM/deps
	rm .build/requirements.txt

	# Move pillow libs to the right place
	mv .build/RomM/deps/pillow.libs .build/RomM/libs

	# Remove unnecessary files
	find .build/RomM/deps -name "*.dist-info" -type d -exec rm -rf {} \; 2>/dev/null || true
	find .build/RomM/deps -name "*__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
	rm -r .build/RomM/deps/pip
	rm -r .build/RomM/deps/sdl2/examples 
	rm -r .build/RomM/deps/sdl2/test

zip:
	mkdir -p .dist
	zip -r "{{ base_name }} {{ version }}.muxapp" ./.build/*
	mv "{{ base_name }} {{ version }}.muxapp" .dist/"{{ base_name }} {{ version }}.muxapp"

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
    if [[ -n $PRIVATE_KEY_PATH ]]; then rsync -avz --no-owner --no-group -e "ssh -i \"$PRIVATE_KEY_PATH\"" .dist/"{{ base_name }} {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE/; echo "Upload successful"; exit 0; fi
    if [[ -n $SSH_PASSWORD ]]; then sshpass -p "$SSH_PASSWORD" rsync -avz --no-owner --no-group -e ssh  .dist/"{{ base_name }} {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE/; echo "Upload successful"; exit 0; fi
