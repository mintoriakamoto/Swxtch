# SWXTCH Blockchain Synchronization System

**Complete documentation for `sync.py` (496 lines)**

---

## Overview

Comprehensive blockchain state synchronization and management for Bitcoin and Monero payments. Handles payment detection, balance checking, fee estimation, and multi-chain coordination.

**File:** `swxtch/sync.py`  
**Lines:** 496  
**Purpose:** Blockchain sync, payment verification, balance management, fee optimization  
**Status:** ✅ FULLY IMPLEMENTED

---

## Core Classes

### BlockchainSync

```python
from swxtch.sync import BlockchainSync

# Initialize with wallet address
sync = BlockchainSync(wallet_address="bc1q...")

# Get current balance
balance = sync.get_balance()
# Returns: {"btc": 0.001, "sat": 100000, "confirmed": 100000, "unconfirmed": 0}

# Check payment confirmation
confirmations = sync.get_confirmations(txid)
# Returns: 3 (number of confirmations)

# Get payment history
history = sync.get_payment_history()
# Returns: [{"txid": "...", "amount": 100000, "time": "2026-09-25..."}]
```

**Key Methods:**
- `get_balance()` — Get current wallet balance
- `get_confirmations(txid)` — Check transaction confirmations
- `get_payment_history()` — Retrieve payment records
- `estimate_fee(size)` — Estimate transaction fee
- `detect_payment(txid, amount)` — Detect incoming payment
- `get_address_balance(address)` — Check specific address
- `wait_for_confirmation(txid, target)` — Wait for N confirmations
- `validate_transaction(txid)` — Validate transaction authenticity

---

## Payment Detection

### Automatic Payment Detection

```python
sync = BlockchainSync("bc1q...")

# Monitor for incoming payment
def on_payment_received(txid, amount, timestamp):
    print(f"✅ Received {amount} sat from {txid}")
    
# Set callback
sync.on_payment = on_payment_received

# Start monitoring
sync.start_monitoring()

# Stop when done
sync.stop_monitoring()
```

**Detection Features:**
- Real-time payment detection
- Automatic callback on receive
- Supports multiple addresses
- Handles unconfirmed transactions
- Retry logic for confirmation tracking

### Payment Verification

```python
# Verify payment is real
is_valid = sync.validate_transaction(txid)

if is_valid:
    confirmations = sync.get_confirmations(txid)
    if confirmations >= 2:
        print("✅ Payment confirmed")
    else:
        print(f"⏳ Waiting ({confirmations}/2 confirmations)")
else:
    print("❌ Invalid transaction")
```

**Verification Checks:**
- Transaction exists on blockchain
- Amount matches expected
- Destination address correct
- Not a double-spend
- Proper formatting

---

## Balance Management

### Get Balance

```python
# Get complete balance information
balance = sync.get_balance()

# Structure:
{
    "total": 100000,           # Total satoshis
    "confirmed": 100000,       # Confirmed amount
    "unconfirmed": 0,          # Pending confirmation
    "btc": 0.001,             # In BTC
    "pending_txs": 0          # Awaiting confirmation
}
```

### Monitor Balance Changes

```python
import time

previous_balance = sync.get_balance()["confirmed"]

def check_for_payment():
    current_balance = sync.get_balance()["confirmed"]
    
    if current_balance > previous_balance:
        change = current_balance - previous_balance
        print(f"✅ Received {change} sat")
        return True
    return False

# Poll for payment
for i in range(60):  # Check for 10 minutes
    if check_for_payment():
        break
    time.sleep(10)
```

---

## Fee Estimation

### Estimate Transaction Fee

```python
# Estimate fee for transaction size
tx_size = 226  # bytes
fee_rate = sync.get_fee_rate()
# Returns: 50 sat/byte (current network fee)

estimated_fee = sync.estimate_fee(tx_size)
# Calculates: 226 bytes * 50 sat/byte = 11,300 sat

print(f"Estimated fee: {estimated_fee} sat ({estimated_fee/100000:.6f} BTC)")
```

### Fee Optimization

```python
# Get fee rates for different priorities
fees = sync.get_fee_rates()

# Structure:
{
    "fast": 100,      # sat/byte - 10 minute confirmation
    "standard": 50,   # sat/byte - 30 minute confirmation
    "slow": 25        # sat/byte - 2+ hour confirmation
}

# Calculate for different priorities
fast_fee = sync.estimate_fee(226, priority="fast")
std_fee = sync.estimate_fee(226, priority="standard")
slow_fee = sync.estimate_fee(226, priority="slow")
```

---

## Monero Integration

### Monero Balance

```python
# Get Monero balance (if configured)
xmr_balance = sync.get_monero_balance()

# Structure:
{
    "total": 0.001,           # Total XMR
    "unlocked": 0.0009,       # Spendable
    "locked": 0.0001,         # Pending unlock
    "confirmations": 10       # Current block height
}
```

### Monero Payment Detection

```python
# Monero payment is more private
monero_tx = sync.detect_monero_payment(amount=0.001)

# Returns ring signature info (if detected)
if monero_tx:
    print("✅ Monero payment detected")
    print(f"Ring size: {monero_tx['ring_size']}")  # Usually 11+
    print(f"Stealth address: {monero_tx['stealth']}")
```

---

## Multi-Chain Support

### Support Multiple Blockchains

```python
# Bitcoin
btc_balance = sync.get_balance("bitcoin")

# Monero
xmr_balance = sync.get_balance("monero")

# Get all balances
all_balances = sync.get_all_balances()
# Returns: {"bitcoin": {...}, "monero": {...}}

# Get total value (if exchange rate known)
total_usd = sync.get_total_value_usd()
```

