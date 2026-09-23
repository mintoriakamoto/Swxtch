# ₿ Bitcoin Payment System & License Key Generation

**Complete Bitcoin-to-license conversion with 30-day auto-renewal.**

Swxtch accepts Bitcoin payments and automatically generates 30-day license keys. Licenses auto-renew until cancelled.

---

## Quick Start

### 1️⃣ Generate Payment Request

```bash
swxtch --pay-bitcoin
```

Output:
```
₿ Bitcoin Payment Request

Wallet:  [masked]...
Amount:  0.001 BTC
Satoshi: 100000

Validation QR Code (BIP21):
bitcoin:[wallet]?amount=0.001&label=Swxtch%20Premium

Wallet Options:
  • Phantom (SOL/ETH) → bridge to Bitcoin
  • MetaMask → add Bitcoin network
  • Coinbase Wallet → native Bitcoin support
  • Direct Bitcoin Wallet → scan QR code

Request ID: [request-id]
After payment, use: swxtch --check-payment TXID
```

### 2️⃣ Send Bitcoin

Use any wallet app:
- **Phantom**: Sol/Eth wallet with Bitcoin bridge
- **MetaMask**: Install Bitcoin network, send 0.001 BTC
- **Coinbase Wallet**: Native Bitcoin support
- **Ledger/Trezor**: Hardware wallet support

### 3️⃣ Verify Payment

```bash
swxtch --check-payment <transaction-id>
```

Response (once confirmed):
```
₿ Payment Status: [transaction-id]

✓ Payment confirmed on blockchain

✓ License key will be sent to your email
```

### 4️⃣ Activate License Key

Once payment is confirmed (usually 20 minutes for 2 confirmations), receive license key in email.

```bash
swxtch --activate sk_btc_[your-license-key]
```

---

## Configuration

### Environment Variable Setup

Your Bitcoin wallet address should be stored securely in environment variables, **never in code**:

```bash
# Set your Bitcoin wallet address
export SWXTCH_BITCOIN_WALLET="bc1qxyz..."

# Optional: Set payment amount (in satoshi)
export SWXTCH_PAYMENT_SATOSHI="100000"  # ~0.001 BTC
```

### Production Setup

In production, store wallet address in a secure vault:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Docker Secrets (Swarm)
- Kubernetes Secrets

**Never hardcode wallet addresses in source code.**

---

## License Key Details

### Format

```
sk_btc_[48-character-random-string]
```

Example:
```
sk_btc_KUPwGxErxyf4owoWJdXuAMvwqeg0H_aQGycgMw8a1VK
```

### Validity

- **Duration**: 30 days from activation
- **Auto-renewal**: Enabled by default (automatic recurring payment)
- **Expiration**: License key expires exactly 30 days after generation
- **Renewal**: New payment required after expiration (auto-pay enabled)

### Verification

```bash
# Check license validity
swxtch --verify-btc-key sk_btc_[your-key]

# Output:
# ✓ License valid (25 days remaining)
```

---

## Auto-Renewal

### Enable Auto-Renewal

Auto-renewal is **enabled by default**. License automatically renews every 30 days:

```bash
swxtch --auto-renew sk_btc_[your-key]
```

**What happens:**
1. License expires on day 30
2. Automatic payment of 0.001 BTC is initiated
3. New 30-day license is generated
4. No manual action required

### Disable Auto-Renewal

Stop automatic payments:

```bash
swxtch --disable-renewal sk_btc_[your-key]
```

**What happens:**
- License still works until expiration
- No automatic payment after expiration
- Manual renewal required to continue using Swxtch

---

## Wallet Integration

### Phantom Wallet (Solana/Ethereum)

1. Install Phantom: https://phantom.app
2. Create/import Bitcoin wallet via bridge
3. Send payment to Swxtch address
4. Confirmation: ~1 minute

### MetaMask

1. Install MetaMask: https://metamask.io
2. Add Bitcoin network manually
3. Send payment: 0.001 BTC
4. Confirmation: ~20 minutes (2 blockchain confirmations)

### Coinbase Wallet

1. Install Coinbase Wallet
2. Select Bitcoin network
3. Send payment directly
4. Confirmation: ~20 minutes (2 blockchain confirmations)

### Hardware Wallet (Ledger/Trezor)

1. Connect hardware wallet
2. Open Bitcoin app
3. Send to Swxtch address
4. Confirm on device
5. Confirmation: ~20 minutes (2 blockchain confirmations)

---

## Payment Verification

### Check Payment Status

```bash
swxtch --check-payment bc1q8abc...xyz
```

Possible responses:

