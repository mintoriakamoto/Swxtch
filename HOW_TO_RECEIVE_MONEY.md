# HOW TO RECEIVE MONEY (Complete Guide)

**As the Payment Receiver - From Setup to Payment**

---

## Quick Summary

You set up your wallet address in SWXTCH → Customers send money to that address → Payment appears in your wallet → You own it completely and can spend anytime.

---

## Step 1: Set Your Wallet Address

### Bitcoin Wallet Setup

```bash
# Get your Bitcoin receive address (from your wallet)
# Example: bc1qnq7sh0v2u7kzqpacld0c7wl3sytjlu...

# Set it in SWXTCH
export SWXTCH_BITCOIN_WALLET="bc1qnq7sh0v2u7kzqpacld0c7wl3sytjlu..."
```

### Monero Wallet Setup

```bash
# Get your Monero primary address (from your wallet)
# Example: 8AbcD...XyZ123...

# Set it in SWXTCH
export SWXTCH_MONERO_WALLET="8AbcD...XyZ123..."
```

---

## Step 2: Start SWXTCH Payment Server

```bash
# Terminal 1: Start Tor (required for anonymity)
tor --socks-port 9050 &

# Terminal 2: Start SWXTCH
python -m swxtch --server

# Output shows:
# ✓ Bitcoin wallet configured
# ✓ Monero wallet configured
# ✓ Tor connection active
# ✓ Ready to receive payments
```

---

## Step 3: Customer Sends Payment (Their Action)

### Bitcoin Payment Flow

```
Customer decides to pay
         ↓
Customer runs: swxtch --pay-bitcoin
         ↓
System shows:
  Address: [YOUR WALLET ADDRESS from Step 1]
  Amount: 0.001 BTC
  QR Code: [scannable image]
         ↓
Customer opens their wallet (Phantom/MetaMask/Coinbase/Ledger)
         ↓
Customer scans QR code OR pastes address
         ↓
Customer sends 0.001 BTC
         ↓
Bitcoin network processes payment (10 minutes typical)
         ↓
Payment appears on blockchain (confirmation pending)
```

### Monero Payment Flow

```
Customer decides to pay
         ↓
Customer runs: swxtch --pay-monero
         ↓
System shows:
  Address: [YOUR WALLET SUBADDRESS - different each time]
  Amount: 0.001 XMR
  QR Code: [scannable image]
         ↓
Customer opens Monero wallet (GUI/CLI)
         ↓
Customer scans QR code OR pastes address
         ↓
Customer sends 0.001 XMR
         ↓
Monero network processes payment (2 minutes typical)
         ↓
Payment appears in blockchain (Tor-verified)
```

---

## Step 4: Payment Arrives in Your Wallet

### Bitcoin: Immediate Appearance

```
Blockchain confirms payment
         ↓
SWXTCH detects via Tor
         ↓
Your Bitcoin wallet shows: +0.001 BTC
         ↓
Status: Pending (0-2 confirmations)

After 10 minutes (2 confirmations):
Status: Confirmed ✓

After 20+ minutes:
Status: Fully spendable
```

### Monero: Faster Appearance

```
Blockchain confirms payment
         ↓
SWXTCH detects via Tor
         ↓
Your Monero wallet shows: +0.001 XMR
         ↓
Status: Locked (1 confirmation needed)

After 1 block (~2 minutes):
Status: Unlocked ✓

After confirmation:
Status: Fully spendable and private
```

---

## Step 5: You Own the Money - What You Can Do

### Bitcoin Options

```bash
# Option 1: Keep in your wallet
# Money stays safe, you can access anytime

# Option 2: Spend immediately
bitcoin-cli sendtoaddress "other_address" 0.001

# Option 3: Convert to cash
# Send to exchange (via Tor for privacy)
# Convert BTC → Fiat (USD/EUR/etc)
# Withdraw to bank

# Option 4: Mix/Tumble (for privacy)
# Send through Wasabi/CoinJoin service
# Receive "clean" coins with no history
```

### Monero Options

