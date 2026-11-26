# Point of view: priorities, trade-offs and evolution

Why Capper is built the way it is, what I traded away, and where I'd take it
next. [Features](features.md) lists what was built,
[Known limitations](known-limitations.md) lists the gaps in detail, and the
[decision log](decision-log.md) records every decision as it was made. This
page is the short version of the reasoning.

## What I prioritized

1. **Context engineering.** The brief asks for multi-turn conversations, user
   context, memory limits and dialogue coherence. Those all come down to one
   question, "what does the model see on each request, and why?" I put most of
   the effort there. What goes into a request, what's stored, what gets
   cleared or summarized, and how a long conversation stays coherent without
   growing without limit are the focus of this MVP.
2. **A production-shaped core with a small surface.** The token check,
   persistence, streaming, the provider integration and the content pipeline
   work the way a real service would. The production code has no test modes
   or fake paths; tests swap in scripted models through dependency injection.
   The one exception is the demo sign-in, which stands in for an auth service
   the brief says already exists.
3. **Simplicity.** Lean on the framework, keep tools narrow, and remove what
   doesn't earn its place. Several features were built, measured and then
   removed (see [What changed](#what-changed-along-the-way)).
4. **Honesty over cleverness.** Capper doesn't invent facts, doesn't silently
   drop context, and says what it can't do. The documentation does the same:
   [Known limitations](known-limitations.md) is as long as the feature list.

## Conversation design principles

- **Stay on purpose.** A scope charter says what Capper helps with (products,
  Bonus Caps, referrals, the app) and what it doesn't. Outside that, or when
  its documents and tools don't have the answer, it says so and points to
  Carton Caps support rather than guessing.
- **Ground every fact.** Program facts come from the knowledge documents;
  product, promotion, purchase and account facts come from tools. Products
  appear only as cards built from database records, so the model can't invent
  a product or a price.
- **Ask before recommending.** When something important is missing (what the
  family likes, what to avoid), ask first, as the mockup flow does. Then use
  what the user said, their purchases and their saved guidance.
- **Write for a phone.** Short paragraphs, which the app shows as separate
  bubbles; lists and headings for steps; a polite close.
- **Do no harm.** An always-loaded core sets the safety rules and tells the
  model when to read a detailed policy (allergies, dietary claims, children,
  misuse, crisis). The catalog has no ingredient data, so Capper never
  promises a product is safe. This was not part of the brief, just something
  I added because it seems important.
- **Remember only what the user asks to remember,** and say what was saved.
  Newer guidance wins over older guidance. Extensibility options are covered in
  known limitations, including confirmation or more semantic triggers, but
  for this MVP it is intentionally naive.
- **Treat user-supplied text as data.** Saved notes, summaries and search
  results reach the model labelled as information, never as instructions.

## The decisions that shaped Capper

What I chose, what I chose it over, and what it costs. A lot of this is redundant
with the features and known limitations documents, but duplicated here for
interview clarity.

1. **One continuous conversation per user.**
   - *Over:* separate conversations with IDs.
   - *Why:* the mockups show one ongoing chat, and with no conversation ID
     there's nothing in a URL to tamper with.
   - *Cost:* no "new chat"; topics mix. Compaction, saved guidance and
     history search carry the long-running context instead.
2. **Pydantic AI, with its Harness add-on for clearing and compaction.**
   - *Over:* a hand-written model loop, or LangChain.
   - *Why:* typed dependencies scope every tool to the verified user;
     streaming, cancellation and test models come built in; and it's lighter
     than LangChain.
   - *Cost:* the Harness changes quickly, so it's pinned exactly and the
     compaction specs guard the behavior Capper relies on. Its use would
     be a serious discussion before deployment with the client.
3. **Two records of the conversation.**
   - *Over:* one table in the framework's format.
   - *Why:* the transcript is what the user saw and never changes; the model
     history is what the model works from, and clearing and compaction change
     only what's sent from it. A framework upgrade can't break old
     transcripts.
   - *Cost:* Duplicate data, written in one transaction.
4. **Account context goes with each request, never into history.**
   - *Over:* writing it into the conversation once.
   - *Why:* readily available data shouldn't be copied into the conversation,
     where it goes stale and gets summarized. Each request gets the current
     name, school and saved guidance.
   - *Cost:* a few hundred tokens on every request, mostly covered by prompt
     caching.
5. **Clear, then summarize, at 75% of a token budget, and never truncate
   silently.**
   - *Over:* summarizing a fixed number of messages, or cutting history
     quietly when it's too long.
   - *Why:* silent truncation drops context nobody chose to drop. Old tool
     results are cleared first (the call stays visible, so the model can
     re-run it); if that isn't enough, older history is summarized with a
     fixed template whose headings are checked before the summary is used.
     The summary and its boundary are saved, so later turns reload exactly
     the same context. Summarizing at 75% rather than near the limit costs
     more summarization calls but leaves headroom for tool-heavy turns.
   - *Cost:* a summary can lose detail. History search, saved guidance and
     the summary's required headings reduce that risk; they don't remove it.
6. **Narrow tools for data; whole documents for knowledge.**
   - *Over:* putting the catalog or purchase history in the prompt, or
     retrieval over embeddings.
   - *Why:* structured data belongs behind typed, user-scoped queries with
     totals and paging, so "how many" questions are answered by the database.
     The knowledge documents are small enough to send whole, which is simpler
     and more reliable than retrieval.
   - *Cost:* retrieval becomes necessary once the documents grow; product
     search is literal text matching (semantic search is the first upgrade I'd
     make).
7. **Cards from database records; the model supplies only IDs.**
   - *Over:* letting the model write product details.
   - *Why:* names, prices and images can't be hallucinated, and unknown,
     avoided or expired items are refused.
   - *Cost:* the model could still pick a real ID it never looked up; checking
     that against the turn's lookups is a known next step.
8. **Content as published data, read once per turn.**
   - *Over:* documents baked into the code or a file bundle that needs a
     deploy.
   - *Why:* an FAQ change shouldn't need a deploy. Documents go through an
     allowlist manifest into a versioned table; each turn reads one snapshot,
     and every turn records the content version it used.
   - *Cost:* anything published as instructions is effectively prompt, so a
     real deployment needs review and approval before publishing.
9. **Explicit memory without a confirmation step.**
    - *Over:* inferring preferences in the background, or asking before every
      save.
    - *Why:* saving what the user clearly asked for, and saying so, is
      predictable and reviewable. The avoid list is enforced in the database
      queries, not left to the prompt.
    - *Cost:* preferences mentioned in passing aren't saved, and can fade when
      older history is summarized.
10. **Two models, and no provider-side state.**
    - *Over:* one model, or letting the provider hold the conversation.
    - *Why:* a cheaper model can do the summarizing. Capper owns the history,
      so requests opt out of provider storage, and provider details stay in
      one adapter, so adding another provider doesn't touch the rest of the
      code.
    - *Cost:* Capper owns all of the context management.
11. **Stop keeps what happened; a disconnect isn't a stop.**
    - *Over:* discarding a stopped reply.
    - *Why:* the next message continues naturally, using the framework's own
      handling of interrupted tool calls. A dropped connection on a phone
      shouldn't lose the answer, so generation finishes and is saved.
    - *Cost:* a stopped reply's partial text stays in context.
12. **SQLite and Docker for a self-contained demo.**
    - *Over:* a database server.
    - *Why:* one command runs everything, with nothing to install but Docker.
      The data layer is async from the start, so moving to a managed database
      is mostly configuration and migrations.
    - *Cost:* one instance only; history search uses SQLite's full-text
      search. Would need reworking for a production deployment.
13. **Specs for what's deterministic, evals for what isn't.**
    - *Over:* testing model output in the unit suite.
    - *Why:* the specs run with scripted models and no network. Two small
      real-model evals check policy selection and answer quality, and fail
      when they should.
    - *Cost:* the evals are a demonstration, not a calibrated benchmark.

## What changed along the way

Some of the most useful decisions were reversals:

- **A separate safety check was built, measured and removed.** A cheap
  model picked relevant policies in parallel with loading context. Tuning
  brought its median from 1.7 seconds to about 1 second, but every reply,
  including "hi", still waited for it. The main model was already reading
  the right policy on its own when the always-on core told it to, so the
  check was removed.
- **Background compaction was removed.** Summaries prepared ahead of time
  never matched the history they were made for and were thrown away (about
  ten discarded for every one used in a long test), and each one cost a model
  call. Inline compaction already worked, so the head start went.
- **The avoid list moved out of the prompt.** Listing avoided products in
  every request risked the model mentioning them. The database already
  excludes them, so the list is now shown only when the user asks, and
  products are added and removed by name.
- **Content moved from files to a database table,** so publishing doesn't
  need a deploy.
- **History search gained date ranges and user time zones,** so "what did we
  talk about last Tuesday?" works, using the user's own calendar. This seemed
  like a common sense improvement over pure text matching.

## How it would evolve

**Before a pilot:**
- Real ingestion of the client's canonical documents. For this prototype I
  turned the supplied PDFs into Markdown by hand and resolved their conflicts
  myself, with the Program Rules winning over the FAQ. A pilot needs ingestion
  that reads the client's own sources and flags contradictions, gaps and
  placeholder values for the content owner to settle, recording which source
  governs each disputed rule. Capper's answers are only as reliable as these
  documents.
- Semantic product search behind the same tool, compared against literal
  search first.
- Cards only for products the turn actually looked up.
- Evals for facts surviving compaction, and a larger set of multi-turn and
  adversarial cases, reviewed by people.
- Spending limits per user, and failover to a second model provider.

**Before production:**
- The client's identity service in place of the demo sign-in.
- A managed database, and turn ownership and Stop that work across instances.
- A content workflow with review, approval, evals and rollback.
- Retention, deletion and redaction that reach every stored copy (see
  [Privacy](privacy.md)).
- Dashboards and alerts on the traces that already exist.

**Later:**
- A confirmation step, once tools can do things with consequences, such as
  applying a referral.
- Richer memory: consolidating notes, and preferences the user can review and
  correct.
- Recommendations that learn from feedback and purchases.
- Languages other than English.

## How I worked

Decisions were made one at a time and recorded in the
[decision log](decision-log.md) with the options considered. Design reviews,
the build log and the cleanup passes are kept as [checkpoints](checkpoints/),
which are history. They show how the design got here and are not updated as
the code changes. The code is the source of truth. The
[conversation log](conversation-log.md) is the full working record, including
the AI-assisted process used to build Capper.
