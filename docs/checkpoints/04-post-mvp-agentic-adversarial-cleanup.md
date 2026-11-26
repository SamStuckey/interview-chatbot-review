# Post-MVP review 1: open items

> **Settled historical context.** All 42 questions were reviewed with Sam.
> This document preserves the original questions and suggestions and is no
> longer authoritative. The agreed MVP action items are in
> [Post-MVP Cleanup](../post-mvp-cleanup.md). Deferred work and presentation
> topics are in [Future Considerations](../future-considerations.md).
> The original open statuses below are preserved as historical context.

Every open question left after the MVP build and the refactor (2026-11-18),
normalized into one list. We go through it one item at a time, and each item
ends in exactly one place:

- **Future:** documented in `future-considerations.md`;
- **Cleanup:** documented in `post-mvp-cleanup.md`, as work to do before
  submission;
- **Resolved:** marked resolved here, with the reason.

Each item records its sources:
- **R#:** the combined code review;
- **D#:** the discussion list in `mvp-plan.md`;
- **P#:** "Punted from the MVP" in `future-considerations.md` (as committed in
  `9e43cf9`), which Sam had already sorted as future;
- **FC:** other sections of that file;
- **WT#:** the walkthrough findings in `second-agent/interview-review.md`, by
  topic;
- **BL#:** the build log's known limitations.

The suggestions are Claude's; Sam decides.

**Not on this list (already settled):**
- the refactor's fixes (R1, R3–5, R7–10, R12–14, R16);
- D1–4, D11 and D16 (D-094, D-095, D-096);
- requirement IDs in comments, which are kept.

## 1. Safety check latency
*From: new item; D32; WT24*
- **Problem:** every turn waits up to about 1 s for a cheap model to pick policy documents before the main call.
- **Example:** "hi" waits the same second as "Is this granola safe for a peanut allergy?"
- **Importance:** High. It's on every reply's first-word time, and it's a headline feature.
- **Suggestion:** keep it as is (measured, fails open), and feature it in the presentation.
- **Decision:** open

## 2. Demo reachable from the network
*From: R2*
- **Problem:** ports 8000 and 16686 bind every interface.
- **Example:** on shared Wi-Fi, anyone opening your-ip:8000 can pick a user and chat as them.
- **Importance:** Medium. It's only the demo, but it hands out tokens for any user.
- **Suggestion:** cleanup. `127.0.0.1:` on two lines in `compose.yaml`.
- **Decision:** open

## 3. The eval can't fail
*From: R6*
- **Problem:** it doesn't check the turn completed, counts failed reads, and always exits 0.
- **Example:** a turn that errors before any tool call passes a "no policy needed" case.
- **Importance:** Medium. The eval is a brief deliverable, so green must mean something.
- **Suggestion:** cleanup. Require completion, count only successful reads, exit non-zero on failure.
- **Decision:** open

## 4. TDD out of step with the build
*From: D5–10, D13–15, D17*
- **Problem:** accepted deviations were never written into the TDD.
- **Example:** TOOL-4 says the request backstop is the limit + 2, but the code uses + 4; AGT-6/7 never mention `ToolGuard`. Also CNT-1, CTX-1, ING-1, §8.2, CMP-1, CMP-3 and §16.
- **Importance:** High. Reviewers read the TDD against the code.
- **Suggestion:** cleanup. One documentation pass.
- **Decision:** open

## 5. No history lookup by date or position
*From: D25; WT16*
- **Problem:** `search_my_history` only finds keyword matches.
- **Example:** "What did we talk about last Tuesday?" finds nothing.
- **Importance:** Low to medium. Summaries and notes cover the gist.
- **Suggestion:** future. A new tool is new scope after the MVP.
- **Decision:** open

## 6. Small code nits
*From: R15, R17, R21*
- **Problem:** an untyped services lookup, a shared limit-reached dict, an `assert` in the runner, an unusual `super()` call in `TemplateSummarizer`.
- **Example:** `request.app.state.services` is untyped in four routers.
- **Importance:** Low.
- **Suggestion:** resolved, won't do. Sam's line review will catch any that matter.
- **Decision:** open

