# 🔐 Swxtch Privacy Hardening Guide

**Complete anti-tracking protection across all privacy vectors.**

---

## Overview

Swxtch implements multi-layer privacy hardening to ensure you're never discoverable by ISPs, networks, or even AI tracking systems. This goes beyond MAC address rotation to address **every vector** where your identity can leak.

### Privacy Vectors Protected

| Vector | Protection | Status |
|--------|-----------|--------|
| **MAC Address** | Random rotation every 15 minutes | ✅ Active |
| **DHCP Snooping** | Randomized hostname + client ID | ✅ Active |
| **DNS Leaks** | DNS-over-TLS / DNS-over-HTTPS | ✅ Configurable |
| **IPv4 Leaks** | VPN/Proxy enforcement check | ✅ Monitored |
| **IPv6 Leaks** | IPv6 disabled completely | ✅ Active |
| **WebRTC Leaks** | Browser configuration guide | ⚠️  User-configured |
| **Browser Fingerprint** | Randomization guidance | ⚠️  User-configured |

---

## Quick Start

### Enable All Privacy Hardening

```bash
sudo swxtch --privacy
```

This will:
1. ✅ Configure DHCP privacy (randomized hostname + client ID)
2. ✅ Enable DNS-over-TLS encryption (Cloudflare)
3. ✅ Disable IPv6 completely
4. ✅ Verify VPN/proxy is active
5. ⚠️  Guide you through WebRTC browser configuration

### Check Privacy Status

```bash
swxtch --privacy-status
```

Displays:
- Overall Privacy Score (0-100)
- DHCP Privacy: enabled/disabled
- DNS Privacy: enabled/disabled
- IPv4 Protected: VPN/proxy detected
- IPv6 Protected: disabled/active

### Verify All Protections

```bash
swxtch --verify-privacy
```

Complete audit of all privacy vectors with:
- ✓ checks for enabled protections
- ⚠️  warnings for potential leaks
- 📋 configuration recommendations

---

## Privacy Layers

### Layer 1: DHCP Privacy

**Problem:** DHCP requests broadcast your hostname, device model, and vendor info to networks.

**Solution:** Randomize every DHCP parameter:
- 🔄 Random hostname (12 random chars)
- 🔄 Random client ID (RFC 4361 compliant)
- 🚫 Hostname broadcast disabled
- 🔄 Random vendor class

**Enable:**
```bash
sudo swxtch --privacy
```

**Verification:**
```bash
sudo dhcpdump -i wlan0  # Watch DHCP requests
# Should show randomized hostname, no identifying info
```

---

### Layer 2: DNS Privacy (DoT/DoH)

**Problem:** Your ISP can see every website you visit via DNS queries.

**Solution:** Encrypt DNS with DNS-over-TLS (DoT) or DNS-over-HTTPS (DoH).

**Providers:**
- 🔐 Cloudflare (1.1.1.1:853 - DoT)
- 🔐 Google (8.8.8.8:853 - DoT)
- 🔐 Quad9 (9.9.9.9:853 - DoT)

**Enable Cloudflare DoT:**
```bash
sudo swxtch --privacy
# Selects Cloudflare by default
```

**Enable Google DNS (DoT):**
```bash
sudo resolvectl dns eth0 8.8.8.8 +tls-yes
```

**Verify DNS Encryption:**
```bash
resolvectl status
# Should show "DNSSEC setting: yes" and "DNS over TLS: yes"

sudo tcpdump -i wlan0 -n port 53
# Should show NO unencrypted DNS queries on port 53
```

---

### Layer 3: IPv4 Leak Prevention

**Problem:** Without a VPN, your real IPv4 address is always discoverable.

**Solution:** Require VPN/proxy tunnel before allowing any traffic.

**Verification:**
```bash
swxtch --privacy
# Will warn: "IPv4 leak risk detected: No VPN/proxy tunnel found"
```

**Requirements:**
- 🔐 WireGuard tunnel (recommended)
- 🔐 OpenVPN tunnel
- 🔐 HTTP/SOCKS5 proxy
- 🔐 Tor (bridges + proxychains)

