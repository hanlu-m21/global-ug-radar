# Country Environment

Use this reference before installing apps or starting research for `us`, `br`, `jp`, or `kr`.

## Target Standard

Build a research-grade country emulator, not merely an emulator whose display language was changed.

The target country is ready only when these layers agree or are explicitly documented as emulator residual risk:

1. Fresh Google Play AVD for the selected country, without stale snapshots.
2. Host/emulator network egress country matches `networkCountry`.
3. Android runtime locale resolves to the profile locale in `adb shell am get-config`.
4. Timezone and geolocation match the profile.
5. SIM profile exposes the configured MCC/MNC through `gsm.sim.*` and runtime config.
6. Google Play shows target-country UI/recommendations/rankings after user sign-in.
7. Target app shows target-country feed/content after user sign-in.
8. Screenshots, hierarchy, OCR, package/version, and verification JSON are captured in the run folder.

If any acceptance gate fails, stop and report `country_env_unverified` or the more specific blocker.

## Known Emulator Limits

Google Play emulator images can retain built-in radio registration values such as `gsm.operator.iso-country=us` and `gsm.operator.numeric=311740` even after a country SIM profile is supplied. Treat this as a warning only when the country profile sets `operatorResidualPolicy: "warn"` and these are all true:

- `gsm.sim.operator.iso-country` and `gsm.sim.operator.numeric` match the selected country profile.
- `am get-config` contains the expected locale and MCC/MNC.
- VPN/proxy egress is in the selected country.
- Google Play and the target app both show selected-country service-side content.

Do not hide this residual risk in notes. Record it in verification output.

## Provision AVD

Use the provisioning script instead of hand-assembling AVDs:

```bash
python3 scripts/provision_country_avd.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --dry-run
```

After the user approves the displayed storage/memory plan, create or start the emulator explicitly:

```bash
python3 scripts/provision_country_avd.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --storage-gb <DOCTOR_RECOMMENDED_GB> --confirm-resource-use --start
```

The script creates or reuses `researchAvdName`, configures Google Play, disables snapshots, sets the data partition size, generates a country ICC profile, starts with `-icc-profile`, applies timezone/geolocation, and opens Android language settings. Default storage should come from `doctor.py` and is normally 24GB. Use 50GB only when the user explicitly asks for high-capacity mode.

If system-image creation fails, install the reported Google Play system image with `sdkmanager`, then rerun the script.

## Apply Runtime State

Use the profile values from `config/countries.json`:

```bash
adb shell cmd alarm set-timezone <timezone>
adb emu geo fix <longitude> <latitude>
```

`adb shell settings put system system_locales <locale>` is only a preparatory hint. It is not sufficient proof that Android resources, Google Play, or apps resolve to the selected country.

## Language Switch

Switch the system language through Android Settings:

```bash
adb shell am start -a android.settings.LOCALE_SETTINGS
```

Add/select the profile language and move it to the first position. Confirm the system-language change dialog when Android asks.

Use `adb shell am get-config` as the canonical automated proof:

- Japan: expect a token like `mcc440-mnc10-ja-rJP`.
- Brazil: expect `pt-rBR` plus the configured Brazil MCC/MNC.
- United States: expect `en-rUS` plus the configured US MCC/MNC.
- Korea: expect `ko-rKR` plus the configured Korea MCC/MNC.

Do not accept `settings get system system_locales` alone. It can return the target locale while the runtime UI remains another language.

## Verify Environment

Run automated verification before login-sensitive work:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID>
```

After the user has manually confirmed Google Play country and target app country state, run:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --confirm-google-play-country --confirm-target-app-country
```

Proceed only when status is `pass`. The script checks device visibility, runtime locale, locale setting, timezone, SIM country, MCC/MNC, network country through fallback providers, and manual Play/app confirmations.

## Google Play Gate

Open Google Play only after automated country checks are clean or have only documented radio-residual warnings. The user must sign in manually.

Capture evidence that Google Play is target-country service-side content:

- screenshot of the Play home or rankings page;
- UI hierarchy/OCR containing `playStoreUiSignals` from `config/countries.json`;
- visible target-country recommendations, rankings, app names, currency, or copy;
- verification JSON from `verify_country_env.py`.

If Play Store rankings or recommendations are not target-country, stop. Do not continue app research as confirmed country evidence.

## Target App Gate

After installation and user login, verify the app itself:

- capture home/feed/reward/task pages as screenshots plus hierarchy/OCR;
- check locale/currency/merchant/feed/ranking signals for the target country;
- ask the user to confirm the app is showing target-country content when the state depends on account history or risk controls.

If the app shows a non-selected-country feed, capture the blocker and mark `country_env_unverified`.

## Manual Boundaries

The agent may open Google Play, Settings, or target apps, but the user must handle:

- Google Play sign-in and country/account verification;
- app login, OTP, captcha, identity, wallet, payment, withdrawal, or risk-control steps;
- any Play Store country/account correction.

Do not enter credentials or attempt to bypass country, captcha, risk-control, or account restrictions.

## Recovery

- If network country mismatches, ask the user to enable the correct VPN/proxy and rerun verification. A single provider HTTP 429 is not enough to prove mismatch; use fallback provider output.
- If runtime locale mismatches, reopen Android Language settings and move the target language to the top.
- If SIM country mismatches, start the AVD with the generated ICC profile from `scripts/provision_country_avd.py`.
- If Google Play country mismatches, stop. The user must provide an account usable for the selected country.
- If the app still shows a non-selected-country feed after login, capture the screenshot, mark `country_env_unverified`, and ask for human recovery.