## 7. Demo sign-out race
*From: R11*
- **Problem:** old stream callbacks survive sign-out.
- **Example:** switch from Tyler to Nora mid-reply, and Tyler's words appear in Nora's chat.
- **Importance:** Low. The demo page only, and display only.
- **Suggestion:** resolved, won't do.
- **Decision:** open

## 8. Cost estimate rate
*From: R18*
- **Problem:** summarizer tokens are priced at the chat model's rate.
- **Example:** a compacting turn shows a higher `capper.estimated_cost_usd` than it really cost.
- **Importance:** Low. It's labelled an estimate.
- **Suggestion:** resolved, won't do.
- **Decision:** open

## 9. Conversation sessions
*From: P9*
- **Problem:** there's no grouping of a stretch of chatting.
- **Example:** no per-session greeting or per-session metrics.
- **Importance:** Low. Nothing needs it.
- **Suggestion:** resolved, won't do.
- **Decision:** open

## 10. SQLite and the shared database
*From: D19; FC caveats 1, 4, 5; WT3*
- **Problem:** SQLite allows one writer, and Capper shares the app's database. The async data layer was a greenfield choice.
- **Example:** two Capper instances saving turns at once contend for the file lock.
- **Importance:** Medium in production; none for the demo.
- **Suggestion:** future. Present moving early to the client's managed database.
- **Decision:** open

## 11. Deployment and CI
*From: P4, P10*
- **Problem:** there's no deployment design or CI.
- **Example:** a change is checked only when someone runs the `dev` container.
- **Importance:** Medium in production.
- **Suggestion:** future. Present the ECR → Fargate sketch, fitting into the client's VPC, and CI running the four checks.
- **Decision:** open

## 12. Observability
*From: P1; D12, D33; BL1; WT29*
- **Problem:** there are traces but no dashboards, and the OpenAI SDK's retries are invisible.
- **Example:** a slow turn caused by an SDK retry shows only as one long model span.
- **Importance:** Medium.
- **Suggestion:** future. Rehearse debugging a turn from its trace for the presentation.
- **Decision:** open

## 13. Failover, rate limits and spend caps
*From: P2, P3; FC footnotes 4, 5*
- **Problem:** there's one provider, and no daily limits.
- **Example:** an OpenAI outage fails every turn; a script can run up spend.
- **Importance:** Medium to high in production.
- **Suggestion:** future.
- **Decision:** open

## 14. Resumable streams
*From: P7*
- **Problem:** a dropped connection can't rejoin a live reply.
- **Example:** a phone switches to cellular mid-reply, and the app shows the reply only after reloading.
- **Importance:** Low to medium.
- **Suggestion:** future.
- **Decision:** open

## 15. The Idempotency-Key contract
*From: D18; WT26*
- **Problem:** the API assumes the client sends one key per logical send and reuses it on retries.
- **Example:** a client that makes a new key per retry creates a duplicate turn.
- **Importance:** Medium. It's an integration contract.
- **Suggestion:** future. Make it explicit in the presentation.
- **Decision:** open

## 16. Model-call provenance
*From: D24; WT18, WT29, WT30*
- **Problem:** the trace doesn't say what each model call actually saw.
- **Example:** an eval fails, and you can't tell which summary or content version was in context.
- **Importance:** Medium for debugging.
- **Suggestion:** future. Per-call model, content version, summary and cutoff; opt-in capture of the exact request for seeded eval runs only.
- **Decision:** open

## 17. The Harness dependency
*From: FC "for review later" 1; R19, R20; D23; WT22–23*
- **Problem:** compaction relies on a fast-changing library: its output shape, a private test field (`_usage`), and a summary cutoff inferred by position rather than reported. Clearing also costs cache hits.
- **Example:** an upgrade changes the summary marker, and summaries silently stop saving (the specs would catch it).
- **Importance:** Medium.
- **Suggestion:** future. Present it as a deliberate trade: pinned and specced.
- **Decision:** open

