# Linux-Arctis-Nova-7-ChatMix

## Overview
<br>
The SteelSeries Arctis series of headsets include a hardware modulation knob for 'chatmix' on the headset.
This allows the user to 'mix' the volume of two different devices on their system, named "Game" and "Chat".

On older Arctis models (e.g. Arctis 7), the headset would be detected as two individual hardware devices by
the host operating system and would assign them as such accordingly, allowing the user to specify which device to
use and where.

**Typical use case:** "Chat" for voicechat in games and VOIP/comms software, and "Game" for system / music etc.

On the Arctis Nova 7 model, this two-device differentiation no longer exists, and the host OS will only recognize a single device.
If the user wishes to utilize the chatmix modulation knob, they *must* install the SteelSeries proprietary GG software. This
software does not currently support Linux.

This script provides a basic workaround for this problem for Linux users. It creates a Virtual Audio Cable (VAC) pair called "Arctis_Chat"
and "Arctis_Game" respectively, which the user can then assign accordingly as they would have done with an older Arctis model.
The script listens to the headset's USB dongle signals and interprets them in a way that can be meaningfully converted
to adjust the audio when the user moves the dial on the headset.

## Requirements
<br>

The service itself depends on the `hidapi` python package.

In order for the VAC to be initialized and for the volumes to be controlled, the system requires **Pipewire** (and the underlying **PulseAudio**)
which are both fairly common on modern Linux systems out of the box.

<br>

## Installation
<br>

Python 3 & python-hidapi required.

Run `install.sh` as your desktop user in the project root directory. You may need to provide your `sudo` password during installation for copying the udev rule for your device.

**DISCONNECT DEVICE BEFORE INSTALLING**

To uninstall, set the `UNINSTALL` environment variable while calling the install script, e.g.,

```bash
UNINSTALL= ./install.sh
```

**RECONNECT DEVICE ONCE INSTALL IS COMPLETE**

There may be a short delay before the device becomes available after reconnecting. Use `systemctl --user status arctisn7chatmix.service` to check the service
is running properly.

<br>

# Acknowledgements

Thanks to all the previous forks and their maintainers.
