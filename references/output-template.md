# Output Template

Use this template for every Feishu Doc research output. The only user-facing goal is: 让设计师 3 秒看懂一个玩法，30 秒决定能不能借鉴。

Use Chinese-first prose. Preserve product names, mechanism names, and UI component names in their original source language when that name is part of the product surface. Selected-country UI text can remain inside screenshots or OCR evidence only.

## Feishu Table Contract

All research findings must be written as Feishu tables in the target document. Do not output free-form case sections, long market analysis, SWOT/PEST, or extra user-facing columns.

Create one table per product. The table has exactly 5 columns:

```markdown
| 产品名称 | <产品名> |  |  |  |
|---|---|---|---|---|
| 产品介绍 | <≤80 字。必含：所属公司 / 地区、当前量级数据（下载量 / 榜单 / 关键转化指标）、一句话核心理念> |  |  |  |
| 一句话介绍 | 玩法截图 | 目标 | 亮点分析 | 可借鉴点 |
| <玩法 1> | <1-3 张截图> | <固定枚举 1 个> | <编号列表，最多 6 条> | <TikTok 激励场景落地建议> |
| <玩法 2> | <1-3 张截图> | <固定枚举 1 个> | <编号列表，最多 6 条> | <TikTok 激励场景落地建议> |
```

When writing directly into Feishu Docs, merge row 1 columns 2-5 for the product name, and merge row 2 columns 2-5 for the product introduction. If the local artifact is Markdown, keep the same 5-column shape and leave the unused cells blank.

Do not add or remove columns. Do not add `证据状态`, `变化判断`, `来源与更新时间`, `产品设计亮点`, or `视觉设计亮点` as user-facing columns. Evidence metadata remains an internal validation gate.

## Product Rows

- `产品名称`: product name only. Optional owner/reviewer can be appended in the same cell if the user explicitly asks.
- `产品介绍`: ≤80 Chinese characters. Must include company/region, current scale data, and one-sentence core idea.
- Current scale data can be downloads, chart rank, MAU/DAU, conversion metric, or other directly evidenced metric.
- If current scale data is missing from native evidence and no approved supplemental source exists, write `量级数据待补充` inside the 80-character limit instead of fabricating.

## Gameplay Columns

### 一句话介绍

- ≤15 Chinese characters.
- Use `[关键词]+[机制名]`, for example `货币化暗示`, `高上限博弈：Daily Bonus Ladder`.
- Avoid adjective stacking.
- Ban `非常`, `极其`, `创新性地`.

### 玩法截图

- Include 1-3 key screenshots.
- Put screenshots inside the `玩法截图` cell of the corresponding gameplay row. Do not place gameplay screenshots above the table, below the table, between rows, or in any free-form block outside the research output table.
- For direct Feishu Doc writes, upload all screenshots before writing the table, then insert each uploaded image token only into the matching row's `玩法截图` cell according to the table image manifest.
- If any screenshot cannot be uploaded or cannot be inserted into its table cell, stop as `image_upload_failed` or `table_image_validation_failed` before downstream review.
- If multiple screenshots explain one mechanic, keep them in the same row's `玩法截图` cell. If screenshots explain different mechanics, split them into separate gameplay rows.
- Add state labels only when needed, and each label must be ≤4 Chinese characters, such as `解锁前`, `解锁中`, `解锁后`.
- Screenshots must independently explain the mechanic without relying on text explanation.
- For `native_app_local` rows, every reportable gameplay row must have a real Android app screenshot. If no screenshot exists, do not create a native gameplay row; report the blocker outside the table only if the user needs operational status.
- For user-approved `inspire` rows, screenshots may come from `inspire-research` only after the region gate passes. Keep the source status internal and still put the screenshot inside the correct `玩法截图` cell.

### 目标

Choose exactly one value from this enum:

- 任务转化
- 用户分层
- 提升参与意愿
- 促活留存
- 付费转化
- 拉新裂变
- 品牌建设
- 投稿激励
- 分享传播

Do not invent goals. One gameplay row maps to one core goal only.

### 亮点分析

- Use a numbered list: `1. 2. 3.`
- Maximum 6 items.
- Each item must be ≤70 Chinese characters.
- Each item must include a concrete number or a mechanism name, such as `$0.05-$0.25`, `1000 Coins = $1`, `3 天 / 7 天阶梯`, `Daily Bonus Ladder`.
- Bold the key term, such as `**阶梯式限时奖金**` or `**卡片横滑组件**`.
- Start with the conclusion directly. Do not use `为什么...` as the bold lead-in.
- Analyze the local incentive logic, not only the visible UI. Mention holiday, currency, share channel, social habit, object choice, or task cost when it explains the design.
- Ban mystical descriptions, vague quantities, and value judgments, including `用户体验好`, `很多`, `大量`, `这很棒`.

### 可借鉴点