```bash
# Option 1: Keep in wallet (completely private)
# Money is untraceable anyway
# No mixing needed - Monero is private by default

# Option 2: Spend immediately
monero-wallet-cli
> transfer 8xyz... 0.5  # Send to another address

# Option 3: Convert to cash
# Send to exchange (via Tor)
# Convert XMR → Fiat
# Withdraw to bank (Monero traces end here)

# Option 4: Split across addresses
# Monero best practice: spread funds across multiple wallets
# Each completely unrelated to others
```

---

## Complete Payment Timeline

### Bitcoin Example

```
0:00  Customer initiates payment
      Bitcoin wallet opens
      Customer scans QR code (YOUR ADDRESS)

0:01  Customer sends 0.001 BTC
      Transaction broadcast to network

0:05  First confirmations received
      Your wallet shows unconfirmed: +0.001 BTC

0:15  Second confirmation
      Your wallet shows confirmed: +0.001 BTC ✓
      You can spend it now

1:00  License key auto-generated
      System detects payment
      Creates sk_btc_[random-48-chars]
      License is valid for 30 days
      Auto-renewal ready if needed
```

### Monero Example

```
0:00  Customer initiates payment
      Monero wallet opens
      Customer scans QR code (YOUR STEALTH ADDRESS)

0:01  Customer sends 0.001 XMR
      Transaction broadcast to Monero network
      Ring signature applied (11 possible senders)
      Amount hidden by RingCT
      Receiver hidden by stealth address

0:03  Blockchain confirmation
      Your wallet shows: +0.001 XMR (locked)
      Only you can see this transaction
      Blockchain shows NOTHING about you

0:05  Wallet unlock after 1 block
      Your wallet shows: +0.001 XMR ✓
      Spendable now
      Completely untraceable

1:00  License key auto-generated
      System detects payment via Tor
      Creates sk_xmr_[random-48-chars]
      License is valid for 30 days
      Auto-renewal ready
```

---

## Check Payment Status

### Bitcoin - Check Your Wallet

```bash
# Bitcoin Core
bitcoin-cli getbalance
# Output: 0.001

# Or online
# Go to blockchain.com
# Search your address: bc1q...
# Shows all transactions (public)
```

### Monero - Check Your Wallet

```bash
# Monero CLI
monero-wallet-cli
> balance
Balance: 0.001 XMR (unlocked)

# Or use GUI wallet
# Shows balance privately
# Nobody else can see it
```

### SWXTCH - Check Payment Detection

```bash
# Check if SWXTCH detected payment
python3 << 'EOF'
from swxtch.bitcoin_payments import get_bitcoin_manager
manager = get_bitcoin_manager()

# View all payments received
for txid, payment_data in manager.payment_history.items():
    print(f"TXID: {txid}")
    print(f"Status: {payment_data['status']}")
    print(f"Amount: {payment_data.get('amount', 'N/A')}")
    print(f"Time: {payment_data.get('verified_at', 'pending')}")
    print(f"License: {payment_data.get('license_key', 'N/A')[:20]}...")
    print("---")
EOF
```

---

## Spending Your Money

### Bitcoin Spending Steps

```bash
# 1. Open your Bitcoin wallet
bitcoin-cli getbalance
# Shows: 0.001

# 2. Send to another address
bitcoin-cli sendtoaddress bc1qother... 0.0009

# 3. Money is sent
# Transaction confirmed in 10-20 minutes
# Funds now belong to recipient

# 4. Optional: Use Tor for privacy
# tor --socks-port 9050
# bitcoin-cli -proxy=127.0.0.1:9050 sendtoaddress ...
# Your IP hidden from network
```

### Monero Spending Steps

```bash
# 1. Open Monero wallet
monero-wallet-cli

# 2. Send to another address
> transfer 8xyz... 0.5
# Monero uses new random one-time address for each send
# Ring signature hides you in group of 11

# 3. Money is sent
# Transaction confirmed in 1-2 minutes
# Receiver is anonymous
# Amount is hidden
# Only recipient can see funds

# 4. Complete privacy
# Sender unknown (you're 1 of 11)
# Amount unknown (RingCT encryption)
# Receiver unknown (stealth address)
# Untraceable forever
```

---

## Key Points About Receiving Money

