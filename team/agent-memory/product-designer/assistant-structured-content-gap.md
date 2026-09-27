---
name: assistant-structured-content-gap
description: The assistant chat stream only carries text_delta/tool_call(name)/error/done — any spec that wants interactive UI (buttons, votes) inside an assistant answer needs a new structured stream event first.
metadata:
  type: project
---

`invai-web/src/routes/_app/assistant.tsx` renders assistant messages as plain `text_delta` concatenation plus
a joined list of tool-call *names* (no ids, no structured payload) — see lines 80-90. There is currently no
way to attach an interactive, voteable object (a recommendation, a card, a button) to a specific point in an
assistant answer.

**Why:** found reviewing `specs/market-signals.md` (wave 18): the spec's user flow puts "Done/Not useful"
buttons under each of up to 3 recommendations inside the streamed answer, but nothing in the contract or the
stream carries a stable recommendation id for the web to bind a vote mutation to.

**How to apply:** any future spec (market signals wave 18, and anything like it) that wants clickable,
stateful elements inside an assistant answer must add a new stream/message event type (e.g. a
`recommendations` array with ids) to the architect's contract before the web card starts. Flag this in review
as blocking, not a nice-to-have — the web card literally cannot bind the click handler without it. See
[[market-signals-and-digest-wave-18-19]].
