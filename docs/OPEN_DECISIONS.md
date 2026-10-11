# Open Decisions Requiring User Approval

1. **Registration:** Public self-registration or admin-provisioned users? Recommended for portfolio demo: self-registration only if rate-limited and securely implemented; otherwise seed a local demo user without committing credentials.
2. **Trial code uniqueness:** Recommended unique per user: `(owner_user_id, trial_code)`.
3. **Duplicate participants on re-upload:** Recommended reject duplicates and require explicit correction; do not silently overwrite.
4. **Admin role:** Recommended defer admin functionality in first MVP; audit view scoped to current user's permitted events.
5. **AI retention:** Recommended do not persist raw prompts or provider responses unless needed; if saving insights, store the generated text, model, timestamp, metrics snapshot reference, and disclaimer under a documented retention policy.
6. **Follow-up alerts:** Not included by default. Add only if `next_visit_due_date` is populated and a precise deterministic rule is approved.
7. **Completion prediction:** Excluded from MVP. A forecast requires defined assumptions, schedule data, evaluation, and uncertainty reporting; the LLM must not guess a date.
8. **Deployment provider:** Select after local MVP works and current pricing/security capabilities are reviewed.
9. **Measurement table:** Excluded from MVP because the initial CSV and dashboard requirements do not define safe, useful measurement semantics. Add only with a defined use case and privacy review.
10. **Production clinical use:** Out of scope. Requires separate validation, governance, privacy/security review, and applicable regulatory assessment.
