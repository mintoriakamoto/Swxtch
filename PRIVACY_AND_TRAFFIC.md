# SWXTCH Privacy & Traffic Protection Systems

**Complete documentation for `privacy.py` (390 lines) and `traffic_analysis.py` (244 lines)**

---

## Part 1: Privacy Protection System (privacy.py)

### Overview

Data privacy layer that detects and removes personally identifiable information (PII), masks sensitive data, strips metadata, and enforces log privacy.

**File:** `swxtch/privacy.py`  
**Lines:** 390  
**Purpose:** PII detection/removal, data masking, metadata stripping, log privacy  
**Status:** ✅ FULLY IMPLEMENTED

---

### Core Classes

#### PrivacyManager

```python
from swxtch.privacy import PrivacyManager

privacy = PrivacyManager()

# Remove PII from text
clean_text = privacy.remove_pii("Contact john@example.com")
# Returns: "Contact [EMAIL_MASKED]"

# Mask sensitive data
masked_email = privacy.mask_email("john@example.com")
# Returns: "j***@example.com"

# Strip metadata
clean_data = privacy.strip_metadata({"email": "john@...", "ip": "192.168.1.1"})
# Returns: {}

# Check privacy score
score = privacy.analyze_privacy(user_data)
# Returns: privacy_score (0-100)
```

**Key Methods:**
- `remove_pii(text)` — Remove all personally identifiable info
- `mask_email(email)` — Mask email address
- `mask_phone(phone)` — Mask phone number
- `mask_ip(ip)` — Mask IP address
- `mask_credit_card(cc)` — Mask credit card
- `strip_metadata(data)` — Remove all metadata
- `detect_pii(text)` — Find PII in text
- `analyze_privacy(data)` — Score privacy level
- `sanitize_logs(log_entry)` — Clean log entry

---

### PII Detection & Removal

#### What Gets Masked
- Email addresses → `j***@example.com`
- Phone numbers → `+1 (***) ***-1234`
- IP addresses → `192.168.*.1`
- Credit cards → `****-****-****-1234`
- SSN → `***-**-1234`
- Bitcoin addresses → `bc1q***...***`
- Names → `[NAME_MASKED]`
- URLs → `https://[MASKED].com`

#### Usage Examples

```python
privacy = PrivacyManager()

# Detect PII
text = "Contact john@example.com or call 555-1234"
detected = privacy.detect_pii(text)
# Returns: ["email", "phone"]

# Remove all PII
clean = privacy.remove_pii(text)
# Returns: "Contact [EMAIL_MASKED] or call [PHONE_MASKED]"

# Mask specific types
email_masked = privacy.mask_email("john@example.com")
phone_masked = privacy.mask_phone("+1-555-123-4567")
```

---

### Data Masking Strategies

#### Email Masking
```python
# Full mask
privacy.mask_email("john@example.com", level="full")
# Returns: "[EMAIL_MASKED]"

# Partial mask (show domain)
privacy.mask_email("john@example.com", level="partial")
# Returns: "j***@example.com"

# Keep first letter
privacy.mask_email("john@example.com", level="light")
# Returns: "j***@e***"
```

#### Phone Masking
```python
privacy.mask_phone("+1-555-123-4567")
# Returns: "+1 (***) ***-4567"  # Show last 4 digits

privacy.mask_phone("+1-555-123-4567", show_digits=0)
# Returns: "+1 (***) ***-****"  # Complete mask
```

#### IP Address Masking
```python
privacy.mask_ip("192.168.1.100")
# Returns: "192.168.*.*"  # Last 2 octets masked

privacy.mask_ip("2001:db8::1")  # IPv6
# Returns: "2001:db8:****:****:****:****:****:****"
```

---

### Log Sanitization

```python
# Before: log entry with PII
log_entry = "Payment from john@example.com (192.168.1.100) - $100"

# After: sanitized for storage/display
clean_log = privacy.sanitize_logs(log_entry)
# Returns: "Payment from [EMAIL_MASKED] ([IP_MASKED]) - $100"

# Store securely
with open("/var/log/swxtch/payments.log", "a") as f:
    f.write(clean_log + "\n")
```