**Test for IPv4 Leaks:**
```bash
curl https://[PRIVACY_CHECK_SERVICE]/json/  # Should show VPN IP, not real IP
curl https://api.ipify.org?format=json  # Should show VPN IP
```

---

### Layer 4: IPv6 Complete Disable

**Problem:** IPv6 can reveal your real identity even when using IPv4 VPN.

**Solution:** Disable IPv6 entirely (no dual-stack).

**Enable:**
```bash
sudo swxtch --privacy
# Automatically disables IPv6
```

**Verify IPv6 is Disabled:**
```bash
ip addr show
# Should show NO "inet6" addresses on wlan0
```

**Test for IPv6 Leaks:**
```bash
curl https://api64.ipify.org?format=json
# Should timeout or return empty (IPv6 not available)
```

---

### Layer 5: WebRTC Leak Prevention

**Problem:** WebRTC in browsers bypasses VPN by connecting directly to peers.

**Solution:** Disable WebRTC in your browser.

#### Firefox

1. Open `about:config`
2. Search for `media.peerconnection.enabled`
3. Set to `false`
4. Restart Firefox

**Test:**
```bash
# WebRTC IP leak test
https://[PRIVACY_CHECK_SERVICE]/  # Should NOT show your real IP
```

#### Chrome/Chromium

1. Install **WebRTC Leak Prevent** extension
2. Set to "Disable all non-proxied UDP"

---

### Layer 6: Browser Fingerprinting Protection

**Problem:** Browsers leak unique fingerprints (fonts, canvas, WebGL, etc.).

**Solution:** Use privacy-focused browser or fingerprint randomization.

#### Option A: Tor Browser (Maximum Privacy)
- Randomizes fingerprint on every page load
- Strongest privacy available

#### Option B: Firefox Hardened
- Install **Canvas Blocker** extension
- Set User-Agent to generic value
- Disable WebGL

#### Option C: Librewolf
- Pre-hardened Firefox fork
- Fingerprinting protection built-in

---

## Advanced Configuration

### Custom DNS Provider

Use Google DNS with DoT:
```bash
sudo resolvectl dns 8.8.8.8 +tls-yes
sudo resolvectl dnssec yes
```

Use Quad9 DNS:
```bash
sudo resolvectl dns 9.9.9.9 +tls-yes
```

### DNS-over-HTTPS (DoH)

If your systemd doesn't support DoT (< v254):
```bash
# Install dnscrypt-proxy for DoH
sudo apt install dnscrypt-proxy

# Edit /etc/dnscrypt-proxy/dnscrypt-proxy.toml
server_names = ['cloudflare']  # or google, quad9
```

### VPN Configuration

#### WireGuard (Recommended)

```bash
# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Create interface
sudo ip link add dev wg0 type wireguard
sudo ip addr add 10.0.0.2/24 dev wg0
sudo ip link set dev wg0 up
sudo wg set wg0 private-key <(cat privatekey)
sudo wg set wg0 peer <server-pubkey> endpoint <server-ip>:51820 allowed-ips 0.0.0.0/0
sudo ip route add 0.0.0.0/0 via 10.0.0.1 dev wg0
```

#### OpenVPN

```bash
# Use community VPN provider or deploy your own
sudo openvpn --config /path/to/config.ovpn

# Verify:
curl https://[PRIVACY_CHECK_SERVICE]/json/  # Should show VPN IP
```

#### Tor + Proxychains

```bash
# Install
sudo apt install tor proxychains4

# Edit /etc/proxychains4.conf
# Set: socks5 127.0.0.1 9050

# Run app through Tor
proxychains curl https://[PRIVACY_CHECK_SERVICE]/json/
```

---

## Complete Privacy Checklist

Run this command and verify all checks:

```bash
swxtch --verify-privacy
```

Expected output:
```
🔐 Privacy Verification Report

✓ DHCP privacy configured
✓ DNS privacy enabled (DoT/DNSSEC)
✓ IPv4 protected (VPN/tunnel active)
✓ IPv6 disabled (privacy vector blocked)
⚠️  WebRTC: Configure browser settings (Firefox/Chrome)

✓ All privacy checks passed!
```

