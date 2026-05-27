# Smart Discovery

Use this reference when fixed Maestro routes are missing, stale, or too narrow.

## Evidence Priority

1. Native Android app evidence with verified package name, app version, foreground activity, screenshot, hierarchy, OCR, and route path.
2. Web/PWA evidence captured on the Android device when native installation or login is blocked. Label this as supplemental.
3. Public web, AnySearch, social, ad, and app-store evidence. Use only for context or to seed candidate keywords/URLs. Do not use it as a replacement for native app evidence.

App research has a screenshot gate: every app finding or Feishu Doc case must be grounded in at least one real Android app screenshot plus device/app state. If the screenshot is missing, report a blocker such as `device_not_connected`, `login_blocked`, `native_app_missing`, `install_blocked`, or `web_supplement_only`; do not replace it with public-web research.

## First-Run Device Readiness

When `doctor.py` or `adb devices` returns zero devices, do not conclude that the user has no emulator or that the app is unavailable. It only means ADB currently sees no connected device.

- First check whether Android Studio, Android Emulator, or another emulator already exists.
- If an emulator exists, guide the user to start it from Android Studio Device Manager or with `emulator -list-avds` followed by `emulator -avd <name>`.
- If no suitable emulator exists, provision a disposable Android research AVD automatically where possible before any app research. Use a Google Play system image. Check available disk space first: prefer 50GB local storage when possible, otherwise use the smaller storage size recommended by `doctor.py` so the emulator fits the user's computer. If installation needs a GUI step, license acceptance, admin password, or the machine lacks disk/network prerequisites, report the exact blocker and wait for the user.
- Rerun `adb devices -l` and `doctor.py` after the emulator is visible. Only proceed when a row in state `device` is present.
- Do not pivot to public web as the main evidence source just because ADB is temporarily disconnected.

## Native App Setup

- Prefer Google Play installation for the native app.
- If Google Play asks for sign-in, stop and ask the user to handle it manually.
- After Google Play is ready, present the selected country's configured app choices from `config/countries.json` / `config/apps.example.json`. If no default apps are configured, ask the user for product names or package IDs before installing.
- Do not enter Google credentials, app credentials, OTP, captcha, or identity checks.
- Do not sideload an APK unless the user explicitly approves the source and risk.
- After installation, verify package name and version with device state before capture.

## Discovery Loop

1. Capture baseline state: screenshot, UI hierarchy, foreground package/activity, app version, language, network/region, and timestamp.
2. Score visible entries using `config/ug-signals.json`. Prefer the selected country's `highPriorityKeywords`, then `safeEntryLabels`, and treat `stopPhrases` as safety boundaries.
3. Tap only safe navigation candidates: tabs, profile/menu entries, wallet/benefits/rewards centers, non-committing banners, task-center entries, and floating reward icons.
4. After each tap, capture screenshot and hierarchy, record the route path, classify the page, then backtrack safely.
5. Keep a route graph and a short candidate report with confirmed pages, rejected pages, blocked paths, and next human actions.

## Keyword Sources

Load `config/ug-signals.json` when scoring routes:

- `highPriorityKeywords`: OCR/source-text terms that usually indicate UG mechanics.
- `safeEntryLabels`: low-risk navigation labels worth inspecting first.
- `stopPhrases`: terms that should stop automation and ask for human handling.

Do not translate a keyword match into a confirmed finding by itself. A reportable row still needs a real screenshot, route path, country verification, app package/version, hierarchy, and OCR.

## Stop Conditions

Stop immediately and ask for human handling when the screen asks for login, OTP, captcha, account security, identity, contacts, notification permission that gates progress, social share confirmation, invite sending, payment, checkout, withdrawal, transfer, order placement, or wallet confirmation.

If the UI is blank, partially loaded, or clearly Web/PWA, record package/activity and source type before continuing. Do not treat a Chrome WebAppActivity as native-app evidence.

## Replay Rule

Promote a path to `flows/maestro/` only after discovery confirms it reaches a relevant page without sensitive actions. Maestro flows should replay confirmed routes and capture evidence. They should not blindly explore unknown pages.

When replay fails, mark the route as `route_failed`, attach the last screenshot/hierarchy, and rerun smart discovery for that app.

## Reporting Rule

When the user asks whether there are other incentive pages, report:

- whether each finding passed the native screenshot gate;
- the source type for each finding: `native_app`, `web_pwa`, or `public_web`;
- which native routes were visited;
- which UG candidates were blocked, rejected, or not found;
- why the answer is high-confidence or still uncertain.
