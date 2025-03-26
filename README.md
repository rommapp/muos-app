<!-- trunk-ignore-all(markdownlint/MD033) -->
<!-- trunk-ignore(markdownlint/MD041) -->
<div align="center">

  <img src=".github/resources/isotipo.png" height="180px" width="auto" alt="romm-muos logo">
    <h3 style="font-size: 25px;">
    A beautiful, powerful, RomM app for muOS.
  </h3>

<br>

[![license-badge-img]][license-badge]
[![release-badge-img]][release-badge]
[![discord-badge-img]][discord-badge]

<!-- [![wiki-badge-img]][wiki] -->

  </div>
</div>

# Overview

A [muOS](https://muos.dev/) app that connects to your RomM instance and allows you to fetch games wirelessly from your Anbernic device.

## Screenshots

<div>
  <img src=".github/resources/platforms.png" height="300px" width="auto" alt="muos app platforms list">
  <img src=".github/resources/gamelist.png" height="300px" width="auto" alt="muos app game list">
</div>

## Installation

We leverate the muOS [Archive Manager](https://muos.dev/help/archive) to install/update the app.

1. Head to the [latest release](https://github.com/rommapp/muos-app/releases/latest) and download the `romm_muOS_install_x.x.x.zip` file.
2. Move the **compressed** ZIP file to `/mnt/mmc/ARCHIVE` on your device.
3. Launch the manager from `Applications > Archive Manager` and select `romm_muOS_install_x.x.x.zip`.
4. Once installed, make a copy of `/mnt/mmc/MUOS/application/RomM/env.template`, rename it to `/mnt/mmc/MUOS/application/RomM/.env`, edit it (any method is fine, we recommend SSH) and set `HOST`, `USERNAME` and `PASSWORD`.
5. Launch the app from `Applications > RomM` and start browsing your collection.

## Support

> [!NOTE]
> Your device must connect to your RomM instance or home server over Wi-Fi. The easiest method is to keep them on the same network and set HOST to the server's IP and the port where RomM is running. Advanced users or those using reverse proxies can configure their network and DNS settings as needed, using a URL with a domain like `https://romm.domain.com`.

If you have any issues with the app, please [open an issue](https://github.com/rommapp/muos-app/issues/new) in this repository. If the issue is with RomM itself, open an issue in the [RomM repository](https://github.com/rommapp/romm/issues/new/choose).

Join us on Discord, where you can ask questions, submit ideas, get help, showcase your collection, and discuss RomM with other users. You can also find our team is the [muOS Discord](https://discord.com/invite/muos).

[![discord-invite]][discord-invite-url]

<!-- Badges -->

[license-badge-img]: https://img.shields.io/github/license/rommapp/muos-app?style=for-the-badge&color=a32d2a
[license-badge]: LICENSE
[release-badge-img]: https://img.shields.io/github/v/release/rommapp/muos-app?style=for-the-badge
[release-badge]: https://github.com/rommapp/muos-app/releases
[discord-badge-img]: https://img.shields.io/badge/discord-7289da?style=for-the-badge
[discord-badge]: https://discord.gg/P5HtHnhUDH

<!-- Links -->

[discord-invite]: https://invidget.switchblade.xyz/P5HtHnhUDH
[discord-invite-url]: https://discord.gg/P5HtHnhUDH