- ≤80 Chinese characters.
- Use this sentence shape: `TikTok可考虑在[具体场景]中[具体动作],以[预期效果]`.
- Must name a concrete TikTok incentive landing scene, such as 邀请页, 分享链路, 任务页, 签到, 视频任务, 奖励中心, 提现门槛, Push 通知, 复访入口, 投稿入口.
- Keep the takeaway about incentives. Do not write generic product/content advice.
- If the mechanic does not fit TikTok, write `不建议直接照搬，原因:<≤30 字>`.

## Region Gate for Inspire Materials

Before using an Inspire screenshot, verify the requested country from at least one strong signal and no contradictory signal:

- Strong signals: source region metadata, app listing region, local currency, campaign copy, local holiday context, local social/share channel, or region-specific legal/payment wording.
- Brazil signals: `R$`, Brazilian Portuguese copy, Brazil campaign context, Brazil app metadata, or Brazil-local channels.
- Reject as `region_mismatch`: `Rp`, Indonesian copy, Indonesian metadata, or any source region that conflicts with the requested country.
- Mark as `region_unverified`: language-only evidence, cropped screenshots with no country signal, or copied campaign assets with unclear market.

Do not fill a confirmed country row with `region_mismatch` or `region_unverified` material.

## Incentive Activity Analysis Rules

Use this thinking path for `亮点分析`:

- First classify the incentive: 拉新裂变、促活留存、任务转化、投稿激励、分享传播、付费转化、用户分层、品牌建设.
- Then explain the local context: why this country, holiday, currency, channel, relationship, object, or task fits the incentive.
- Then break down the mechanism: threshold, countdown, reward split, progress bar, unlock step, custom content, share surface, or reminder loop.
- Finally write the TikTok takeaway for an incentive scene, especially sharing, invite, check-in, task completion, reward claim, withdrawal, return visit, or posting.

Preferred highlight style:

- `**首邀低门槛**：R$299 拆成 R$100/R$100/R$99，先让用户完成第 1 邀`
- `**定制化分享理由**：用户分享的是给妈妈的贺卡，不是冷冰冰的任务链接`
- `**7 天短周期目标**：May 4-May 11 把签到、看视频、邀请压进一轮冲刺`

## Content Rules

Must include when evidenced:

- 数字化指标：金额、时长、转化率、用户量、榜单或下载量。
- 机制名称：保留英文原名，如 `Daily Bonus Ladder`。
- 视觉 / 交互组件名：如卡片横滑、暗黑模式、入账音效。
- 目标用户画像：仅当它影响设计决策，如年轻男性、游戏玩家。

Must remove:

- 商业模式、财报、融资历史。
- 创始人故事、公司沿革。
- 技术架构、后端实现。
- 长篇市场分析、SWOT/PEST。
- 主观感受，如 `我觉得`, `很惊艳`。
- 翻译腔，如 `它是一个...的产品`。

## Language Style

- Chinese first. Product names, mechanism names, and UI component names can remain English.
- Prefer short sentences. Each sentence should be ≤25 Chinese characters where practical.
- Prefer verbs over nominalized phrasing, such as `筛选出 Power Users`.
- Do not use emoji or exclamation marks.

## Self-Check Before Output

Before writing or sending the Feishu Doc, verify:

- The whole table can be scanned in one screen.
- Every `亮点分析` item has a concrete number or mechanism name.
- Every `可借鉴点` names a TikTok landing scene.
- No business, finance, technical, or company-history content unrelated to design decisions remains.
- Every `一句话介绍` is ≤15 Chinese characters.
- Screenshots are independently readable.
- All screenshot uploads succeeded before table writing started.
- All gameplay screenshots are inside the correct row's `玩法截图` cell, not outside the table.
- A read-back structure check confirms no gameplay screenshot exists outside the table and no row screenshot is in the wrong cell.
- The final structure matches the reference: product rows first, then the fixed 5-column gameplay table.

## Native Evidence Gate

- Evidence status is an internal validation signal. Do not add a dedicated `证据状态` row, field, or table item to user-facing Feishu Docs or Chinese reports unless the user explicitly asks for it. If evidence is insufficient, describe the limitation briefly in the conclusion, change judgment, or source note instead.
- `native_app_local` 案例必须包含本次真实 App 截图、包名、版本、前台 Activity、国家 profile、语言/时区/网络国家、账号状态、采集时间和入口路径。
- `public_web` 只能作为背景或假设来源，不能替代 App 截图生成案例分析。
- Global UG Radar 不使用读者模式或中心证据库作为主路径；每个用户都应完成本地安卓模拟器采集，并通过所选国家环境验证。
- 如果 `adb devices: 0`，写 `device_not_connected`，并说明下一步是启动/安装虚拟机或修复 ADB 连接。
- 如果进入登录、验证码、通讯录、分享、支付、提现、下单或风控页，写 `login_blocked` 或对应阻塞类型，等待人工处理。
