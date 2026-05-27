# Feishu Digest Prompt

Create a concise Chinese Feishu message from the weekly analysis. The message is only a pointer/status note; do not duplicate research findings outside the Feishu Doc table.

Use this shape:

```markdown
全球 UG 竞品巡检｜<RUN_ID>

本周状态：<已归档/部分失败/需刷新证据>

需处理：
- <登录态失效/路径失效/模拟器问题/无>

完整记录已归档到飞书 Doc：<link-or-placeholder>
```

Keep it short. Do not add case summaries, market analysis, screenshots, or extra bullets in the message. All research content must live in the fixed 5-column Feishu Doc table defined in `references/output-template.md`.
