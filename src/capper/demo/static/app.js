// The Capper demo client: a thin page that uses the API the way the mobile app would.
// Markdown is rendered from escaped text only; no raw HTML from the model reaches the DOM.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { token: null, turnId: null, sending: false };

// ---------- Markdown: a small, safe subset ----------

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInline(escaped) {
  return escaped
    // Images are not rendered: show their alt text only.
    .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, "$1")
    // Links are shown as plain text with their URL.
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, "$1 ($2)")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
    .replace(/(^|[^_\w])_([^_\s][^_]*)_/g, "$1<em>$2</em>");
}

function renderMarkdown(text) {
  const lines = escapeHtml(text).split("\n");
  const html = [];
  let list = null;
  const closeList = () => {
    if (list) { html.push(`</${list}>`); list = null; }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    let match;
    if ((match = line.match(/^(#{1,6})\s+(.*)$/))) {
      closeList();
      const level = Math.min(match[1].length + 2, 4);
      html.push(`<h${level}>${renderInline(match[2])}</h${level}>`);
    } else if ((match = line.match(/^\s*[-*+]\s+(.*)$/))) {
      if (list !== "ul") { closeList(); html.push("<ul>"); list = "ul"; }
      html.push(`<li>${renderInline(match[1])}</li>`);
    } else if ((match = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      if (list !== "ol") { closeList(); html.push("<ol>"); list = "ol"; }
      html.push(`<li>${renderInline(match[1])}</li>`);
    } else if (line.trim() === "") {
      closeList();
    } else {
      closeList();
      html.push(`<p>${renderInline(line)}</p>`);
    }
  }
  closeList();
  return html.join("");
}

// ---------- Rendering ----------

function scrollDown() {
  const box = $("messages");
  box.scrollTop = box.scrollHeight;
}

function addBubble(role, markdown) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  if (role === "user") div.textContent = markdown;
  else div.innerHTML = renderMarkdown(markdown);
  $("messages").appendChild(div);
  scrollDown();
  return div;
}

function addNote(text, className = "status") {
  const div = document.createElement("div");
  div.className = className;
  div.textContent = text;
  $("messages").appendChild(div);
  scrollDown();
  return div;
}

function cardElement(event) {
  const wrap = document.createElement("div");
  wrap.className = "cards";
  const heading = document.createElement("h4");
  heading.textContent = event.heading;
  const carousel = document.createElement("div");
  carousel.className = "carousel";
  for (const item of event.items) {
    const card = document.createElement("div");
    card.className = "card";
    if (item.image_url) {
      const img = document.createElement("img");
      img.src = item.image_url;
      img.alt = item.name || item.title || "";
      img.loading = "lazy";
      card.appendChild(img);
    }
    const body = document.createElement("div");
    body.className = "body";
    const name = document.createElement("div");
    name.className = "name";
    name.textContent = event.card_type === "promotion" ? item.title : item.name;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = event.card_type === "promotion" ? item.description : `$${Number(item.price).toFixed(2)}`;
    body.append(name, meta);
    card.appendChild(body);
    carousel.appendChild(card);
  }
  wrap.append(heading, carousel);
  return wrap;
}

function addCard(event) {
  $("messages").appendChild(cardElement(event));
  scrollDown();
}

// A run of streamed text, shown as one bubble per paragraph (the app splits bubbles).
class TextSegment {
  constructor() { this.text = ""; this.bubbles = []; }
  append(delta) {
    this.text += delta;
    const paragraphs = this.text.split(/\n{2,}/).filter((p) => p.trim() !== "");
    paragraphs.forEach((paragraph, i) => {
      if (!this.bubbles[i]) this.bubbles[i] = addBubble("bot", "");
      this.bubbles[i].innerHTML = renderMarkdown(paragraph);
    });
    scrollDown();
  }
}

function renderParts(parts) {
  for (const part of parts) {
    if (part.type === "text") new TextSegment().append(part.text);
    else addCard(part);
  }
}

function addFeedback(messageId) {
  const row = document.createElement("div");
  row.className = "feedback";
  for (const [rating, label] of [["up", "👍"], ["down", "👎"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.setAttribute("aria-label", `Rate ${rating}`);
    button.onclick = async () => {
      const response = await api(`/v1/conversation/messages/${messageId}/feedback`, {
        method: "POST",
        body: JSON.stringify({ rating }),
      });
      if (response.ok) {
        row.querySelectorAll("button").forEach((b) => b.classList.remove("chosen"));
        button.classList.add("chosen");
      }
    };
    row.appendChild(button);
  }
  $("messages").appendChild(row);
}

// ---------- API ----------

function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  return fetch(path, { ...options, headers });
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    return body.error?.message || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

// ---------- Sign-in (demo only) ----------

async function loadUsers() {
  const response = await fetch("/demo/users");
  const users = await response.json();
  const list = $("users");
  list.innerHTML = "";
  for (const user of users) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.textContent = user.name;
    const school = document.createElement("small");
    school.textContent = user.school || "No school linked";
    button.appendChild(school);
    button.onclick = () => signIn(user.id);
    li.appendChild(button);
    list.appendChild(li);
  }
}

async function signIn(userId) {
  const response = await fetch("/demo/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) { alert(await errorMessage(response)); return; }
  state.token = (await response.json()).access_token;
  $("sign-in").hidden = true;
  $("chat").hidden = false;
  $("sign-out").hidden = false;
  await openChat();
}

function signOut() {
  state.token = null;
  $("messages").innerHTML = "";
  $("chat").hidden = true;
  $("sign-out").hidden = true;
  $("sign-in").hidden = false;
}

// ---------- Chat ----------

async function openChat() {
  const [conversation, history] = await Promise.all([
    api("/v1/conversation").then((r) => r.json()),
    api("/v1/conversation/messages?limit=50").then((r) => r.json()),
  ]);
  const messages = history.messages.slice().reverse();
  if (messages.length) {
    addNote(new Date(messages[0].created_at).toLocaleString(), "day");
  }
  for (const message of messages) {
    if (message.role === "user") {
      addBubble("user", message.parts.map((p) => p.text || "").join("\n"));
    } else {
      renderParts(message.parts);
      if (message.status === "stopped") addNote("Stopped");
      if (message.status === "error") addNote("This reply didn't finish.");
      addFeedback(message.id);
    }
  }
  // The greeting is shown when the chat opens and is never stored.
  for (const bubble of conversation.greeting) addBubble("bot", bubble);
  if (conversation.turn_in_progress) addNote("A reply is still being written. Reload in a moment.");
}

function setSending(sending) {
  state.sending = sending;
  // Switching users mid-reply would leave the old stream writing into the next user's chat.
  $("sign-out").disabled = sending;
  const button = $("send");
  button.classList.toggle("stop", sending);
  button.textContent = sending ? "■" : "➤";
  button.setAttribute("aria-label", sending ? "Stop" : "Send");
  button.type = sending ? "button" : "submit";
}

async function stop() {
  if (state.turnId) await api(`/v1/conversation/turns/${state.turnId}/stop`, { method: "POST" });
}

function handleEvent(event, view) {
  switch (event.type) {
    case "turn.start":
      state.turnId = event.turn_id;
      break;
    case "text.delta":
      view.typing?.remove();
      view.typing = null;
      if (!view.segment) view.segment = new TextSegment();
      view.segment.append(event.text);
      break;
    case "card":
      view.typing?.remove();
      view.typing = null;
      view.segment = null;
      addCard(event);
      break;
    case "turn.end":
      view.typing?.remove();
      if (event.status === "stopped") addNote("Stopped");
      if (event.assistant_message_id) addFeedback(event.assistant_message_id);
      break;
    case "error":
      view.typing?.remove();
      addNote(event.message);
      break;
  }
}

async function send(text) {
  addBubble("user", text);
  setSending(true);
  const view = { segment: null, typing: addNote("Capper is typing…", "status typing") };
  try {
    const response = await api("/v1/conversation/messages", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      view.typing.remove();
      addNote(await errorMessage(response));
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let newline;
      while ((newline = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, newline).trim();
        buffer = buffer.slice(newline + 1);
        if (line) handleEvent(JSON.parse(line), view);
      }
    }
  } catch (error) {
    view.typing?.remove();
    addNote("Connection lost. Reload to see the saved reply.");
  } finally {
    state.turnId = null;
    setSending(false);
  }
}

$("composer").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = $("input");
  const text = input.value.trim();
  if (!text || state.sending) return;
  input.value = "";
  send(text);
});
$("send").addEventListener("click", (event) => {
  if (state.sending) { event.preventDefault(); stop(); }
});
$("input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("composer").requestSubmit();
  }
});
$("sign-out").addEventListener("click", signOut);
loadUsers();
