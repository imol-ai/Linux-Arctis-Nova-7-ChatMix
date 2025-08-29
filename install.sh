#!/usr/bin/env bash

if [[ "$USER" == root ]]; then
    echo "Please run the install script as non-root user."
    exit 1
fi

CONFIG_DIR="system-config/"
SYSTEMD_CONFIG="arctisn7chatmix.service"
UDEV_CONFIG="91-steelseries-arctis-nova-7.rules"
SCRIPT="arctis_nova_7_chatmix.py"

SCRIPT_DIR="$HOME/.local/bin/"
SYSTEMD_DIR="$HOME/.config/systemd/user/"
UDEV_DIR="/etc/udev/rules.d/"

function cleanup {
    echo
    echo "Cleaning up:"
    sudo rm -vf "${UDEV_DIR}${UDEV_CONFIG}"
    rm -vf "${SCRIPT_DIR}${SCRIPT}"
    rm -vf "${SYSTEMD_DIR}${SYSTEMD_CONFIG}"
    systemctl --user disable --now "$SYSTEMD_CONFIG"
}

if [[ -v UNINSTALL ]]; then
    echo "Uninstalling Arctis Nova 7 ChatMix."
    cleanup ; exit 0
fi

echo "Installing Arctis Nova 7 ChatMix."
echo "Installing script to ${SCRIPT_DIR}${SCRIPT}."
if [[ ! -d "$SCRIPT_DIR" ]]; then
    mkdir -vp $SCRIPT_DIR || \
        { echo "FATAL: Failed to create $SCRIPT_DIR" ; cleanup ; exit 1;}
fi
cp "$SCRIPT" "$SCRIPT_DIR"

echo
echo "Installing udev rule to ${UDEV_DIR}${UDEV_CONFIG}."
envsubst < "${CONFIG_DIR}${UDEV_CONFIG}" > "$UDEV_CONFIG"
sudo cp "$UDEV_CONFIG" "$UDEV_DIR" || \
    { echo "FATAL: Failed to copy $UDEV_CONFIG" ; cleanup ; exit 1;}
sudo udevadm control --reload
rm -f "$UDEV_CONFIG"

echo
echo "Installing systemd unit to ${SYSTEMD_DIR}${SYSTEMD_CONFIG}."
if [[ ! -d "$SYSTEMD_DIR" ]]; then
    mkdir -vp $SYSTEMD_DIR || \
        { echo "FATAL: Failed to create $SCRIPT_DIR" ; cleanup ; exit 1;}
fi
cp "${CONFIG_DIR}${SYSTEMD_CONFIG}" "$SYSTEMD_DIR"

echo
echo "Enabling systemd unit $SYSTEMD_CONFIG."
systemctl --user enable --now "$SYSTEMD_CONFIG" 2>/dev/null
