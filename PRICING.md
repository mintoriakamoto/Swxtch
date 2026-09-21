# Swxtch Pricing & Subscription

## Plans

| Feature | Free Trial | Premium |
|---------|-----------|---------|
| **Cost** | $0 | $9.99/month |
| **Duration** | 7 days | Ongoing |
| **Boot MAC rotation** | ✓ | ✓ |
| **Boot IP renewal** | ✓ | ✓ |
| **SHA3-256 verification** | ✓ | ✓ |
| **FIPS 206 encryption** | ✓ | ✓ |
| **Interactive TUI** | ✓ | ✓ |
| **Manual rotation control** | ✓ | ✓ |
| **Secure logging** | ✓ | ✓ |
| **Priority support** | — | ✓ |

## Free Trial

**Start for FREE. No credit card required.**

- ✓ 7 days full access to all features
- ✓ Boot-verified MAC/IP rotation
- ✓ Post-quantum encryption (MLKEM, FIPS 206)
- ✓ Cryptographic verification (SHA3-256)
- ✓ Interactive control via TUI
- ✓ Secure logging to `/var/log/swxtch/`

Trial starts on your first installation of Swxtch. Check your trial status anytime:

```bash
swxtch --license
```

### What Happens When Trial Ends

After 7 days:
- Boot service stops running
- Interactive TUI closes with a message
- You can upgrade to Premium to continue using Swxtch

## Premium Subscription

**$9.99/month** — Continue using Swxtch after your trial.

### What's Included

- Unlimited boot-verified MAC/IP rotation
- All cryptographic features (SHA3-256, MLKEM, FIPS 206)
- Priority support via email
- Cancel anytime (no lock-in contracts)

### How to Subscribe

After your trial expires, upgrade online:

```bash
swxtch --subscribe
```

Or visit: https://swxtch.io/pricing

## Upgrade to Premium

### From CLI

```bash
swxtch --subscribe
```

This opens https://swxtch.io/pricing in your default browser.

### Manual Payment

1. Go to https://swxtch.io/pricing
2. Choose Premium ($9.99/month)
3. Enter payment method
4. Your subscription activates immediately

### License Verification

Premium subscriptions are verified locally. After subscribing, Swxtch updates your license file at `~/.swxtch/license.json` with subscription details. No external verification required.

## Cancellation & Refunds

### Cancel Anytime

No long-term commitment. Cancel your subscription at https://swxtch.io/account/subscriptions.

- Month-to-month billing
- No early termination fees
- No questions asked

### Refunds

If you cancel within 7 days of subscribing, we offer a full refund. Contact **silasmintori@gmail.com** with your subscription ID.

## FAQ

### Can I use Swxtch after the trial without paying?

No. After 7 days, you need an active Premium subscription to continue using Swxtch. The free trial is designed to let you evaluate the tool risk-free.

### Is the trial automatic? Do I need to sign up online?

No online signup required. The trial starts automatically when you install Swxtch. Just run:

```bash
pip install -e ".[crypto]"
swxtch --license    # Check trial status
```

### Can I reinstall Swxtch to get another free trial?

Trial status is stored in `~/.swxtch/license.json`. If you remove this file, a new trial starts on next run. However, we ask that you respect the spirit of the trial — it's meant for genuine evaluation, not multiple free periods.

### What if I unsubscribe? Can I resubscribe later?

Yes. You can unsubscribe and resubscribe anytime. Premium is month-to-month billing.

### Does Swxtch phone home to verify my license?

No. License verification is **entirely local**. Swxtch never contacts our servers to check if you're subscribed. Your `~/.swxtch/license.json` file is the source of truth.

### What if the subscription file gets corrupted?

Contact support at **silasmintori@gmail.com** with your subscription ID. We can issue a new license file.

### Do I need to stay online to use Swxtch?

No. Swxtch works offline. The boot service and TUI work without internet. Only the initial subscription step requires a network connection.

### Can I use Swxtch on multiple machines?

Each machine tracks its trial independently. If you install Swxtch on a second machine, it gets its own 7-day trial. Subscriptions can cover multiple machines at the same $9.99/month price — contact **silasmintori@gmail.com** for details.

### Is Swxtch open source?

Yes, the source code is available on GitHub (MIT license). You can read, audit, and modify the code. The premium version is the same code with a paid-only feature flag.

### What payment methods do you accept?

We accept:
- Credit cards (Visa, Mastercard, American Express)
- Debit cards
- PayPal (coming soon)

All payments are processed securely through Stripe.

## Support

### During Free Trial

Email: **silasmintori@gmail.com**

Response time: 24-48 hours

### Premium Subscribers

Email: **support@swxtch.io**

Response time: 12 hours (priority)

## Special Cases

### Educational/Non-Profit Use

Contact **silasmintori@gmail.com** for educational or non-profit licensing. We offer discounts for legitimate privacy advocacy and security research.

### Large Deployments

For organizations deploying Swxtch across many machines, contact **enterprise@swxtch.io** for volume licensing.

### Security Researchers

If you're researching Swxtch's security, we offer free Premium access for the duration of your research. Email **research@swxtch.io** with details of your work.

## Business Model

Swxtch uses a **freemium model** to balance accessibility with sustainability:

1. **Free Trial (7 days)** — Let users evaluate the tool risk-free
2. **Premium Subscription ($9.99/month)** — Support ongoing development and maintenance
3. **Open Source** — Code is public (MIT license) for transparency and community contributions

We believe this model:
- ✓ Protects user privacy (no tracking, entirely local license checking)
- ✓ Ensures quality (revenue funds security audits and development)
- ✓ Respects user freedom (code is open source and auditable)

---

**Questions?** Email **silasmintori@gmail.com** — we're here to help!
