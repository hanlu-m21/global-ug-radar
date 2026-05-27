# Data Contract

The stable handoff is:

```text
country profile -> country verification -> discovery artifacts -> route_candidates.md/capture manifest -> prepared.json -> analysis_pack.json -> diff.json -> analysis.md -> table_image_manifest.json -> feishu-payload.json
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
- `image_upload_failed`: one or more gameplay screenshots could not be uploaded before Feishu table writing.
- `table_image_validation_failed`: Feishu read-back found a missing screenshot, wrong-row screenshot, wrong-cell screenshot, or table-external gameplay screenshot.

## analysis_pack.json

Use `analysis_pack.json` as the default model input for standard runs. It is a lossy index over retained raw artifacts, not the source of truth. Each route card keeps country/app identity, screenshot and hierarchy paths, top visible text, ranked candidate entries, stop phrases, evidence hashes, and explicit raw-fallback reasons.

Open raw screenshots/XML/OCR when `rawFallback.required` is true, when candidate ranking conflicts with the screenshot, or when a reportable row cannot be tied to a route screenshot.

## table_image_manifest.json

The Feishu table image manifest maps every gameplay screenshot to a row and the fixed screenshot cell:

```json
{
  "schemaVersion": "2026-05-27.feishu-table-images.v1",
  "rows": [
    {
      "rowId": "daily-bonus",
      "tableRowIndex": 4,
      "screenshotCell": {"columnName": "玩法截图", "columnIndex": 2},
      "screenshots": [
        {"imageIndex": 1, "path": "/abs/path/screen.png", "placeholder": "{{screenshot:daily-bonus:1}}"}
      ]
    }
  ]
}
```

Direct Feishu writers must upload images first, insert uploaded image tokens into the matching `玩法截图` cell, then read back the document structure before marking delivery complete.
