# Contributing to RomM muOS app

Thank you for considering contributing to RomM muOS app! This document outlines some guidelines to help you get started with your contributions.

**If you're looking to implement a large feature or make significant changes to the project, it's best to open an issue first AND join the Discord to discuss your ideas with the maintainers.**

## Code of Conduct

Please note that this project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating in this project, you are expected to uphold this code.

## Contributing to the Docs

If you would like to contribute to the project's [documentation](https://docs.romm.app/latest/Integrations/muOS-app/), open a pull request against [the docs repo](https://github.com/rommapp/docs). We welcome any contributions that help improve the documentation (new pages, updates, or corrections).

## How to Contribute Code

We use `uv` to manage python dependencies, install it with:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

And activate it:

```sh
uv venv
source .venv/bin/activate
```

Then install python and the required dependencies:

```sh
uv python install
uv sync --all-extras --dev
```

To build the app, you'll need to [install `just`](https://github.com/casey/just?tab=readme-ov-file#packages), then run:

```sh
just build
```

Just can also push the app to your device, but you need to set up an `.env` file with your device's IP and SSH credentials. Create a file called `.env` in the root of the project and add the following:

```env
DEVICE_IP_ADDRESS=
PRIVATE_KEY_PATH=
SSH_PASSWORD=
```

Then run `just`, which will clean, build and push the app to your device.

## Pull Request Guidelines

- Make sure your code follows the project's coding standards.
- Test your changes locally before opening a pull request.
- Update the documentation if necessary.
- Ensure all existing tests pass, and add new tests for new functionality.
- Use clear and descriptive titles and descriptions for your pull requests.

## Code Style

Follow the existing code style used throughout the project. If working with VSCode or a similar editor, consider installing these extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)

## Issue Reporting

If you encounter any bugs or have suggestions for improvements, please [create an issue](https://github.com/rommapp/muos-app/issues) on GitHub. Provide as much detail as possible, including steps to reproduce the issue if applicable.

## Licensing

By contributing to RomM muOS app, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE).

---

Thank you for contributing to RomM muOS app! Your help is greatly appreciated.