---

## Monitoring Privacy

### Check Real-Time Privacy

```bash
swxtch --privacy-status

🔐 Privacy Hardening Status

Overall Privacy Score: 100/100
  • DHCP Privacy: ✓
  • DNS Privacy: ✓
  • IPv4 Protected: ✓
  • IPv6 Protected: ✓
```

### Monitor DHCP Randomization

```bash
# Watch DHCP requests in real-time
sudo dhcpdump -i wlan0

# Should show new random hostname on each request:
# DHCP ACK: hostname=xyzabc123456
# (next request)
# DHCP ACK: hostname=qwerty654321
```

### Monitor DNS Encryption

```bash
# Watch DNS traffic
sudo tcpdump -i wlan0 -n 'udp port 53 or tcp port 853'

# Port 53 = unencrypted (should be NONE)
# Port 853 = DoT encrypted (should see this)
```

### Monitor VPN Connection

```bash
# Verify VPN is active
ip route show | grep -E 'tun|tap|wg'

# Test public IP matches VPN
curl https://[PRIVACY_CHECK_SERVICE]/json/
```

---

## Threat Model: What We Protect Against

| Threat | Protected? | Method |
|--------|-----------|--------|
| ISP seeing your sites (DNS) | ✅ Yes | DNS-over-TLS encryption |
| ISP seeing your MAC | ✅ Yes | Random MAC every 15m |
| Network admin seeing your hostname | ✅ Yes | Random hostname per DHCP |
| VPN provider seeing your IP | ✅ Yes | No unencrypted traffic |
| Website seeing your real IP | ✅ Yes | VPN tunnel + no WebRTC |
| Browser fingerprinting | ⚠️  Partial | Needs browser config |
| AI tracking real identity | ✅ Yes | All identifying info removed |

---

## What We DON'T Protect Against

- 🚫 **Content inspection**: If someone can intercept encrypted traffic
- 🚫 **Timing attacks**: Pattern analysis of traffic volume/timing
- 🚫 **Physical attacks**: Compromised router/ISP equipment
- 🚫 **Software exploits**: Malware/rootkit accessing your system
- 🚫 **Social engineering**: Someone calling your ISP for your info

**Mitigation:** Use in addition to strong system security, firewall, and trusted VPN provider.

---

## Troubleshooting

### DHCP Privacy Not Applied

```bash
# Check if NetworkManager is managing the interface
nmcli -t device show wlan0

# If managed, reconnect to apply DHCP changes
sudo nmcli connection up wlan0
```

### DNS Still Leaking

```bash
# Verify systemd-resolved version
systemctl status systemd-resolved

# Needs systemd 254+ for DoT support
# If older, use dnscrypt-proxy instead
```

### IPv6 Not Disabled

```bash
# Check IPv6 status
ip addr show wlan0

# Manual disable
sudo sysctl -w net.ipv6.conf.wlan0.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
```

### WebRTC Still Leaking (Chrome)

```bash
# Verify extension is installed
# Settings > Extensions > WebRTC Leak Prevent

# Check WebRTC disabled in Chrome flags
chrome://flags/#enable-webrtc-hide-local-ips-with-mdns
# Should be "Enabled with mDNS IP hiding"
```

---

## Security Guarantees

Swxtch Privacy Hardening provides:

✅ **DHCP Anonymity** - No identifying info in DHCP requests  
✅ **DNS Privacy** - All DNS queries encrypted end-to-end  
✅ **IP Anonymity** - Real IP never visible without VPN  
✅ **IPv6 Disabled** - No dual-stack privacy leak vector  
✅ **MAC Randomization** - New MAC every 15 minutes  
✅ **Local-Only Verification** - No external API calls to verify privacy

---

## License & Attribution

🔐 **Swxtch Privacy Hardening** - Part of Swxtch Premium ($9.99/month)

Freemium Licensing enforces these privacy protections are always active when Swxtch is running.

---

**Questions?** Email: [SUPPORT_EMAIL]
