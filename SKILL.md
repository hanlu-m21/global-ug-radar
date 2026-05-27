---
name: global-ug-radar
description: Token-efficient, country-first native Android user-growth competitor research for the United States, Brazil, Japan, and Korea. Use when Codex needs to verify country emulator/Google Play/app gates, research an already-open Android app, install configured native apps when needed, capture screenshots/hierarchy/OCR evidence, summarize UG candidates with scripts, compare baseline changes, and prepare Chinese Feishu message/Doc outputs.
---

# Global UG Radar

## Core Contract

Run native-app UG research only after the selected country environment is verified. Optimize tokens by summarizing evidence before analysis; do not reduce the evidence captured.

Supported countries are exactly:

- `us` - United States
- `br` - Brazil
- `jp` - Japan
- `kr` - Korea

Do not offer Europe in this skill. If the user asks for Europe, explain that this skill requires a specific country profile first.

## Operating Modes

Choose the narrowest mode that matches the user's request:

1. `research-current-app` - default when the target app is already open on the test device.
2. `setup-and-install` - use when the country emulator, Google Play state, or target app is not ready.
3. `deliver` - use when evidence already exists and the user asks for Feishu/Doc output.

## Load Only When Needed

Keep `SKILL.md` as the router. Load references only for the active stage:

- `config/countries.json`: country profiles, locale, timezone, AVD name, network country, and default apps.
- `config/apps.example.json`: supported-country app candidates.
- `config/ug-signals.json`: country-language UG keywords, safe entry labels, and stop phrases.
- `references/country-environment.md`: read only for emulator provisioning or country verification failures.
- `references/safety-boundaries.md`: read only when an action may cross login, payment, invite, identity, or wallet boundaries.
- `references/smart-discovery.md`: read only for manual route exploration or unclear UG candidates.
- `references/output-template.md`: read only immediately before drafting or writing Chinese Feishu output.
- `scripts/doctor.py`: local tooling, storage, and selected-country readiness.
- `scripts/provision_country_avd.py`: create/start research-grade Google Play AVDs and country ICC profiles.
- `scripts/verify_country_env.py`: hard country-environment validation gate.
- `scripts/capture_current_app.py`: capture the foreground Android app and write a compact `evidence_summary.json` from screenshot, hierarchy, package, and country-signal matches.
- `scripts/build_analysis_pack.py`: merge captured summaries into the default `standard + raw fallback` model input.
- `scripts/prepare_run.py`: create a prepared run shell when no capture manifest exists.
- `scripts/render_feishu_table.py`: validate structured findings, render the fixed 5-column Feishu table XML, and emit the screenshot-to-cell manifest.
- `scripts/deliver.py`: create local Feishu payloads and run strict table-image preflight; direct Feishu writes still require explicit user destination confirmation.

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

## Fast Path: Current App Research

Use this path when the user says the target app is already open on the test device.

1. Identify the selected country from the user request. If missing, ask for `us`, `br`, `jp`, or `kr`.

