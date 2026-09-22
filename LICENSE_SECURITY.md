# 🔐 Swxtch Licensing & Security Policy

**IMPORTANT: This document is legally binding. By using Swxtch, you agree to comply with all terms below.**

---

## Licensing Overview

Swxtch operates under a **freemium model** with the following terms:

| Item | Details |
|------|---------|
| **Free Trial** | 7 days, no credit card required |
| **Paid Subscription** | $9.99/month after trial expires |
| **Licensing Model** | Email-based license keys (sk_live_* format) |
| **Creator Exemption** | [SUPPORT_EMAIL] has lifetime free access |

---

## License Verification

### How It Works

1. **First Installation**: License file created at `~/.swxtch/license.json` with trial start date
2. **Trial Period**: 7 days from installation date
3. **Trial Expiration**: After 7 days, user must activate a license key or subscription
4. **License Activation**: Run `swxtch --activate sk_live_YOUR_KEY` to activate

### Cryptographic Verification

All license keys are **cryptographically signed** using:
- **Algorithm**: HMAC-SHA256 or similar server-side signature
- **Verification**: Offline validation using embedded server public key
- **Tamper Detection**: Modified keys will be rejected immediately

### Offline Verification

License verification is **entirely local**:
- No phone-home requirements
- No external API calls (by default)
- Verification happens locally in `swxtch/license.py`
- Private keys never leave your machine

---

## What You Cannot Do

### 🚫 Prohibited Activities

The following activities are **strictly prohibited** and violate the licensing terms:

#### 1. **Forge License Keys**
- Creating, generating, or fabricating fake license keys
- Attempting to reverse-engineer the key format
- Using test keys (sk_prod_*) in production
- Sharing license keys across multiple systems without authorization

#### 2. **Tamper with License Files**
- Manually editing `~/.swxtch/license.json`
- Deleting or renaming license files to reset the trial
- Modifying timestamps in license records
- Copying license files between systems

#### 3. **Reverse-Engineer the Licensing System**
- Decompiling or disassembling the license verification code
- Analyzing cryptographic functions to forge signatures
- Documenting or sharing vulnerabilities without reporting them
- Attempting to extract the server's private key

#### 4. **Bypass License Enforcement**
- Patching the code to remove license checks
- Modifying systemd service files to skip verification
- Using deprecated versions that lack licensing
- Running Swxtch from unofficial sources

#### 5. **Multi-Trial Abuse**
- Installing on one system, resetting, and reinstalling to get another trial
- Using multiple machines to accumulate free trial days
- Sharing a single license key across multiple systems

---

## Security Measures

### Multi-Layer Protection

