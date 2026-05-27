# Data Contract

The stable handoff is:

```text
country profile -> country verification -> discovery artifacts -> route_candidates.md/capture manifest -> prepared.json -> diff.json -> analysis.md -> feishu-payload.json
```

Global UG Radar has no reader evidence mode. Every reportable run starts from current local Android capture artifacts in the selected verified country environment.

## Source Types

- `native_app_local`: real Android app evidence captured in the current verified local country environment.
- `web_pwa`: Web/PWA evidence captured on Android; supplemental only.
- `public_web`: public web evidence; background or hypothesis only.
- `public_web_supplement_only`: public web evidence with no native screenshot gate; never present as an app finding.

## prepared.json

```json
{
  "runId": "2026-W22",
  "createdAt": "2026-05-26T00:00:00+08:00",
  "environment": {
    "device": "android-emulator",
    "countryId": "jp",
    "countryName": "Japan",
    "profileVersion": "2026-05-26",
    "locale": "ja-JP",
    "timezone": "Asia/Tokyo",
    "networkCountry": "JP",
    "countryVerificationStatus": "pass"
  },
  "apps": [
    {
      "id": "example-app",
      "name": "Example App",
      "packageName": "TBD_VERIFY_ON_DEVICE",
      "appVersion": "TBD",
      "loginState": "unknown",
      "status": "not_captured",
      "sourceType": "native_app_local",
      "discovery": {
        "status": "not_started",
        "artifactsDir": null,
        "confirmedUgPages": 0,
        "blockedCandidates": []
      },
      "routes": []
    }
  ]
}
```

## Route Fields

```json
{
  "routeId": "rewards-home",
  "sourceType": "native_app_local | web_pwa | public_web | public_web_supplement_only",
  "entryPath": ["home", "rewards_icon"],
  "status": "captured",
  "screenshots": ["screenshots/after-rewards-tap.png"],
  "hierarchy": ["hierarchy/after-rewards-tap.xml"],
  "ocr": {"keyTexts": ["reward", "points"]},
  "ugCandidate": {
    "isUgPage": true,
    "confidence": "high",
    "ugMechanic": "invite_friends"
  },
  "safetyConcern": null,
  "notes": "Native route reached without sensitive action."
}
```

## Status Values

- `captured`: evidence exists.
- `not_captured`: no capture evidence exists yet.
- `not_started`: discovery or capture has not started.
- `country_env_unverified`: selected-country locale, timezone, network, Google Play, or app-country state is not verified.
- `login_required`: app requires human login recovery.
- `native_app_missing`: native package is not installed or package identity is unknown.
- `install_blocked`: installation is blocked by Play Store sign-in, country, compatibility, or user approval.
- `web_supplement_only`: evidence came from Web/PWA/public web and must not be presented as native-app evidence.
- `route_failed`: route did not reach the target page.
- `device_unavailable`: no Android device/emulator is available.
- `blocked`: safety boundary or app risk-control stopped the run.
- `changed`: meaningful UG change detected.
- `unchanged`: no meaningful UG change detected.
- `needs_review`: insufficient evidence or uncertain classification.
