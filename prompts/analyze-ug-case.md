# Analyze UG Case Prompt

Analyze only from prepared JSON, screenshots, OCR, and route metadata. Do not fabricate missing competitor findings.

Do not create a confirmed gameplay row unless `countryVerificationStatus` is `pass`.

Return only Feishu-table-ready Chinese output. The user-facing goal is: 让设计师 3 秒看懂一个玩法，30 秒决定能不能借鉴。

Create one fixed 5-column table per product. Do not add free-form sections or extra columns.

```markdown
| 产品名称 | <产品名> |  |  |  |
|---|---|---|---|---|
| 产品介绍 | <≤80 字。必含：所属公司 / 地区、当前量级数据、一句话核心理念> |  |  |  |
| 一句话介绍 | 玩法截图 | 目标 | 亮点分析 | 可借鉴点 |
| <≤15 字：[关键词]+[机制名]> | <1-3 张关键截图，必要时加 ≤4 字状态标注> | <固定枚举 1 个> | <最多 4 条编号列表> | <TikTok 落地建议> |
```

Column rules:
- `一句话介绍`: ≤15 字，句式 `[关键词]+[机制名]`。禁止 `非常`、`极其`、`创新性地`。
- `玩法截图`: 1-3 张关键截图。截图必须能独立说明玩法。没有真实 Android App 截图时，不生成玩法行。
- `目标`: 只能选 1 个：任务转化 / 用户分层 / 提升参与意愿 / 促活留存 / 付费转化 / 拉新裂变 / 品牌建设。
- `亮点分析`: 编号列表，最多 4 条；每条 ≤60 字；每条必须含具体数字或机制名；关键词加粗。
- `可借鉴点`: ≤50 字；句式 `TikTok可考虑在[具体场景]中[具体动作],以[预期效果]`。不适合时写 `不建议直接照搬，原因:<≤30 字>`。

Content priority:
- Include evidenced数字化指标、机制名称、视觉/交互组件名。
- Include目标用户画像 only when it changes a design decision.
- Preserve English names such as `Daily Bonus Ladder`.

Avoid:
- Adding `证据状态`, `变化判断`, `来源与更新时间`, `产品设计亮点`, or `视觉设计亮点` as user-facing columns.
- Macro industry conclusions from a single case.
- Bilingual prose unless requested.
- Highlighting personal/private data in screenshots.
- Business model, financials, funding history, founder story, company history, technical architecture, backend implementation, SWOT/PEST.
- Subjective phrases such as `我觉得`, `很惊艳`, `用户体验好`, `很多`, `大量`, `这很棒`.

Before returning, self-check:
- The table can be scanned in one screen.
- Every `亮点分析` item has a concrete number or mechanism name.
- Every `可借鉴点` names a TikTok landing scene.
- Every `一句话介绍` is ≤15 Chinese characters.
- Screenshots are independently readable.
