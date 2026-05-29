# Safety Boundaries

## Never Automate

- Login, password entry, SMS/email code entry, captcha, risk-control verification, or identity verification.
- Google Play sign-in, app-store account setup, or credential recovery.
- Invite sending, contact import, social sharing confirmation, payment, transfer, withdrawal, order placement, checkout, refund, or wallet actions.
- Sideloading a third-party APK without explicit user approval of the source and security risk, or without a run config that preauthorizes the approved source for a disposable research emulator.
- Clearing app data or uninstalling an app unless the user explicitly approves it, or the run config marks the app/emulator as disposable and preauthorizes reset.
- Any action that spends money, changes account balance, contacts real users, or changes account security state.
- Silent emulator provisioning. Installing the skill must never create, install, or start an emulator. Before creating or starting a research emulator, check disk and physical memory, show the planned storage size, and wait for explicit user approval.
- Default 50GB provisioning. Use the smaller `doctor.py` recommendation by default, normally 24GB and never below 12GB. Use 50GB only when the user explicitly asks for high-capacity mode and the machine has enough disk and memory headroom.

## Human Intervention Required

Stop and ask the user to handle the app manually when:

- The app asks for login, captcha, OTP, identity, payment, wallet, or risk confirmation.
- Google Play requires sign-in before installing an app.
- The route enters checkout, transfer, withdrawal, order, invite-send, or contact-permission screens.
- The app appears to block emulator usage or country/network state, unless the selected country profile can resolve the environment issue without login, captcha, risk-control bypass, payment, invite, or account actions.
- The route path has changed and safe navigation is no longer clear.
- The only available evidence is Web/PWA instead of the native app; label the result and ask whether to continue with supplemental evidence.

## Data Handling

- Keep screenshots, local state, baseline, logs, and secrets out of the skill folder.
- Use `~/.global-ug-radar/` by default.
- Do not commit screenshots, account state, Feishu tokens, app tokens, cookies, or credential files.
- If screenshots contain personal data, mark the case for manual review and avoid highlighting personal information in the report.
- If APK sideloading is explicitly approved, record the source and mark all findings with APK provenance risk.
- If APK sideloading or app-data reset is preauthorized by config, record the config/source, action taken, app version, and evidence path in the run notes.
