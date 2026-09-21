# Swxtch

A standing terminal window that rotates your Wi-Fi MAC address on a schedule —
Linux's answer to iOS/macOS's "Private Wi-Fi Address: Rotating" setting.

It periodically replaces your Wi-Fi adapter's MAC address with a random,
locally-administered address (same bit trick Apple uses), so nearby networks
and devices can't track you by a fixed hardware address. Runs as a live TUI
in its own terminal window so you can see the current address and rotation
status at a glance.

## How it works

- Reads Wi-Fi interfaces from `/sys/class/net/*/wireless` (or `phy80211`).
- Generates a random MAC with the locally-administered bit set and the
  multicast bit cleared, so it never collides with a real vendor OUI.
- Applies it with `ip link set dev <iface> address <mac>` (bringing the
  interface down/up, and coordinating with NetworkManager via `nmcli` if the
  device is NM-managed) so Wi-Fi reconnects cleanly under the new address.
- A background thread rotates on an interval; the TUI shows current MAC,
  original MAC, interval, and time since last rotation — the same fields
  as the iOS panel.

## Requirements

- Linux, Python 3.10+
- `iproute2` (`ip`) — present on virtually every distro
- Root privileges (changing a MAC address requires `CAP_NET_ADMIN`)
- Optional: `nmcli` if you use NetworkManager (Swxtch coordinates with it
  automatically), and a terminal emulator (gnome-terminal, konsole, xterm,
  alacritty, kitty, ...) if you want `--window` to pop open a new window

## Install

```sh
pip install .
```

This installs the `swxtch` command.

## Usage

### Interactive TUI (Manual)

```sh
# Auto-detect your Wi-Fi interface, rotate every 15 minutes, run here
sudo swxtch

# Pick an interface explicitly and rotate every 5 minutes
sudo swxtch -i wlan0 --interval 5

# Pop the live view open in its own terminal window
sudo swxtch --window

# List detected Wi-Fi interfaces
swxtch --list
```

### Automatic on Boot (Systemd Service with FIPS 206)

Install to rotate MAC and IP automatically every time the system boots:

```sh
# Install with cryptographic verification support
pip install -e ".[crypto]"

# Set up systemd service
sudo bash ./install-boot-service.sh

# Enable and start
sudo systemctl enable swxtch-boot
sudo systemctl start swxtch-boot
```

Each boot will:
- Generate new random MAC address
- Renew DHCP lease for new IP
- Verify changes with SHA3-256 hashing
- Encrypt records with MLKEM (FIPS 206)
- Log to `/var/log/swxtch/changes.log`

See [BOOT-SERVICE.md](BOOT-SERVICE.md) for details.

### Keys inside the TUI

| Key | Action |
| --- | --- |
| `r` | Rotate the MAC address now |
| `t` | Toggle rotating on/off |
| `+` / `-` | Increase / decrease the rotation interval by 1 minute |
| `q` | Quit (leaves the current random address in place) |

## Notes

- Changing a MAC address briefly drops the Wi-Fi link while the interface
  cycles down/up, exactly like the iOS/macOS equivalent does when it rotates.
- Some Wi-Fi chipsets/drivers don't support changing the MAC on the fly;
  if `ip link set address` fails, Swxtch surfaces the error in the TUI
  instead of silently doing nothing.
- Swxtch only randomizes the hardware address — it does not change your IP
  address, route your traffic, or provide anonymity beyond link-layer
  tracking resistance.