2. Run country verification. Use manual confirmation flags only when the user has explicitly confirmed Google Play and target-app country state:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID>
```

3. Capture the foreground app and compact evidence summary:

```bash
python3 scripts/capture_current_app.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --run-id <RUN_ID> --route-id baseline
```

4. Read the generated `evidence_summary.json` first. For more than one captured route, build the standard analysis pack:

```bash
python3 scripts/build_analysis_pack.py --state-dir ~/.global-ug-radar --run-id <RUN_ID>
```

Use `analysis_pack.json` as the default model input. Open raw XML or screenshots only when:

- the summary has too few visible texts or candidates;
- candidate ranking conflicts with the screenshot;
- a sensitive boundary needs manual verification;
- a reportable row cannot be tied to a screenshot path and route id.

5. Explore only safe entries from `candidateEntries`. Capture each visited route with `capture_current_app.py --route-id <ROUTE_ID>`. Stop at login, OTP, captcha, identity, payment, withdrawal, invite send, order, contact import, or risk-control screens.

6. Analyze only from native evidence. Every user-facing gameplay row must point to a real screenshot path retained in the run directory.

## Setup and Install Path

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
- Also read `config/apps.example.json` for the selected country app metadata.

8. Install selected apps from Google Play when available. If Play Store blocks installation by country, account, compatibility, or risk state, capture the blocker and stop with `install_blocked`.

9. Ask the user to sign in to each selected app manually. Stop at login, OTP, captcha, identity, wallet, payment, withdrawal, invite-send, contact-permission, or risk-control screens.

10. Re-run country verification with manual confirmations after app login:

```bash
python3 scripts/verify_country_env.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --confirm-google-play-country --confirm-target-app-country
```

Only continue if the result status is `pass`.

11. Run smart discovery. Prefer `scripts/capture_current_app.py` and its `evidence_summary.json` over reading full XML/OCR. Read `references/smart-discovery.md` only when fixed routes are stale, route scoring is ambiguous, or manual exploration is needed.

12. Prepare structured run JSON:

```bash
python3 scripts/prepare_run.py --state-dir ~/.global-ug-radar --country <COUNTRY_ID> --apps-config config/apps.example.json
```

13. Analyze only from native app evidence. Default to `standard + raw fallback`: build/read `analysis_pack.json` first, then open raw screenshots/XML/OCR only for the fallback reasons listed in the pack or when a reportable row cannot be tied to a screenshot and route id. Do not load every prompt by default. For single-app current-state research, use `evidence_summary.json` or `analysis_pack.json`, the evidence gate, and `references/output-template.md`. For batch or diff workflows, load only the specific prompt needed:

- `prompts/judge-ug-page.md`
- `prompts/analyze-ug-case.md`
- `prompts/judge-diff.md`
- `prompts/feishu-digest.md`

14. Prepare delivery artifacts as dry-run/local payloads first:

```bash
python3 scripts/deliver.py --state-dir ~/.global-ug-radar --run-id <RUN_ID> --dry-run --strict-table-images --table-manifest <TABLE_IMAGE_MANIFEST_JSON>
```

Only send Feishu messages or write Feishu Docs after the user explicitly confirms destination and credential path.

## Token-Efficient Evidence Rules

- Capture full screenshots, hierarchy, package data, country checks, and route paths; summarize them for model analysis.
- Use `standard + raw fallback` by default. Expected savings are 45-65% tokens and 30-55% response-time improvement on multi-route runs, with target quality loss 0-2% when fallback is followed.
- Treat `analysis_pack.json` and `evidence_summary.json` as lossy indexes, not as the source of truth. Raw artifacts remain available for fallback.
- Do not load complete UI XML unless the summary is insufficient.
- Do not load every prompt file by default. For single-app current-state research, use the evidence gate below plus `references/output-template.md`.
- If compression creates uncertainty, read the raw artifact and report the uncertainty instead of guessing.
- Do not use top-candidate-only fast mode for final reports unless the user explicitly asks for a quick scan and accepts missed-candidate risk.

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

Read `references/output-template.md` before drafting Chinese reports or writing Feishu Docs. Keep the existing 5-column Feishu table contract:

- `一句话介绍`
- `玩法截图`
- `目标`
- `亮点分析`
- `可借鉴点`

Keep evidence status internal unless the user explicitly asks for operational status.

When writing a Feishu Doc, prefer structured JSON plus the renderer instead of hand-writing table XML:

```bash
python3 scripts/render_feishu_table.py --input <FINDINGS_JSON> --output <TABLE_XML> --image-manifest-output <TABLE_IMAGE_MANIFEST_JSON> --require-local-images
```

The JSON rows must include `rowId`, `oneLine`, `screenshots`, `goal`, `highlights`, and `takeaway`. The renderer validates goal enums, row lengths, local screenshot readability, and the fixed 5-column shape. `screenshots` entries should be local image paths or objects with `path` plus optional `label` / `caption` / `state`.

Before writing a Feishu Doc, upload every screenshot first and map the returned image/file token back to `TABLE_IMAGE_MANIFEST_JSON`. If any image upload fails after retry or format/size recovery, stop as `image_upload_failed` before generating review text or continuing analysis. Do not spend tokens reviewing a document with missing images.

Screenshots must be inserted into the correct `玩法截图` cell of the corresponding gameplay row. Do not place gameplay screenshots above the table, below the table, between rows, or in any free-form block outside the research output table. If a row needs multiple screenshots, put them in that row's `screenshots` list / `玩法截图` cell; if screenshots belong to different mechanics, split them into separate gameplay rows.

After writing to Feishu Docs, read back the document structure before marking delivery complete. Verify that every uploaded screenshot appears inside a table, every uploaded screenshot is in the matching row's `玩法截图` cell, no uploaded gameplay screenshot appears outside the table, and the local screenshot count equals the Feishu document screenshot count. If any check fails, classify delivery as `table_image_validation_failed` and do not claim success.

## Decision Notes

This skill is intentionally country-profile based, not a single huge country document. Add or change country behavior in `config/countries.json` and `references/country-environment.md`, then validate with the scripts. Do not expand `SKILL.md` with country-specific playbooks.
