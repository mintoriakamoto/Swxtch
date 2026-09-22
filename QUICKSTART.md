# ⚡ Swxtch Quick Start

**Get boot-verified Wi-Fi privacy in 2 minutes.**

## One Command Installation

```bash
bash install.sh
```

Done! Your 7-day free trial is active. 🎉

---

## What Just Happened

✅ Installed Swxtch package with crypto libraries  
✅ Set up boot-time MAC/IP rotation service  
✅ Started your 7-day free trial (no credit card)  
✅ All 45 tests passing  

---

## Try It Now

### Check Your Trial Status
```bash
swxtch --license
```

Shows how many days remain in your trial.

### Test Interactive Mode
```bash
sudo swxtch --list        # See your Wi-Fi interfaces
sudo swxtch -i wlan0 --interval 1  # Rotate every minute (testing)
```

Keys in interactive mode:
- `r` — Rotate MAC now
- `t` — Toggle on/off
- `+` / `-` — Adjust interval
- `q` — Quit

### Check Boot Service Status
```bash
sudo systemctl status swxtch-boot
```

The boot service automatically rotates your MAC and IP every time you restart.

---

## Next Steps

1. **Understand What It Does**  
   Read `README.md` for the full story

2. **See the Architecture**  
   Look at `SECURITY.md` for cryptographic details

3. **Detailed Setup**  
   Read `INSTALL.md` for OS-specific instructions

4. **Upgrade to Premium**  
   After 7 days: `swxtch --subscribe`  
   Cost: $9.99/month (cancel anytime)

---

## Common Questions

### Does it work offline?
Yes. Swxtch is entirely local — no phone-home, no external verification.

### What if I don't like it?
Uninstall anytime. No long-term commitment.

```bash
pip uninstall swxtch
sudo systemctl disable swxtch-boot
sudo rm -rf /var/log/swxtch
```

### How do I know it's working?
Check the logs:
```bash
sudo journalctl -u swxtch-boot -f    # Live boot logs
sudo tail -f /var/log/swxtch/changes.log  # Rotation history
```

### Can I use it on multiple machines?
Each machine gets its own 7-day trial. Premium subscriptions can cover multiple machines — contact **silasmintori@gmail.com** for details.

### How is my privacy protected?
- MAC addresses → cryptographically hashed (SHA3-256)
- Logs → encrypted with post-quantum algorithm (MLKEM, FIPS 206)
- No external calls → everything stays on your machine
- Open source → audit the code yourself

---

## Installation Troubleshooting

### "Command not found: bash"
Use `/bin/bash install.sh` instead

### "Permission denied"
Make sure the script is executable:
```bash
chmod +x install.sh
bash install.sh
```

### "python3 not found"
Install Python 3.10+:
- **Ubuntu/Debian:** `sudo apt install python3 python3-pip`
- **Fedora/RHEL:** `sudo dnf install python3 python3-pip`
- **Arch:** `sudo pacman -S python python-pip`

### "liboqs installation failed"
That's OK — MLKEM is optional. Swxtch works perfectly with SHA3-256 only.

### "Boot service setup requires root"
The boot service needs sudo. For trial-only (no boot service):
```bash
bash install.sh --trial-only
```

---

## Get Help

- **Issues:** https://github.com/mintoriakamoto/Swxtch/issues
- **Email:** silasmintori@gmail.com
- **Discussion:** See SECURITY.md for threat model and FAQ

---

## Ready?

```bash
swxtch --license      # Check trial status
sudo swxtch -i wlan0  # Test rotation
```

Welcome to Swxtch! 🔒