---

### Privacy Scoring

```python
# Score data for privacy risks
user_data = {
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "ip": "192.168.1.1",
    "name": "John Smith"
}

score = privacy.analyze_privacy(user_data)
# Returns: privacy_score (0-100)
#   0 = Maximum PII (dangerous)
#   100 = No PII (safe)

if score < 50:
    print("⚠️ HIGH PRIVACY RISK - Remove PII")
    clean_data = privacy.remove_pii(user_data)
else:
    print("✅ Privacy acceptable")
```

---

## Part 2: Traffic Analysis & Protection (traffic_analysis.py)

### Overview

Network traffic analysis and obfuscation to defeat traffic analysis attacks, packet pattern analysis, and behavioral profiling.

**File:** `swxtch/traffic_analysis.py`  
**Lines:** 244  
**Purpose:** Packet obfuscation, dummy traffic, timing randomization, pattern hiding  
**Status:** ✅ FULLY IMPLEMENTED

---

### Core Classes

#### TrafficAnalyzer

```python
from swxtch.traffic_analysis import TrafficAnalyzer

analyzer = TrafficAnalyzer()

# Add dummy traffic to hide real requests
analyzer.add_dummy_traffic(count=10)
# Sends 10 fake requests mixed with real ones

# Randomize packet sizes
analyzer.randomize_packet_sizes(min_size=64, max_size=1500)
# Packets now random sizes

# Add timing perturbation
analyzer.add_timing_perturbation(base_delay=100, variance=50)
# Requests delayed 50-150ms randomly

# Obfuscate traffic patterns
analyzer.obfuscate_patterns()
# Hides correlation between requests
```

**Key Methods:**
- `add_dummy_traffic(count)` — Send N fake requests
- `randomize_packet_sizes(min, max)` — Randomize packet sizes
- `add_timing_perturbation(base, variance)` — Add random delays
- `obfuscate_patterns()` — Hide traffic patterns
- `detect_anomalies(traffic)` — Find unusual patterns
- `analyze_traffic(traffic)` — Analyze for patterns
- `get_traffic_metrics()` — Get current statistics

---

### Dummy Traffic Generation

#### Why Dummy Traffic Matters

```
Normal behavior:
├── Request: example.com [PATTERN IDENTIFIABLE]
├── Request: github.com [PATTERN IDENTIFIABLE]
└── Request: reddit.com [PATTERN IDENTIFIABLE]

With dummy traffic:
├── Request: example.com [REAL]
├── Request: [FAKE]
├── Request: github.com [REAL]
├── Request: [FAKE]
├── Request: reddit.com [REAL]
├── Request: [FAKE]
└── Request: [FAKE]

Attacker can't distinguish real from dummy
```

#### Implementation

```python
analyzer = TrafficAnalyzer()

# Generate 20 dummy requests
analyzer.add_dummy_traffic(count=20)

# Dummy requests include:
# - Requests to random domains
# - Random HTTP methods
# - Random body sizes
# - Random timing
# - Random headers

# Result: Real traffic hidden in noise
```

---

### Packet Size Randomization

```python
# Randomize packet sizes (defeats size-based analysis)
analyzer.randomize_packet_sizes(
    min_size=64,      # Minimum packet size (bytes)
    max_size=1500     # Maximum packet size (bytes)
)

# Before:
# Packet 1: 256 bytes
# Packet 2: 256 bytes
# Pattern: Always 256 = "consistent request size"

# After:
# Packet 1: 847 bytes
# Packet 2: 432 bytes
# Packet 3: 1203 bytes
# Pattern: Unidentifiable
```

---

### Timing Obfuscation

```python
# Add random delays to hide timing patterns
analyzer.add_timing_perturbation(
    base_delay=100,     # Base delay (ms)
    variance=50         # ±50ms variance
)

# Before:
# Request 1 at 0ms
# Request 2 at 100ms
# Request 3 at 200ms
# Pattern: Regular 100ms intervals = "machine behavior"

# After:
# Request 1 at 0ms
# Request 2 at 87ms (within 50-150ms range)
# Request 3 at 156ms (within 50-150ms range)
# Pattern: Randomized = "human behavior"
```