```
✓ Payment confirmed on blockchain
  → License key sent

⏳ Payment pending confirmation (usually 20 minutes for 2 confirmations)
  → Check back shortly

✗ Transaction not found
  → Verify transaction ID
```

### Blockchain Confirmation

Bitcoin payments require **confirmation on the blockchain**:

- **Pending**: 0-1 confirmations (0-10 minutes)
- **Confirmed**: 2+ confirmations (~20 minutes)
- **Final**: 6+ confirmations (~60 minutes)

Swxtch sends license key after **2 confirmations** (~20 minutes).

---

## Payment Records

### View Payment History

Payment history is stored in encrypted logs:

```bash
# View your payment log (requires admin)
sudo cat /var/log/swxtch/bitcoin_payments.json
```

Example entry:
```json
{
  "license_key": "sk_btc_...",
  "generated_at": "2026-09-22T23:43:24.514953",
  "expires_at": "2026-10-22T23:43:24.514953",
  "payment_address": "bc1q...",
  "status": "active",
  "auto_renew": true
}
```

---

## Pricing

| Period | Cost |
|--------|------|
| 30-day license | 0.001 BTC (~$25-50 USD) |
| Auto-renewal | 0.001 BTC every 30 days |
| Manual renewal | 0.001 BTC per 30 days |

**Current Bitcoin price affects USD equivalent.**

---

## Troubleshooting

### "Payment pending confirmation"

**Problem**: Payment sent but not yet on blockchain

**Solution**:
- Wait ~20 minutes for 2 blockchain confirmations
- Use `swxtch --check-payment TXID` to monitor
- Check transaction on blockexplorer.com

### "Payment not found"

**Problem**: Transaction ID doesn't match Swxtch address

**Solution**:
- Verify you sent to correct address (shown in payment request)
- Check transaction on blockchain
- Generate new payment request: `swxtch --pay-bitcoin`

### "License key not found"

**Problem**: License key doesn't match any payment

**Solution**:
- Use full key including prefix: `sk_btc_...`
- Verify key wasn't typo'd
- Check payment confirmation: `swxtch --check-payment TXID`

### "License expired"

**Problem**: 30-day license has passed expiration

**Solution**:
- Auto-renewal failed → check payment account
- Manual renewal: `swxtch --pay-bitcoin`
- Disable auto-renewal: `swxtch --disable-renewal KEY`

### "Auto-renewal disabled"

**Problem**: License expired because auto-renewal was off

**Solution**:
- Pay for new license: `swxtch --pay-bitcoin`
- Enable auto-renewal: `swxtch --auto-renew NEW_KEY`

---

## Security

### Wallet Address Protection

✅ **Bitcoin wallet address is masked in all output**

```bash
Wallet: [BITCOIN_WALLET_MASKED]
```

Real wallet address stored only in:
- Environment variable (`SWXTCH_BITCOIN_WALLET`)
- Encrypted config (production vault)

### License Key Security

✅ **License keys are cryptographically random**

- Generated using `secrets.token_urlsafe()` (CSPRNG)
- 48-character format (high entropy)
- Unique per payment

### Payment Log Security

✅ **Payment history encrypted at rest**

```bash
# Permissions: 0o600 (owner read/write only)
-rw------- /var/log/swxtch/bitcoin_payments.json
```

Access requires root/admin privileges.

---

## API Reference

### Generate Payment Request

```python
from swxtch.bitcoin_payments import get_bitcoin_manager

mgr = get_bitcoin_manager()
request = mgr.generate_payment_request()

# Returns:
{
    "wallet_address": "[BITCOIN_WALLET_MASKED]",
    "amount_satoshi": 100000,
    "amount_btc": 0.001,
    "qr_code_uri": "bitcoin:...",
    "request_id": "...",
    "created_at": "2026-09-22T..."
}
```

### Generate License Key

```python
from swxtch.bitcoin_payments import get_bitcoin_manager

mgr = get_bitcoin_manager()
license_key = mgr.generate_license_key(
    transaction_id="bc1q...",
    payment_address="bc1q..."
)

# Returns LicenseKey object:
# - key: "sk_btc_..."
# - expires_at: "2026-10-22T..."
# - auto_renew_enabled: True
```

### Verify License Key

```python
valid, message = mgr.verify_license_key("sk_btc_...")

if valid:
    print(message)  # ✓ License valid (25 days remaining)
else:
    print(message)  # License expired - renewal required
```

---

## Support

Having issues?

- Check: [BITCOIN_PAYMENTS.md](BITCOIN_PAYMENTS.md) (this file)
- Report: GitHub Issues
- Email: [SUPPORT_EMAIL]

---

**Last Updated**: 2026-09-22  
**Version**: 1.0  
**Status**: Production Ready
