# Mobile integration

How the Carton Caps app would use Capper. The endpoints, events and errors
are defined in the [API contract](api-contract.md); this page covers the
app's side, i.e. what to call when, how to render the stream, and what to handle.
The demo page ([app.js](../src/capper/demo/static/app.js)) is a working
reference client for everything below.

## What the app owns, and what Capper owns

| The app | Capper |
|---|---|
| Logging in and refreshing tokens (the existing auth API) | Verifying the token on each request |
| Rendering: bubbles, cards, timestamps, the processing state | Deciding what to say, and which cards to show |
| A new `Idempotency-Key` per message | Duplicate-send rules and replay |
| Showing the user's local time | Interpreting dates in the user's time zone |
| The chat screen's state | The conversation itself: history, summaries, saved guidance |

Capper keeps no session. App restarts and token refreshes need nothing from
Capper. Each user has one continuous conversation; separate chat sessions are
a possible addition, discussed in
[Known limitations](known-limitations.md#6-memory-is-explicit-limited-and-potentially-lossy).

## Tokens

- Send the access token the app already has from the auth API on every `/v1`
  request.
- On a `401`, refresh the token with the auth API and retry the request.
- The main integration task with the auth team is agreeing the token's claims
  and sharing its public key with Capper; the requirements are under
  [Authentication](api-contract.md#authentication).

## Opening the chat

1. Call `GET /v1/conversation` and `GET /v1/conversation/messages` together.
2. Render the history oldest first (the API returns newest first). Load older
   pages with the returned cursor as the user scrolls up.
3. Show the date header from message timestamps, in the user's time zone.
4. Show the `greeting` bubbles every time the chat opens. They're never in the
   history, so they never duplicate.
5. If `turn_in_progress` is true, a reply is still being written (for
   example, the app was closed mid-reply). Show the processing state and
   reload the history after a moment.

## Sending a message

1. Create a random `Idempotency-Key` (a UUID) for the message.
2. Show the user's bubble and the processing dots, and turn the send button
   into a Stop button.
3. `POST /v1/conversation/messages` with the text and the key.
4. If the request fails before any response arrives (a network error, a
   timeout), retry it **with the same key**. Capper never starts a second
   reply for a key it has already seen
   ([send rules](api-contract.md#post-v1conversationmessages)).

The key is an integration contract: one key per message the user meant to
send, reused only for retries of that message. A client that makes a new key
for each retry can create duplicate turns (see
[Known limitations](known-limitations.md#14-duplicate-send-protection-depends-on-the-client)).

| Response | What to do |
|---|---|
| `200` | Read the stream (below). |
| `409 turn_in_progress` | Another reply is running, perhaps from another device. Wait, then reload the history. |
| `422` | Show the error's `message` and let the user edit and resend. |
| `401` | Refresh the token and retry with the same key. |

## Reading the stream

The body is NDJSON: split it on newlines and parse each line as JSON. The
[events](api-contract.md#events) section lists every field.

| Event | What to do |
|---|---|
| `turn.start` | Keep `turn_id` for Stop. |
| `text.delta` | Append to the current text. Re-render it, starting a new bubble at each blank line (paragraph break). |
| `card` | End the current text bubble and render a horizontal carousel under `heading`. Following text starts a new bubble. |
| `turn.end` | The reply is finished and saved. Show "Stopped" if `status` is `stopped`. Show feedback controls if `assistant_message_id` isn't null. |
| `error` | Show the event's `message`. Whatever streamed before it is saved. |

Then restore the send button.

### Bubbles

The mockups show several short bubbles per reply. Capper doesn't send bubble
boundaries; the app splits text at paragraph breaks (blank lines) and around
cards. Capper's persona writes short paragraphs to suit this.

### Cards

- **Product:** image, name and price.
- **Promotion:** image, title and description.
- Image URLs are paths on the Capper host: resolve them against Capper's base
  URL, and show a placeholder when there's none.

### Markdown

- Render only the subset Capper writes: paragraphs, bold, italic, lists and
  headings.
- Escape all HTML before rendering, and never render raw HTML from a reply.
- Show links as plain text with their URL.
- Don't render images from text. Images come only from card events.

## Stop, disconnects and retries

- **Stop:** the Stop button calls the turn's
  [stop endpoint](api-contract.md#post-v1conversationturnsturn_idstop) with
  the `turn_id` from `turn.start`. Keep reading the stream: it ends with
  `turn.end`, status `stopped`. What was said is kept, and the next message
  continues from it.
- **Leaving the screen or losing the connection** does not stop the reply. It
  finishes and is saved. On return, reload the history. There is no way to
  rejoin a live stream.
- **Don't** retry automatically after a `200` stream has started and failed:
  the reply may already have saved a note or shown cards. Let the user decide
  whether to ask again.

## Feedback

Show thumbs up and down on assistant messages, and send the rating to the
[feedback endpoint](api-contract.md#post-v1conversationmessagesmessage_idfeedback).
A new rating replaces the old one, so the controls can simply show the latest
choice. Note that this is a naive POC for collecting feedback that neither trains
the model, nor affects preferences. Reliance on this would require API work.

## Time zones

- Times from the API are UTC. Show them in the device's time zone.
- Capper reads dates in a message ("what did we talk about last Tuesday?") in
  the time zone on the user's account. The prototype can't set it, so in
  production either the app's account data supplies it or the app sends it
  with each request. That's a decision to make with the Carton Caps team.

## Integration checklist

- [ ] Token claims agreed with the auth team, and Capper has the public key.
- [ ] One `Idempotency-Key` per message, reused only on retries.
- [ ] Bubbles split at paragraph breaks and around cards.
- [ ] Markdown rendered with HTML escaped.
- [ ] Card image paths resolved against Capper's base URL.
- [ ] `409` and `turn_in_progress` handled by waiting and reloading.
- [ ] History reloaded after a lost connection.
- [ ] The user's time zone available on their account.
