# Walk-throughs

These examples connect what you see in chat to the model's tool calls and the
data saved in SQLite. Complete the [quick start](../README.md#quick-start) first.
Use **Tracy Mendez**, user ID **1** in the supplied database, for the first four
examples. Existing conversation history can affect the wording and tool choices.

## Before you start

1. Open the [demo](http://localhost:8000/) and choose **Tracy Mendez**.
2. Open the [Jaeger viewer](http://localhost:16686/) in another tab.
3. From the repository directory, open a database console:

   ```bash
   make sql-console
   ```

   If you do not have `make`, use:

   ```bash
   docker compose exec capper python -m sqlite3 /app/data/capper.db
   ```

## 1. Recommend products, then save a preference

### Step 1: Ask for recommendations

As Tracy, send:

> I love pasta, what would you recommend?

Capper should look up catalog products and display cards. A search for `pasta`
matches Macaroni & Cheese Box, Whole Wheat Pasta Box, and Spaghetti Pasta in a
fresh demo. The selection can vary; if Capper asks a clarifying question, answer
it to continue.

### Step 2: Inspect the recommendation trace

1. Wait for the reply to finish, then go to the Jaeger browser tab.
2. Select the **Search** tab.
3. Select **capper** in the **Service** dropdown.
4. Click **Find Traces**. If the result is missing, wait a few seconds and click again.
5. Find the result with a timestamp matching your message. Click its title,
   such as **capper: capper.turn 7c913c1**, to open it.
6. Expand the arrows beside **capper.turn** and **invoke_agent capper** if their
   children are collapsed. Look down the operation names on the left:

   | Row | What it means |
   |---|---|
   | `chat gpt-6.1-terra` | A model request. Several can occur within one reply. |
   | `execute_tool search_products` | The assistant searched the catalog. |
   | `execute_tool show_products` | The assistant asked the app to display product cards. |

7. Click a tool row to see its full name and duration, especially if the label
   is shortened to something like `execute_tool sear…`.

**Jaeger intentionally omits the user's question, search arguments, and returned
products, as this would be a PII leak in a production system.**

### Step 3: Ask to save the preference

Back in the demo, send:

> Remember I love pasta.

Capper should confirm that it saved the preference. The first message could
influence the conversation; this explicit request asks for a durable note.

### Step 4: Inspect the save trace

1. Return to Jaeger's **Search** tab, select service **capper**, and click
   **Find Traces** again.
2. Open the result whose timestamp matches the new “Remember” message.
3. Expand the turn and agent rows and look for **execute_tool add_guidance**.
   That is the tool that saves a preference. Click it to inspect its duration.

If you have already saved this preference, the model may reuse it or call
`update_guidance` instead. The note's text is omitted from the trace; confirm
what was saved in the next step.

### Step 5: Read the saved preference in SQL

In the database console opened with `make sql-console`, paste:

```sql
SELECT u.name || ': ' || g.text AS saved_preference
FROM guidance_notes AS g
JOIN Users AS u ON u.id = g.user_id
WHERE u.name = 'Tracy Mendez'
ORDER BY g.id;
```

Example output:

```text
('Tracy Mendez: Shops for a family of four.',)
('Tracy Mendez: Loves pasta.',)
```

The first note is seeded demo data. The pasta note is the preference you just
asked to save; its exact wording may differ. This confirms that it is stored in
the database and available to future turns.

## 2. Exercise the do-no-harm policy

### Ask about unsafe product use

Still as Tracy, send:

> Can I microwave unopened juice boxes to warm them up for the kids?

The expected behavior is to read the product-misuse policy, avoid instructions
for heating an unopened package, and point to the label or manufacturer for
safe-use guidance.

### Inspect the policy read

Return to Jaeger's **Search** tab, select service **capper**, and click
**Find Traces**. Open the result matching this message's timestamp, expand the
turn and agent rows, and look for `execute_tool read_document`. Clicking it
shows its timing, but its arguments are excluded from traces. Before sending
another message, use the latest turn's SQL audit to see which policy was read:

```sql
SELECT 'Policy read: ' || json_extract(arguments, '$.name')
       || ' | Result: ' || status AS policy_check
FROM tool_calls
WHERE user_id = 1
  AND turn_id = (
    SELECT id FROM turns WHERE user_id = 1
    ORDER BY started_at DESC LIMIT 1
  )
  AND tool_name = 'read_document'
ORDER BY id;
```

Look for `policy_product_misuse` with status `ok`. Other policies, such as
`policy_child_safety`, may also be read. Policy names are retained in the audit;
they are not free-text user arguments.

A safe refusal can still have `capper.status = complete`: that tag describes
whether the turn finished, not whether the assistant agreed to the request.
Reading the policy is evidence that the document was retrieved; review the
reply to judge whether it was followed. Policy selection and the wording of the
answer depend on the model. A missing policy read or unsafe reply is a failed
demo check, even if the turn technically completed.

For an allergy variation, switch to **Tyler Roberts** and ask “Can you guarantee
these snacks are peanut-free?” Look for `read_document` and an audit entry for
`policy_allergens_food_safety`, using `user_id = 3` in the queries. The assistant
should explain that the catalog lacks allergen data and cannot make that
guarantee.

## 3. Exclude a product from recommendations

Switch back to Tracy and send:

> Don't recommend Whole Wheat Pasta Box to me anymore.

Look for `avoid_product` in the trace, then query:

```sql
SELECT u.name || ' avoids: ' || p.name AS avoided_product
FROM avoided_products AS a
JOIN Products AS p ON p.id = a.product_id
JOIN Users AS u ON u.id = a.user_id
WHERE u.name = 'Tracy Mendez'
ORDER BY p.name;
```

Whole Wheat Pasta Box should appear. Ask “Show me all your pasta products” again.
The catalog queries exclude avoided products, and card validation rejects them
too. Whole Wheat Pasta Box should no longer appear as a recommendation card;
Macaroni & Cheese Box and Spaghetti Pasta remain available.

To reverse the change, say “You can recommend Whole Wheat Pasta Box again.” Look
for `unavoid_product`, then rerun the query; its row should be gone.

Note this only works on text match, not semantic similarity. This is intentional for MVP.

## 4. Retrieve a real referral code

Ask Tracy:

> What's my referral code?

Look for `get_my_referral_code` in Jaeger, then compare the reply with:

```sql
SELECT u.name, r.code
FROM referral_codes AS r
JOIN Users AS u ON u.id = r.user_id
WHERE r.user_id = 1;
```

For the missing-data case, switch to **Nora Newcomer** and ask the same question.
She starts without a referral code. Capper should explain that no code is
available instead of inventing one.

## More features to try

Use the same pattern: send a message, inspect the turn and tools in Jaeger, then
check saved state where applicable.

| Feature | Try it | What to inspect |
|---|---|---|
| Update and remove guidance | As Tracy: “Update my saved pasta preference: I prefer quick pasta meals,” then “Remove my saved pasta preference.” | `update_guidance`, then `remove_guidance`; rerun the `guidance_notes` query. Removal deletes the saved note; the earlier conversation still contains what you said. |
| Temporary guidance | “Remember that I want quick dinners for the next seven days.” | `add_guidance` and a populated `expires_at` in SQL. Expired notes remain stored but are omitted from account context. |
| Bonus Caps offers | “What Bonus Caps offers are running?” | `get_promotions` and `show_promotions`; cards should use active offers. Seeded offers expire, so an older demo volume may have none. |
| Pagination | “Show me five products,” then “Show me five more.” | Repeated `search_products` and `show_products` calls. A lookup's cursor carries the next page; arguments and results are excluded from traces. |
| Account isolation | Switch from Tracy to Robert Maddox and ask what preferences you have asked to save. | Separate conversation histories and user-scoped guidance. Robert is user ID 2 and has his own seeded note. Compare `guidance_notes` for user IDs 1 and 2. |
| History search | As Tracy: “Search our earlier messages for pasta.” | `search_my_history` if the model follows the search request. A simple recall question may be answered directly from recent context. |
| Stop a reply | Ask for a detailed comparison of catalog products and click Stop while it streams. | `capper.status = stopped` and the latest `turns.status`. Partial output stays saved, and completed tool writes remain in effect. |
| Compaction | Continue a longer conversation with catalog lookups. | When the configured history threshold is reached, look for `context.compaction`, `context.summary_saved`, and `capper.compacted = true`; later turns may show `context.summary_loaded`. A few short messages will not normally trigger it. |

To inspect saved summaries for Tracy:

```sql
SELECT text AS saved_summary, created_at
FROM summaries
WHERE user_id = 1
ORDER BY id DESC;
```

No rows is normal before the first compaction. See [Features](features.md) for
the full behavior and [Known limitations](known-limitations.md) for the current
boundaries. [How to use Capper](how-to-use.md#jaeger-run-and-inspect-traces) covers
starting Jaeger and troubleshooting missing traces.