## 18. No compaction head start
*From: P13; D22; WT22*
- **Problem:** the request that crosses the trigger waits for the summary.
- **Example:** one turn in a long chat pauses while summarizing.
- **Importance:** Low to medium.
- **Suggestion:** future. D-096 says what it takes, including sharing a prepared summary and its cutoff across instances.
- **Decision:** open

## 19. A context-limit rejection
*From: D31; WT20*
- **Problem:** a request over the model's limit fails the turn.
- **Example:** a huge pasted message on top of a tool-heavy turn.
- **Importance:** Low. The budget keeps history small.
- **Suggestion:** future. A reactive retry only; never estimate size before sending (D-092).
- **Decision:** open

## 20. No memory-pressure warning
*From: P6; FC caveat 3*
- **Problem:** facts can be summarized away without the model first saving them.
- **Example:** an allergy mentioned once early on survives only as a summary line.
- **Importance:** Low. The summary template, notes and search cover it.
- **Suggestion:** future.
- **Decision:** open

## 21. Conflicting guidance notes
*From: FC ideas 1, 2*
- **Problem:** notes accumulate, and the only rule is that newer wins.
- **Example:** "vegetarian" and later "eating fish now" both stay saved.
- **Importance:** Low to medium.
- **Suggestion:** future. Update in place, plus background consolidation.
- **Decision:** open

## 22. The budget and the 75% trigger
*From: FC hard problems 1; FC caveat 2*
- **Problem:** a trade-off to explain, not a defect.
- **Example:** summarizing at 75% costs extra calls but leaves headroom for tool-heavy turns.
- **Importance:** a presentation point.
- **Suggestion:** future (talking point).
- **Decision:** open

## 23. Literal search only
*From: D30; WT12*
- **Problem:** search misses synonyms.
- **Example:** "fizzy drinks" doesn't find "sparkling water".
- **Importance:** Medium for product quality.
- **Suggestion:** future. Semantic search behind the same tool, compared against literal first.
- **Decision:** open

## 24. Basic recommendations
*From: FC ideas 3, 4*
- **Problem:** only popularity by school or overall.
- **Example:** no "people who bought tortillas also bought salsa".
- **Importance:** Medium for product.
- **Suggestion:** future. Learning interests, and collaborative filtering.
- **Decision:** open

## 25. School popularity privacy
*From: D29; WT13*
- **Problem:** a small school's ranking can reveal one family's purchases.
- **Example:** a school with three users, whose top product is one family's weekly buy.
- **Importance:** Medium before production.
- **Suggestion:** future. A minimum group size, and the client's business sign-off.
- **Decision:** open

## 26. Cards for unseen products
*From: D27; WT15*
- **Problem:** the model can show a card for a real product it never looked up this turn.
- **Example:** it guesses ID 12, which exists, and shows it unprompted.
- **Importance:** Low.
- **Suggestion:** future. A turn-local set of returned IDs.
- **Decision:** open

## 27. Avoid list in context
*From: D26; WT17*
- **Problem:** naming avoided products might make the model mention them.
- **Example:** with "avoid: peanut butter" in context, the model says "unlike peanut butter…"
- **Importance:** Low to medium.
- **Suggestion:** future, as an eval case.
- **Decision:** open

## 28. "Show me more" after clearing
*From: D28; P5; WT14*
- **Problem:** paging depends on a cursor in a tool result that may be cleared, and the app can't page lists itself.
- **Example:** after clearing, the model restarts the search from page 1.
- **Importance:** Low.
- **Suggestion:** future. Store the query and cursor as app state; REST paging for the app.
- **Decision:** open

## 29. Oversized tool output
*From: P12*
- **Problem:** oversized results are refused, not stored for reading in slices.
- **Example:** none today, since there are no unbounded tools.
- **Importance:** Low.
- **Suggestion:** future, only when such tools arrive.
- **Decision:** open

