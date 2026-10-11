# UI/UX Specification

## Design goals
Professional, clean, data-focused dashboard suitable for a portfolio demo. Use clear hierarchy, restrained color, accessible contrast, responsive layout, and consistent feedback. Do not imitate a specific vendor product without a supplied reference.

## Shared shell
- Left sidebar on desktop; collapsible navigation on small screens.
- Header: application name, selected trial where applicable, current user menu, sign-out.
- Main content area with page title, short explanation, and primary action.
- Consistent cards, buttons, tables, badges, loading skeletons, alerts, and empty states.
- Use a neutral clinical/analytics visual style. Define actual color tokens in code and keep them centralized.

## Page 1: Login / Register
- Email and password fields; registration page if public registration is approved.
- Inline validation and generic authentication failure message.
- Never expose whether an email exists in a way that enables easy account enumeration.
- Loading state on submit; accessible labels; password visibility toggle if implemented.
- No demo credentials containing real personal data.

## Page 2: Trials overview
- List trials owned by the signed-in user.
- Columns/cards: trial code, trial name, status, start date, participant count, last updated.
- Actions: open dashboard, create trial.
- Empty state explains how to create a trial.
- Error state includes retry; pagination if needed for larger datasets.

## Page 3: Trial dashboard
- Trial selector or breadcrumb and trial metadata.
- KPI cards: total participants, completed, active, withdrawn, completion rate, withdrawal rate.
- Pie/donut chart for status distribution and bar chart for counts. Include accessible text summary and do not rely on color alone.
- Display the denominator and definition of each percentage in a tooltip/help text.
- If no data exists, show an empty state and upload CTA.
- If status counts do not reconcile, show a data-quality warning rather than misleading charts.
- AI insight CTA is disabled or explains setup is needed when Gemini is not configured.

## Page 4: Upload CSV
- Choose trial; select/drop CSV; show max size and accepted column names.
- Preview a limited number of rows, normalized statuses, and row/column counts.
- Validation summary: valid rows, invalid rows, duplicate IDs, missing required columns.
- Show actionable row errors without exposing server internals.
- Require explicit confirmation before importing.
- Show import progress and final result counts.
- Prevent duplicate submissions while an import is running.

## Page 5: AI insights
- Show the exact aggregate metrics supplied to the model.
- Button: “Generate AI insight”.
- Render the response as plain text/Markdown with safe rendering; never inject raw HTML.
- Label content “AI-generated — requires human review.”
- Show timestamp, model identifier if available, and failure/retry state.
- Never claim “trial is healthy” unless a defined, approved rule supports that exact statement; default AI prompt should avoid binary health judgments.
- Do not show invented follow-up recommendations or projected completion dates.

## Page 6: Reports
- Select trial and reporting snapshot/date if supported.
- Preview included metrics and AI narrative.
- “Export PDF” action with loading and error states.
- PDF must include trial code, generated timestamp, metric definitions, report caveat, and AI-generated label when applicable.

## Page 7: Audit log
- Accessible only to users with permission to view relevant events.
- Columns: timestamp, actor/user ID, action, entity type/ID, outcome.
- Filters by date/action/outcome if feasible.
- Do not show passwords, tokens, API keys, raw CSV rows, or unnecessary participant-level data.

## Page 8: About / Help
- Project purpose, CSV schema link, metric definitions, AI limitations, privacy warning, and local support/documentation link.

## Interaction and responsive rules
- Every asynchronous action has loading, success, and failure states.
- Use confirmation for import and any destructive action.
- Preserve filters and selected trial when navigating where practical.
- Keyboard navigable controls, visible focus, semantic headings, form labels, and sufficient contrast.
- On mobile, stack KPI cards, allow chart/table horizontal scrolling when necessary, and keep primary actions easy to find.
