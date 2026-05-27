# Judge Diff Prompt

Compare current run evidence against baseline or previous run evidence.

Notify only for meaningful UG changes:
- Reward amount, coins, cashback ratio, coupon value, or eligibility changes.
- Invite, task, sign-in, activation, retention, or referral rule changes.
- Entry path, tab, popup trigger, CTA, key visual hierarchy, task card, or progress expression changes.
- User action steps or required conditions change.

Ignore by default:
- Generic banner carousel.
- Unrelated homepage content.
- Tiny wording or style changes.
- Timestamp, badge, recommendation, or feed noise.

Return Chinese JSON:

```json
{
  "status": "changed | unchanged | needs_review",
  "significantChanges": [
    {
      "type": "reward_change | route_change | rule_change | visual_change | cta_change | other",
      "summary": "中文摘要",
      "shouldNotify": true,
      "evidence": ["证据"]
    }
  ],
  "ignoredNoise": ["被过滤的微小变化"]
}
```