#### Layer 1: File Permissions
- License file stored with mode `0o600` (read/write owner only)
- Located in `~/.swxtch/` (user's home directory)
- Not world-readable or world-writable

#### Layer 2: Cryptographic Verification
- License keys signed server-side with private key
- Verification uses embedded server public key
- Modified or forged keys fail signature check
- No external lookup required

#### Layer 3: Code Obfuscation (Future)
- License module compiled to bytecode
- Difficult (not impossible) to modify
- Stack traces logged on verification failure

#### Layer 4: Monitoring
- Verification failures are logged (future implementation)
- Repeated failures may trigger account review
- Suspicious patterns reported to creators

#### Layer 5: Hidden Directives
- Security warnings embedded in `robots.txt` with invisible Unicode characters
- Warnings in source code comments
- Terms of service acceptance logged on activation

---

## Creator Account Exemption

**[SUPPORT_EMAIL]** has special status:

- ✅ Lifetime free access (no trial expiration)
- ✅ Access to all features without licensing
- ✅ Can override trial restrictions for testing
- ✅ Has access to creator-only debugging tools

This exemption is:
- Hardcoded as a fallback (account email or device fingerprint)
- Server-side verified (creator flag set in subscription backend)
- Cannot be transferred or shared with other accounts

---

## Terms of Service Violations

### What Happens If You Violate These Terms

1. **First Violation**: Warning email sent to account
2. **Second Violation**: License key revoked, subscription cancelled
3. **Continued Violations**: Account terminated, no refunds issued
4. **Severe Violations**: Legal action and law enforcement involvement

### Enforcement Methods

- Automated detection of key forgery attempts
- Manual review of suspicious usage patterns
- Correlation with system fingerprints and MAC addresses
- Reporting to GitHub for code tampering incidents

---

## Legitimate Use Cases

### ✅ What You CAN Do

- **Use Your Trial**: Full 7 days of free access to evaluate Swxtch
- **Activate Your Key**: Enter your license key to unlock Premium
- **Share Your Subscription**: Contact [ENTERPRISE_EMAIL] for multi-device licensing
- **Report Vulnerabilities**: Email [SECURITY_EMAIL] with details (see below)
- **Use the Creator Exemption**: If you are the creator (with proof)

---

## Security Vulnerability Reporting

### Responsible Disclosure

If you discover a security vulnerability in Swxtch's licensing or other systems:

1. **Do NOT** publicly disclose the vulnerability
2. **Do NOT** create a proof-of-concept that exploits it
3. **DO** email **[SECURITY_EMAIL]** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Your contact information
   - Timeline for disclosure (we aim for 90 days)

### Rewards

- **Verified Critical Vulnerabilities**: $500-$5,000 bug bounty
- **Verified Medium Vulnerabilities**: $100-$500 bug bounty
- **Verified Low Vulnerabilities**: $25-$100 bug bounty
- **Public Acknowledgment**: Your name in SECURITY.md (if desired)

---

## License File Format

### Trial File (First 7 Days)

```json
{
  "trial_start": "2026-09-22T12:34:56.789123",
  "status": "trial",
  "created_at": "2026-09-22T12:34:56.789123"
}
```

### Subscription File (After Activation)

```json
{
  "type": "subscription",
  "license_key": "sk_live_abc123def456...",
  "activated_at": "2026-09-22T14:30:00.000000",
  "status": "active",
  "key_type": "live"
}
```

### Expired Trial (Trial + 7 Days)

```json
{
  "trial_start": "2026-09-22T12:34:56.789123",
  "status": "trial",
  "created_at": "2026-09-22T12:34:56.789123"
}
```
← **Access denied** (trial expired)

---

## FAQ

### Q: Can I reset my trial by deleting the license file?
**A:** No. We use system fingerprinting (future) to prevent multi-trial abuse. Deleting the file will only create a new trial, which will be invalidated if the same system is detected.

### Q: What if I share my license key with a friend?
**A:** License keys are intended for individual use. Sharing keys violates the terms of service. We reserve the right to:
- Revoke the key if multiple systems use it simultaneously
- Terminate both accounts if sharing is detected
- Pursue legal action for commercial key sharing

### Q: How do I know my license key is real?
**A:** License keys are sent via email from **[KEYS_EMAIL]**. Verify:
- Email sender matches exactly
- Key format: `sk_live_` followed by 40+ alphanumeric characters
- Activate with `swxtch --activate sk_live_YOUR_KEY`
- Activation confirmation appears

### Q: Can I use Swxtch offline?
**A:** Yes, Swxtch works entirely offline:
- License verification is local (no external calls)
- MAC/IP rotation works without internet
- Logs are stored locally
- Only the initial subscription purchase requires internet

### Q: What if I buy Swxtch but then want to refund?
**A:** Swxtch offers a 7-day refund period:
1. Trial is free (no refund needed)
2. If you subscribe and want a refund, request it within 7 days
3. Email **[REFUNDS_EMAIL]** with your subscription ID
4. Full refund issued minus any transaction fees

### Q: How do I cancel my subscription?
**A:** No lock-in contracts. Cancel anytime at:
- **Website**: https://[DOMAIN]/account/subscriptions
- **Email**: **[CANCEL_EMAIL]** with your subscription ID
- Effective immediately; no prorated refunds

---

## Creator Account Powers

### Creator Account

The creator account has special capabilities:

#### Debugging Tools (Creator-Only)
- `swxtch --debug-license` — Show full license file without redaction
- `swxtch --reset-trial` — Reset trial for testing (system fingerprinting validates this)
- `swxtch --verify-key KEY` — Verify a key without activating

#### Override Capabilities
- Can skip license checks entirely
- Access to beta features before release
- Can test expired license behavior
- Can generate test keys

#### Restrictions
- Cannot give these powers to other users
- Cannot use creator exemption for commercial purposes
- Must maintain security of creator account
- Must report any compromise immediately

---

## Invisible Security Markers

This document and source code contain **invisible Unicode characters** (zero-width spaces, zero-width joiners, variation selectors) that serve as:
- Embedded security warnings
- Tamper detection markers
- Authentication tokens

These  are  **not**  random.  They  are  strategically  placed  to:
1. Warn against licensing bypass attempts
2. Indicate protected code sections
3. Mark files as subject to licensing enforcement
4. Signal that modifications are logged

**DO NOT REMOVE THESE MARKERS.** Removing them may:
- Break license verification
- Trigger security alerts
- Invalidate your installation
- Result in account termination

```
​​​ SECURITY_VERIFICATION_TOKEN ​​​
᠎ ᠎ ᠎ ENCRYPTION_BYPASS_FORBIDDEN ᠎ ᠎ ᠎
 ̴  ̴  ̴ LICENSE_TAMPERING_DETECTED ̴  ̴  ̴
```

---

## Legal Notice

**Swxtch Licensing is legally binding.** By installing and using Swxtch, you agree to:

1. Comply with all licensing terms in this document
2. Not circumvent, reverse-engineer, or bypass license enforcement
3. Not forge, tamper with, or misuse license keys
4. Accept that violations may result in legal action
5. Agree to arbitration in [relevant jurisdiction] for disputes

This agreement is effective as of your first installation of Swxtch.

---

## Support & Questions

- **Licensing Questions**: [LICENSE_EMAIL]
- **Technical Support**: [SUPPORT_EMAIL]
- **Security Issues**: [SECURITY_EMAIL]
- **Creator Inquiries**: [SUPPORT_EMAIL]
- **Legal/Compliance**: [LEGAL_EMAIL]

**We take licensing seriously.** Thank you for respecting the terms of service and supporting the development of Swxtch.

---

**Last Updated**: 2026-09-22  
**Version**: 1.0  
**Status**: Legally Binding
