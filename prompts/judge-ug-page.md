# Judge UG Page Prompt

You are judging whether a selected-country native app screenshot/page is user-growth relevant.

Input:
- App metadata.
- Country profile and country verification status.
- Entry path.
- Screenshot/OCR evidence.
- Any route notes.
- Source type: `native_app`, `web_pwa`, or `public_web`.
- Selected-country keyword hits from `config/ug-signals.json`, when available.

Output Chinese JSON:

```json
{
  "isUgPage": true,
  "confidence": "high",
  "ugMechanic": "invite_friends | tasks | rewards | cashback | coupons | sign_in | activation | retention | receipt_rewards | point_exchange | daily_lottery | walk_to_earn | coupon_ladder | membership_tier | other",
  "countryKeywordHits": ["matched OCR/source terms from config/ug-signals.json"],
  "reason": "中文说明",
  "evidence": ["页面中可见的关键证据"],
  "sourceType": "native_app",
  "safetyConcern": null
}
```

Rules:
- Do not guess beyond evidence.
- Do not mark a page as confirmed when `countryVerificationStatus` is missing or not `pass`.
- Do not describe Web/PWA/public-web evidence as native-app evidence.
- Mark `confidence` as `low` when screenshots/OCR are insufficient.
- Keyword hits can raise priority for inspection, but cannot by themselves make a confirmed UG page.
- Use selected-country source terms as evidence when they are visible in OCR or hierarchy; do not translate invisible terms into evidence.
- If the page enters payment, withdrawal, checkout, transfer, real invite sending, or login verification, set `safetyConcern`.