## 30. Message parts as a JSON array
*From: D21; WT8*
- **Problem:** querying across conversations by part type means scanning arrays.
- **Example:** counting how often a product's card was shown.
- **Importance:** Low.
- **Suggestion:** future. Develop an alternative.
- **Decision:** open

## 31. No confirmation flow
*From: P11*
- **Problem:** there's no approval step for tools that act.
- **Example:** a future "apply referral code" tool would act without asking.
- **Importance:** Low now; there are no action tools.
- **Suggestion:** future. The design is ready (D-073).
- **Decision:** open

## 32. Content publishing
*From: D20; P8; WT9; FC source-document discrepancies*
- **Problem:** hand-edited Markdown is published directly, with no staging, review, conflict detection or access control.
- **Example:** a malicious edit to an always-loaded document becomes model instructions on the next turn.
- **Importance:** Medium to high in production.
- **Suggestion:** future. Admin authoring, staged publishing checked by evals, approval rights, uploads treated as data.
- **Decision:** open

## 33. Conflicting and missing source documents
*From: FC source-document discrepancies, knowledge gaps, documents not provided, data observations*
- **Problem:** the sources disagree, and some referenced documents don't exist.
- **Example:** the FAQ says the bonus needs a school link; the Rules say first scan or a link.
- **Importance:** Medium for correct answers.
- **Suggestion:** future. A question list for the client.
- **Decision:** open

## 34. Long documents and internal-only content
*From: FC footnotes 1, 2*
- **Problem:** there's no retrieval for large documents, and internal documents must never reach the model.
- **Example:** a 40-page terms of service can't be loaded whole.
- **Importance:** Low for the MVP.
- **Suggestion:** future. RAG, and keep the manifest allowlist.
- **Decision:** open

## 35. English only
*From: FC "for review later" 2*
- **Problem:** no other languages.
- **Example:** a Spanish-speaking parent gets English answers and content.
- **Importance:** Low to medium.
- **Suggestion:** future.
- **Decision:** open

## 36. No user time zone
*From: FC footnote 3*
- **Problem:** time-aware answers use a configured default.
- **Example:** "ends today" is off by hours for a West Coast user.
- **Importance:** Low.
- **Suggestion:** future. A profile field, or the app sends it.
- **Decision:** open

## 37. No purge or redaction
*From: FC privacy system*
- **Problem:** only saved notes can be removed.
- **Example:** "Forget what I told you about my brother" can't be honored.
- **Importance:** High in production (erasure requests).
- **Suggestion:** future. The privacy-system design: suppress, hide, delete.
- **Decision:** open

## 38. OWASP 2026
*From: FC "for review later" 3*
- **Problem:** the security audit used the 2025 Top 10.
- **Example:** a new 2026 category is unchecked.
- **Importance:** Low to medium.
- **Suggestion:** future. Check it before the presentation.
- **Decision:** open

## 39. Ignored user groups
*From: FC edge cases*
- **Problem:** COPPA, non-US users and other user types are out of scope.
- **Example:** a child chatting on a parent's account.
- **Importance:** Medium in production.
- **Suggestion:** future.
- **Decision:** open

## 40. Choices that look like gaps
*From: FC product decisions*
- **Problem:** deliberate decisions a reviewer may question.
- **Example:** Stop saves the partial reply instead of discarding it.
- **Importance:** a presentation point.
- **Suggestion:** future. Talking points: stop, two models, notes aren't safety, generic capabilities.
- **Decision:** open

## 41. Thin evals
*From: FC "for review later" 4; FC hard problems 1*
- **Problem:** there's one tool-call eval.
- **Example:** nothing checks that a fact survives compaction.
- **Importance:** Medium.
- **Suggestion:** future. Start with fact retention across compaction, the only match beyond page 1, and avoid-list placement (item 27).
- **Decision:** open

## 42. The demo sign-in
*From: FC caveat 6; BL2*
- **Problem:** the demo routes let anyone act as anyone, and the token is lost on reload.
- **Example:** refreshing the page returns to the user list.
- **Importance:** a presentation caveat.
- **Suggestion:** future. Remove the routes for production.
- **Decision:** open