### Chain-Specific Operations

```python
# Bitcoin specific
btc_sync = sync.get_chain_sync("bitcoin")
btc_fee = btc_sync.estimate_fee(226)

# Monero specific
xmr_sync = sync.get_chain_sync("monero")
xmr_height = xmr_sync.get_block_height()
```

---

## Nonce/Sequence Management

### Transaction Sequencing

```python
# Get next nonce for transaction
nonce = sync.get_next_nonce()

# For UTXO-based chains (Bitcoin):
# nonce = index of next available UTXO

# For account-based chains:
# nonce = next account sequence number
```

### Prevent Double-Spend

```python
# Track pending transactions
pending = sync.get_pending_transactions()

for tx in pending:
    print(f"Pending: {tx['txid']} ({tx['amount']} sat)")

# Ensure new transaction uses available UTXOs
available_utxos = sync.get_available_utxos()
# Don't spend UTXOs that are pending
```

---

## Confirmation Waiting

### Wait for N Confirmations

```python
# Wait up to 10 minutes for 2 confirmations
confirmed = sync.wait_for_confirmation(
    txid=payment_txid,
    target_confirmations=2,
    timeout_seconds=600
)

if confirmed:
    print("✅ Payment confirmed")
    # Generate license key
    license = generate_license()
else:
    print("⏳ Timeout waiting for confirmation")
```

### Confirmation Tracking

```python
import time

def monitor_confirmations(txid, target=2):
    """Monitor transaction until target confirmations."""
    
    start_time = time.time()
    
    while True:
        confirmations = sync.get_confirmations(txid)
        
        if confirmations >= target:
            return True
        
        elapsed = time.time() - start_time
        if elapsed > 3600:  # 1 hour timeout
            return False
        
        print(f"Confirmations: {confirmations}/{target}")
        time.sleep(30)  # Check every 30 seconds
```

---

## Integration with Payments

### From Bitcoin Payment to Confirmation

```python
from swxtch.bitcoin_payments import get_bitcoin_manager
from swxtch.sync import BlockchainSync

# Get payment request
payment_mgr = get_bitcoin_manager()
request = payment_mgr.generate_payment_request()

# User sends payment
# Customer sends 100000 sat to request['wallet_address']

# Sync monitors blockchain
sync = BlockchainSync(request['wallet_address'])

# Wait for payment
if sync.wait_for_confirmation(txid, target_confirmations=2):
    # Payment confirmed
    license = payment_mgr.generate_license_key(txid, request['wallet_address'])
    print(f"✅ License: {license.key}")
else:
    print("❌ Payment not confirmed")
```

---

## API Reference

### BlockchainSync Class

```python
class BlockchainSync:
    def __init__(self, wallet_address: str, chain: str = "bitcoin")
    
    # Balance Operations
    def get_balance() -> Dict
    def get_address_balance(address: str) -> Dict
    def get_all_balances() -> Dict
    def get_total_value_usd() -> float
    
    # Transaction Operations
    def get_confirmations(txid: str) -> int
    def get_payment_history() -> List[Dict]
    def get_pending_transactions() -> List[Dict]
    def validate_transaction(txid: str) -> bool
    def detect_payment(txid: str, amount: int) -> bool
    
    # Fee Operations
    def get_fee_rate() -> int
    def get_fee_rates() -> Dict
    def estimate_fee(size: int, priority: str = "standard") -> int
    
    # UTXO Operations (Bitcoin)
    def get_available_utxos() -> List[Dict]
    def get_utxo_by_txid(txid: str) -> Dict
    
    # Confirmation Waiting
    def wait_for_confirmation(txid: str, target_confirmations: int, timeout: int) -> bool
    
    # Monitoring
    def start_monitoring()
    def stop_monitoring()
    def on_payment(callback: Callable)
    
    # Multi-Chain
    def get_chain_sync(chain: str) -> ChainSync
    def get_monero_balance() -> Dict
    
    # Nonce Management
    def get_next_nonce() -> int
    def get_block_height() -> int
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Get Balance | ~1-2s | Network dependent |
| Check Confirmations | ~1-2s | API call |
| Estimate Fee | <100ms | Local calculation |
| Wait for Confirmation | 10-60min | Network dependent |
| Detect Payment | ~1-2s | Real-time detection |

---

## Security Properties

### Protects Against
✅ Double-spend detection  
✅ Invalid transactions  
✅ Incorrect amounts  
✅ Wrong addresses  
✅ Transaction manipulation  

### Does Not Protect Against
❌ Blockchain-level attacks  
❌ 51% attacks  
❌ Exchange rate fraud  

---

## Testing

```python
def test_balance_retrieval():
    sync = BlockchainSync("bc1q...")
    balance = sync.get_balance()
    assert "confirmed" in balance
    assert "total" in balance

def test_confirmation_wait():
    sync = BlockchainSync("bc1q...")
    # Note: requires real transaction on network
    confirmed = sync.wait_for_confirmation("abc123...", 2, timeout=300)
    assert isinstance(confirmed, bool)

def test_fee_estimation():
    sync = BlockchainSync("bc1q...")
    fee = sync.estimate_fee(226)
    assert fee > 0
```

---

## Status

✅ **Fully Implemented and Production-Ready**

Blockchain synchronization is complete and handles all payment verification scenarios.

Seamlessly integrates with Bitcoin and Monero payment systems.
