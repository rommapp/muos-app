set dotenv-load

alias b := build
alias c := clean
alias p := upload

default: clean build upload

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
	mkdir -p .dist

	rsync -a --exclude={__pycache__,.venv,.env,.DS_Store,.build,.dist} RomM/ .build/RomM/
	
	# Platform-independent approach
	sed "s/<version>/{{ version }}/" .build/RomM/__version__.py > .build/RomM/__version__.py.new
	mv .build/RomM/__version__.py.new .build/RomM/__version__.py

	(cd .build && zip -r "../{{ base_name }} {{ version }}.muxapp" ./*)

	mv "{{ base_name }} {{ version }}.muxapp" .dist/"{{ base_name }} {{ version }}.muxapp"

upload:
	@echo "Uploading..."
	@echo "DEVICE_IP_ADDRESS=$DEVICE_IP_ADDRESS"
	@echo "PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH"
	@echo "SSH_PASSWORD=****"

	DEVICE_IP_ADDRESS=$DEVICE_IP_ADDRESS
	PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH
	SSH_PASSWORD=$SSH_PASSWORD

	if [[ -z $DEVICE_IP_ADDRESS ]]; then echo "Cannot upload: no DEVICE_IP_ADDRESS set in environment"; exit 1; fi
	if [[ -z $PRIVATE_KEY_PATH ]] && [[ -z $SSH_PASSWORD ]]; then echo "Cannot upload: no PRIVATE_KEY_PATH or SSH_PASSWORD set in environment"; exit 1; fi
	if [[ -n $PRIVATE_KEY_PATH ]]; then scp -i "$PRIVATE_KEY_PATH" .dist/"{{ base_name }} {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE; echo "Upload successful"; exit 0; fi
	if [[ -n $SSH_PASSWORD ]]; then sshpass -p "$SSH_PASSWORD" scp .dist/"{{ base_name }} {{ version }}.muxapp" root@"${DEVICE_IP_ADDRESS}":/mnt/mmc/ARCHIVE; echo "Upload successful"; exit 0; fi
	