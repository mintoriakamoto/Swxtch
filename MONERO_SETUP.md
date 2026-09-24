# 💰 Monero Wallet Setup Guide for Swxtch
## Complete Privacy - Zero Traceability

---

## Why Monero?

**Bitcoin Problem:**
```
Transaction: You → Swxtch wallet
Blockchain shows: Input A → Output B
Analyst traces: Input A = your wallet (via CoinJoin breaking)
Result: Payment linked to you (eventually)
```

**Monero Solution:**
```
Transaction: You → Swxtch wallet  
Blockchain shows: ??????? → ???????
Analyzer sees: Nothing traceable
Result: Payment completely anonymous (mathematically)
```

---

## Option 1: GUI Wallet (Easiest)

### Download Monero GUI Wallet

```bash
# Visit: https://www.monero.project.org/downloads/

# Or install via package manager
apt-get install monero-gui

# macOS
brew install monero-gui

# Windows
# Download from monero.project.org
```

### Step 1: Create Wallet

```
1. Open Monero GUI
2. Click "Create new wallet"
3. Set password (random, strong)
4. Enable "Stagenet" (testnet) for testing OR
   Enable "Mainnet" (real network)
5. Create wallet
```

### Step 2: Write Down Seed Phrase

⚠️ **CRITICAL:**
- Monero gives you 25-word seed phrase
- Write it down on paper ONLY
- Store in safe/vault
- Never store digitally
- This is your only key backup

### Step 3: Generate Receiving Address

```
GUI shows:
- Primary Address (starts with 4 or 8)
- Subaddresses (privacy addresses)

USE SUBADDRESS FOR SWXTCH:
- Each payment gets separate subaddress
- No blockchain link between payments
- Maximum privacy
```

### Step 4: Configure Monero GUI

```
Settings → Daemon:
  - Local node (recommended)
  - OR connect to public node

Settings → Network:
  - Enable Tor (if available)
  - Route through Socks proxy
  - Force Tor connections

Settings → Wallet:
  - View-only wallet (for checking balances)
  - Keep separate from spending wallet
```

---

## Option 2: CLI Wallet (Advanced)

### Install Monero CLI

```bash
# Download
wget https://www.monero.project.org/downloads/monero-linux-x64-v0.18.3.0.tar.bz2
tar xf monero-linux-x64-v0.18.3.0.tar.bz2
cd monero-linux-x64-v0.18.3.0/

# Or via package manager
apt-get install monero
```

### Create Wallet

```bash
# Run wallet daemon
./monero-wallet-cli

# Output:
# Specify wallet name: swxtch
# Specify password: [RANDOM_PASSWORD]
# Creating wallet...
# Generated seed:
# [25 WORDS - SAVE THIS]

# Wallet created!
# Address: 4ABCD...XYZ (55 characters)
```

### Generate Subaddresses

```bash
# In wallet CLI:
> address new

Output:
Address 1: 4ABCD...XYZ (primary)
Address 2: 8ABCD...XYZ (subaddress 1)
Address 3: 8ABCD...XYZ (subaddress 2)

# Use new subaddress for each Swxtch payment
```

### Configure Tor Routing

```bash
# Edit ~/.bitmonero/monero_config.conf

socks-proxy=127.0.0.1:9050
add-peer=piyavjchc4wwn6ov.onion:18080
add-peer=monero.stackwallet.com
enable-dns-blocklist=1
```

### Start Monero Node

```bash
# Terminal 1: Start daemon
./monerod --data-dir ~/.bitmonero \
  --add-peer piyavjchc4wwn6ov.onion:18080 \
  --proxy 127.0.0.1:9050 \
  --tor-socks 127.0.0.1:9050

# Terminal 2: Start wallet
./monero-wallet-cli --daemon-address localhost:18081
```

---

## Option 3: Hardware Wallet (Maximum Security)

### Ledger Device Setup

```bash
# Hardware wallets support Monero
# Ledger Nano S/X

1. Download Ledger Live app
2. Connect Ledger device
3. Install Monero app on device
4. Create new wallet
5. Keys never leave hardware device
6. Use Monero GUI to manage
```

### Advantages:
- ✅ Private keys never touch computer
- ✅ All signing on device
- ✅ Impossible to steal keys
- ✅ Survives malware
- ✅ Physical backup recovery phrase

---

## Option 4: Air-Gapped Wallet (Paranoid Mode)

### Setup:

```bash
# Device 1: OFFLINE (key generation)
# Device 2: ONLINE (transaction broadcasting)

# On Device 1 (isolated):
./monero-wallet-cli --generate-new-wallet air-gapped

# Write seed phrase (physically secure)
# Generate address
# DO NOT CONNECT TO INTERNET

# On Device 2 (connected to Tor):
./monero-wallet-cli --generate-from-view-key

# Input: View-only address from Device 1
# Can see balance (view-only)
# Cannot spend (no spend key)

# To spend:
# 1. Create transaction on Device 2 (unsigned)
# 2. Transfer via USB to Device 1
# 3. Sign on Device 1 (offline)
# 4. Transfer back to Device 2
# 5. Broadcast to network via Tor
```