---

### Pattern Analysis & Detection

#### Detect Anomalies

```python
# Analyze traffic for suspicious patterns
traffic_log = [...]  # Your traffic data

anomalies = analyzer.detect_anomalies(traffic_log)

for anomaly in anomalies:
    print(f"Pattern detected: {anomaly['type']}")
    print(f"Confidence: {anomaly['confidence']}%")
    # Could indicate:
    # - Automated behavior
    # - Bot activity
    # - Suspicious access pattern
```

#### Analyze Traffic Patterns

```python
metrics = analyzer.analyze_traffic(traffic_log)

# Returns:
{
    "request_frequency": 5.2,      # requests/second
    "average_packet_size": 512,    # bytes
    "timing_variance": 2.1,        # standard deviation
    "pattern_entropy": 4.8,        # 0-8 (higher = more random)
    "anomaly_score": 0.1,          # 0-1 (higher = more suspicious)
    "identifiability": 0.2         # 0-1 (higher = more identifiable)
}
```

---

### Integration Examples

#### Complete Traffic Obfuscation

```python
from swxtch.traffic_analysis import TrafficAnalyzer
from swxtch.dns_privacy import DNSPrivacyManager

# Layer 1: DNS Privacy
dns = DNSPrivacyManager()
dns.configure_dns_over_tor()

# Layer 2: Traffic Obfuscation
analyzer = TrafficAnalyzer()
analyzer.add_dummy_traffic(count=15)
analyzer.randomize_packet_sizes(64, 1500)
analyzer.add_timing_perturbation(100, 50)
analyzer.obfuscate_patterns()

# Layer 3: Tor Network
# (Already handled by dns_privacy)

# Result: Multi-layered traffic protection
```

---

### API Reference

#### PrivacyManager

```python
class PrivacyManager:
    def remove_pii(text: str) -> str
    def mask_email(email: str, level: str = "partial") -> str
    def mask_phone(phone: str, show_digits: int = 4) -> str
    def mask_ip(ip: str) -> str
    def mask_credit_card(cc: str, show_digits: int = 4) -> str
    def strip_metadata(data: Dict) -> Dict
    def detect_pii(text: str) -> List[str]
    def analyze_privacy(data: Dict) -> int
    def sanitize_logs(log_entry: str) -> str
```

#### TrafficAnalyzer

```python
class TrafficAnalyzer:
    def add_dummy_traffic(count: int) -> None
    def randomize_packet_sizes(min_size: int, max_size: int) -> None
    def add_timing_perturbation(base_delay: int, variance: int) -> None
    def obfuscate_patterns() -> None
    def detect_anomalies(traffic: List) -> List[Dict]
    def analyze_traffic(traffic: List) -> Dict
    def get_traffic_metrics() -> Dict
```

---

## Performance Impact

| Operation | Time | Impact |
|-----------|------|--------|
| PII Detection | <1ms | Per item |
| Data Masking | <1ms | Per item |
| Log Sanitization | ~1ms | Per entry |
| Dummy Traffic | +50-200ms | Per request |
| Packet Randomization | <1ms | Per packet |
| Timing Perturbation | +50-150ms | Per request |

---

## Security Properties

### Privacy Module
✅ Detects and removes PII  
✅ Masks sensitive data  
✅ Sanitizes logs  
✅ Scores privacy level  
✅ Prevents data leaks  

### Traffic Analysis Module
✅ Hides traffic patterns  
✅ Defeats timing analysis  
✅ Defeats packet analysis  
✅ Obfuscates behavior  
✅ Prevents fingerprinting  

---

## Status

✅ **Both modules fully implemented and production-ready**

Privacy and traffic protection work together to provide comprehensive protection against analysis attacks.

Seamlessly integrate with all other SWXTCH systems.