✅ **You set the wallet address** - Where payments go  
✅ **Customers send to YOUR address** - They see it when paying  
✅ **Money appears in YOUR wallet** - Within minutes  
✅ **You own it completely** - Can spend anytime, no restrictions  
✅ **Nobody can take it** - Once on blockchain, it's yours  
✅ **Completely anonymous (Monero)** - Nobody knows who received it  
✅ **License auto-generated** - SWXTCH creates key upon payment confirmation  
✅ **30-day validity** - License valid for 30 days, auto-renewable  

---

## Receiving Multiple Payments

### Bitcoin

```bash
# Same address for all payments
export SWXTCH_BITCOIN_WALLET="bc1q..."

# All payments go to same address
# Blockchain shows all transactions to that address
# (Publicly visible but not linked to your identity if careful)
```

### Monero (RECOMMENDED)

```bash
# Generate NEW subaddress for each payment
monero-wallet-cli
> address new

# Each payment to different subaddress
# Each transaction completely separate
# No connection between payments
# Maximum privacy
```

---

## Privacy Best Practices

### Bitcoin Receiving

1. **Use a dedicated address** - Don't reuse across services
2. **Use privacy wallet** - Wasabi/Samourai for spending
3. **CoinJoin mixing** - Mix received coins before spending
4. **Route through Tor** - Your IP hidden from blockchain
5. **Don't associate with identity** - Keep wallet anonymous

### Monero Receiving (Already Private!)

1. **Use new subaddress per payment** - Automatic with `address new`
2. **All payments inherit privacy** - No extra steps needed
3. **Monero handles it all** - Ring signatures, RingCT, stealth addresses
4. **Route through Tor** - Already integrated in SWXTCH
5. **No mixing needed** - Private by design

---

## Troubleshooting

### "I'm not seeing the payment in my wallet"

```bash
# Wait for confirmations
Bitcoin: 2-10 confirmations needed (10-60 minutes)
Monero: 1 confirmation needed (2-5 minutes)

# Verify your address is set
echo $SWXTCH_BITCOIN_WALLET
echo $SWXTCH_MONERO_WALLET

# Check blockchain directly
Bitcoin: blockchain.com/search/YOUR_ADDRESS
Monero: (Monero blockchain private - only you see it)

# Verify SWXTCH is running
python -m swxtch --status
```

### "Payment detected but no license key generated"

```bash
# Check SWXTCH logs
tail /var/log/swxtch/*.log

# Restart payment detection
python -m swxtch --check-payments

# Manually generate license for TXID
python3 << 'EOF'
from swxtch.bitcoin_payments import get_bitcoin_manager
manager = get_bitcoin_manager()
license = manager.generate_license_key("TXID_HERE", "YOUR_ADDRESS")
print(f"License: {license.key}")
EOF
```

### "Wallet shows received but SWXTCH doesn't detect"

```bash
# Check if Tor is running
curl --proxy socks5://127.0.0.1:9050 https://check.torproject.org

# Manually verify payment
python3 << 'EOF'
from swxtch.payment_anonymity import get_anonymous_router
router = get_anonymous_router()
confirmed, msg = router.verify_payment_anonymous("TXID")
print(msg)
EOF
```

---

## Summary

**You = Payment Receiver**

1. **Set wallet address** - Where you want payments
2. **Customers send money** - They see your address when paying
3. **Money arrives** - Appears in your wallet within minutes
4. **You spend it** - Anytime, no restrictions, completely private
5. **License auto-generated** - SWXTCH creates key upon confirmation
6. **Repeat** - Accept more payments with new subaddresses (Monero)

**That's it. Complete anonymity, complete security, complete control.**

---

**Status: READY TO RECEIVE PAYMENTS**

Bitcoin: bc1q... (set via $SWXTCH_BITCOIN_WALLET)  
Monero: 8AbcD... (set via $SWXTCH_MONERO_WALLET)  
Network: Tor + I2P + Yggdrasil + CJDNS (automatic failover)  
Encryption: Triple-layer (AES-256 + ChaCha20 + OTP)  
Security: ★★★★★ Absolute Maximum
