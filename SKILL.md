---
name: global-ug-radar
description: Country-first native Android user-growth competitor research for the United States, Brazil, Japan, and Korea. Use when Codex needs to ask the user to choose a country, provision or start a research-grade country Android Google Play emulator, verify runtime locale/MCC/SIM/timezone/geolocation/network/Google Play/app content country gates before research, prompt for manual Google Play and app login, install selected native apps, capture screenshots/hierarchy/OCR evidence, discover UG pages such as invite/reward/task/cashback/sign-in flows, compare baseline changes, and prepare Chinese Feishu message/Doc outputs.
---

# Global UG Radar

## Core Rule

Run native-app UG research only after the selected country environment is verified.

Supported countries are exactly:

- `us` - United States
- `br` - Brazil
- `jp` - Japan
- `kr` - Korea

Do not offer Europe in this skill. If the user asks for Europe, explain that this skill requires a specific country profile first.

## Architecture

Keep the workflow stable by using progressive disclosure:

- `SKILL.md`: country-first workflow and hard gates only.
- `config/countries.json`: country profiles, locale, timezone, AVD name, network country, and default apps.
- `references/country-environment.md`: how to apply and verify country-specific emulator state.
- `references/safety-boundaries.md`: actions that require human handling.
- `references/smart-discovery.md`: native app route discovery.
- `references/output-template.md`: Chinese Feishu output contract.
- `assets/iccprofile_android_emulator_base.xml`: emulator ICC template used to generate country SIM profiles.
- `scripts/doctor.py`: local tooling, storage, and selected-country readiness.
- `scripts/provision_country_avd.py`: create/start research-grade Google Play AVDs and country ICC profiles.
- `scripts/verify_country_env.py`: hard country-environment validation gate.

## Hard Boundaries

- Only observe, capture screenshots, record paths, and analyze.
- Never enter Google Play credentials, app passwords, OTP, captcha, identity checks, payment data, invite sends, withdrawals, orders, transfers, contact import, or sensitive confirmations.
- Do not fabricate findings when screenshots, OCR, hierarchy, package/version, or country verification are missing.
- Do not treat `adb devices: 0` as proof that no emulator exists. Check AVDs and recover the ADB connection first.
- Before creating an emulator, check disk space. Prefer 50GB storage when possible; otherwise choose the smaller size recommended by `doctor.py` while preserving local free-space headroom.
- Do not continue research if the emulator is in a non-selected-country state. Report the failed check and the recovery step.
- Do not reuse an old AVD or snapshot when country conformity matters. Use the selected country's research AVD and cold boot path.
- Do not accept language-only configuration as country proof. Runtime locale, SIM/MCC, network egress, Google Play content, and app content must be checked.
- Store runs, screenshots, baselines, logs, and secrets under `~/.global-ug-radar/` or the user-provided state directory, never inside the skill folder.

## Workflow

1. Ask the user to choose one country: `us`, `br`, `jp`, or `kr`.

2. Load the selected profile from `config/countries.json`. If the country is missing or ambiguous, stop and ask for a supported country.

3. Run doctor with the selected country:

```bash
python3 scripts/doctor.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID>
```

Use the returned `storage.recommendedEmulatorGb`, `country.researchAvdName` or `country.recommendedAvdName`, locale, timezone, and network country. For country-conforming research, prefer the selected `researchAvdName`; only reuse an existing AVD when it was provisioned by this skill for the same country and has no stale snapshot dependency.

4. Provision or normalize the selected-country research emulator. Read `references/country-environment.md`, then run:

```bash
python3 scripts/provision_country_avd.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --storage-gb <DOCTOR_RECOMMENDED_GB> --start
```

Use a fresh `researchAvdName` from `config/countries.json` when the user requires country-conforming research. The script must generate the country ICC profile, disable stale snapshots, start with `-icc-profile`, apply timezone/geolocation, and open Android language settings. Finish the Android Settings language switch by putting the profile language first, then verify with `adb shell am get-config`.

5. Verify country environment:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID>
```

This script must pass automated checks for device visibility, runtime locale, locale setting, timezone, runtime MCC/MNC, SIM country, network country, and emulator radio residual policy. It also requires manual confirmation flags for Google Play country and target-app country state before research can start.

6. Ask the user to sign in to Google Play manually. Do not enter or store credentials. Continue only after screenshots/OCR/hierarchy show Google Play recommendations or rankings for the selected country and the user confirms Google Play is usable for that country.

7. Present target apps:

- If `config/countries.json` has `defaultApps`, show those first.
- If no default apps are configured, ask the user for product names or package IDs.
- For Brazil, the default first-version apps remain `Mercado Livre`, `PicPay`, `Shopee`, and `Kwai`.

8. Install selected apps from Google Play when available. If Play Store blocks installation by country, account, compatibility, or risk state, capture the blocker and stop with `install_blocked`.

9. Ask the user to sign in to each selected app manually. Stop at login, OTP, captcha, identity, wallet, payment, withdrawal, invite-send, contact-permission, or risk-control screens.

10. Re-run country verification with manual confirmations after app login:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --confirm-google-play-country --confirm-target-app-country
```

Only continue if the result status is `pass`.

11. Run smart discovery. Read `references/smart-discovery.md`, capture baseline screenshots/hierarchy/OCR, record safe route paths, and stop at sensitive actions.

12. Prepare structured run JSON:

```bash
python3 scripts/prepare_run.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --apps-config config/apps.example.json
```

13. Analyze only from native app evidence. Use:

- `prompts/judge-ug-page.md`
- `prompts/analyze-ug-case.md`
- `prompts/judge-diff.md`
- `prompts/feishu-digest.md`

14. Prepare delivery artifacts as dry-run/local payloads first:

```bash
python3 scripts/deliver.py --state-dir ~/.global-ug-radar --run-id <RUN_ID> --dry-run
```

Only send Feishu messages or write Feishu Docs after the user explicitly confirms destination and credential path.

## Evidence Gate

Every reportable gameplay row must include:

- selected country id and profile version;
- verified runtime locale, timezone, geo, SIM country/MCC/MNC, and network country;
- recorded emulator radio residual warning when applicable;
- manual Google Play country confirmation;
- manual target app country confirmation;
- Google Play target-country recommendation/ranking screenshot or blocker;
- target app target-country content screenshot or blocker;
- native app package name, version, foreground activity, account state, capture time, route id, screenshot, hierarchy, and OCR.

If any gate is missing, classify the result as `country_env_unverified`, `login_blocked`, `device_not_connected`, `native_app_missing`, `install_blocked`, `not_captured`, or `web_supplement_only`. Do not write it as a confirmed app finding.

## Output

Read `references/output-template.md` before drafting Chinese reports. Keep the existing 5-column Feishu table contract:

- `一句话介绍`
- `玩法截图`
- `目标`
- `亮点分析`
- `可借鉴点`

Keep evidence status internal unless the user explicitly asks for operational status.

## Decision Notes

This skill is intentionally country-profile based, not a single huge country document. Add or change country behavior in `config/countries.json` and `references/country-environment.md`, then validate with the scripts. Do not expand `SKILL.md` with country-specific playbooks.