**Result:** Keys never online, impossible to compromise.

---

## Receive Monero (For Swxtch License)

### Step 1: Get Subaddress

```bash
# GUI: Receive tab shows address
# CLI: address new

Copy subaddress (starts with 8)
Example: 8AbcD...XyZ123...
```

### Step 2: Share Address (Anonymously)

```bash
# GOOD: Share via Tor
curl --proxy socks5://127.0.0.1:9050 https://paste.bin

# GOOD: Share via anonymous messaging
Signal, Session (encrypted)

# BAD: Share via email (links to identity)
# BAD: Share via Discord (IP logged)
# BAD: Post publicly with ID
```

### Step 3: Wait for Payment

```bash
# Monero confirmations: ~2 minutes
# GUI shows incoming transaction
# Shows sender as anonymous (that's the feature!)

Payment received:
- Sender is anonymous
- Amount is private (RingCT)
- No blockchain analyst can trace it
```

### Step 4: Verify Payment Received

```bash
# Check balance in GUI
# Or CLI command:
> balance
Balance: 0.001 XMR

# Transaction is completely untraceable
```

---

## Configure Swxtch for Monero

### Environment Variables

```bash
# Enable Monero support
export PAYMENT_METHOD=monero
export MONERO_RPC_HOST=127.0.0.1:18081
export MONERO_WALLET_RPC=127.0.0.1:18082
export MONERO_TOR_ENABLED=true

# Optional: Custom confirmations
export MONERO_MIN_CONFIRMATIONS=2
export MONERO_WAIT_TIME=120  # seconds

# Batch payments (better privacy)
export BATCH_VERIFY_PAYMENTS=true
export BATCH_DELAY_MIN=300  # 5 minutes
export BATCH_DELAY_MAX=900  # 15 minutes
```

### Start Monero Node

```bash
# Terminal 1: Monero daemon (with Tor)
monerod --data-dir ~/.bitmonero \
  --proxy 127.0.0.1:9050 \
  --add-peer piyavjchc4wwn6ov.onion:18080

# Terminal 2: Wallet RPC server
monero-wallet-rpc \
  --wallet-file swxtch \
  --password [YOUR_PASSWORD] \
  --daemon-address 127.0.0.1:18081 \
  --rpc-bind-ip 127.0.0.1 \
  --rpc-bind-port 18082
```

### Test Monero Payment

```bash
# Generate Monero payment address
swxtch --pay-monero

Output:
₿→ Monero Payment Request
Address: 8AbcD...XyZ123...
Amount: 0.001 XMR (~$0.15 USD)
Confirmations: 2 needed
Wait time: ~2 minutes

Instructions:
1. Send 0.001 XMR to address above
2. Wait for 2 blockchain confirmations
3. Verify: swxtch --check-payment <TXID>
4. License key auto-generated
```

---

## Privacy Best Practices with Monero

### Rule 1: Use New Subaddress Per Payment

```bash
# WRONG: Use same address 5 times
# Links all 5 payments (blockchain analysis)

# RIGHT: Generate new subaddress each time
> address new  (creates fresh 8... address)
> address new  (creates another)
> address new  (creates another)

# Result: 5 payments look unconnected
```

### Rule 2: Add Time Delays

```bash
# WRONG: Buy → Check immediately
# Timing analysis: "Someone bought right now"

# RIGHT: Buy → Wait 1-2 hours → Check
# Delay breaks timing correlation

# Swxtch auto-does this if configured:
export BATCH_DELAY_MIN=1800  # 30 minutes
export BATCH_DELAY_MAX=3600  # 60 minutes
```

### Rule 3: Mix Multiple Wallets

```bash
# WRONG: All purchases from Wallet A
# Someone analyzing: "Same wallet = same person"

# RIGHT: Different wallet per payment
Wallet A: First purchase
Wallet B: Second purchase  
Wallet C: Third purchase

# Result: Looks like 3 different people
```

### Rule 4: Use Tor Always

```bash
# Configuration
export MONERO_TOR_ENABLED=true
export TOR_SOCKS5_HOST=127.0.0.1
export TOR_SOCKS5_PORT=9050

# Start Tor first
tor --socks-port 9050 &

# All Monero communication via Tor
# ISP sees: Connection to Tor (not Monero)
# Tor exit node: Connects to Monero network
# Monero nodes: See Tor exit IP (shared with thousands)
```

### Rule 5: Air-Gap For Maximum Security

```bash
# Device A: Offline (holds private keys)
# Device B: Online (connects to network)

# Spending flow:
Device B: Create unsigned transaction
Device A: Sign with private key
Device B: Broadcast to network

# Private keys NEVER touch online device
# Even if Device B compromised, keys safe
```

---

## Troubleshooting

### Problem: Wallet Won't Sync
```bash
# Solution 1: Use public node
--daemon-address seed.monero.loan:18081

# Solution 2: Add more peers
--add-peer piyavjchc4wwn6ov.onion:18080
--add-peer monero.stackwallet.com

# Solution 3: Resync from scratch
rm -rf ~/.bitmonero/lmdb
# Resync takes ~2 hours
```

### Problem: Tor Connection Slow
```bash
# Solution: Use I2P instead
--add-peer [i2p-address]

# Or both:
--proxy 127.0.0.1:9050       # Tor
--add-peer piyavj...onion:18080  # I2P peer
```

### Problem: Can't Receive Payment
```bash
# Check 1: Address valid
# Monero addresses:
# - Primary: starts with 4 (68 chars)
# - Subaddress: starts with 8 (106 chars)

# Check 2: Node is running
ps aux | grep monerod

# Check 3: Wallet is running
ps aux | grep monero-wallet

# Check 4: Network connectivity
ping 8.8.8.8  # or via Tor: torsocks ping
```

---

## Cost & Economics

### Monero Fees
- **Network fee:** 0.0004 XMR (~0.06¢)
- **Transaction size:** ~2 KB (ring signatures add size)
- **Network throughput:** Lower than Bitcoin (intentional)

### Price Reference (2026)
- 0.001 XMR ≈ $0.15 USD
- 1 XMR ≈ $150 USD
- Volatile (crypto markets)

### Advantage Over Bitcoin
- Bitcoin: 0.001 BTC ≈ $25 USD (expensive)
- Monero: 0.001 XMR ≈ $0.15 USD (affordable)

---

## Legal Status

✅ **Legal in most countries:**
- USA: Legal (but exchanges report purchases)
- EU: Legal (privacy is a right)
- UK: Legal (supported by privacy advocates)
- Canada: Legal

❓ **Regulated:**
- Some exchanges delisting Monero
- Peer-to-peer exchanges still available
- Mining still legal everywhere

⚠️ **No country has banned it**
(Privacy is constitutionally protected in most democracies)

---

## Advanced: Monero Integration API

```python
# For Swxtch Monero support (future)
import requests
import json

class MoneroPaymentHandler:
    def __init__(self, rpc_host="127.0.0.1:18082"):
        self.rpc = f"http://{rpc_host}/json_rpc"
    
    def create_address(self):
        """Create new subaddress for payment"""
        response = requests.post(self.rpc, json={
            "jsonrpc": "2.0",
            "id": "0",
            "method": "create_address",
            "params": {
                "account_index": 0
            }
        })
        result = response.json()["result"]
        return {
            "address": result["address"],
            "subaddress_index": result["address_index"]
        }
    
    def check_payment(self, address, min_amount=0.001):
        """Check if payment received"""
        response = requests.post(self.rpc, json={
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_address_info",
            "params": {
                "address": address
            }
        })
        addr_info = response.json()["result"]
        return {
            "received": addr_info["unlocked_balance"] >= min_amount * 1e12,
            "amount": addr_info["balance"] / 1e12  # Convert from atomic units
        }
    
    def generate_license(self, txid, amount):
        """Generate license after payment confirmed"""
        # Amount is private (RingCT hidden)
        # Can only verify: payment happened
        return {
            "license_key": f"sk_xmr_{secrets.token_urlsafe(44)}",
            "payment_method": "monero",
            "txid": txid,
            "anonymous": True
        }
```

---

## Quick Start Checklist

- [ ] Install Monero GUI or CLI
- [ ] Create wallet
- [ ] Save 25-word seed phrase (physically)
- [ ] Generate subaddress
- [ ] Start Monero daemon (with Tor)
- [ ] Configure Swxtch for Monero
- [ ] Send 0.001 XMR to Swxtch address
- [ ] Wait 2 confirmations (~2 min)
- [ ] Verify payment: `swxtch --check-payment`
- [ ] Receive license key (instant)
- [ ] Activate license: `swxtch --activate sk_xmr_...`
- [ ] Enjoy completely anonymous Swxtch

---

## Summary

**Monero = Bitcoin but private:**
- ✅ Sender anonymous (ring signatures)
- ✅ Receiver anonymous (stealth addresses)
- ✅ Amount hidden (RingCT)
- ✅ No blockchain analysis possible
- ✅ Cheaper than Bitcoin
- ✅ Faster confirmations
- ✅ Private by default (not optional)

**Result:** Payment completely untraceable, even to governments.

---

**Last Updated:** 2026-09-23  
**Version:** 1.0 - Monero Setup Guide  
**Status:** Ready for implementation
