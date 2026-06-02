# Signal-to-Touch Governance Engine

A short note on why I built this, where I left a human in the loop, and where it breaks.

## Why this problem

About twenty minutes before I started writing this, I got a LinkedIn message from a founder. It was good. He'd read my open-source post, pulled a real metric from another post of mine, tied both to a problem he guessed I actually have, and offered value before asking for anything. Same week, I got another one that used the exact same raw signals and made me want to throw my phone across the room.

Same signals. Opposite outcomes. The difference was everything that happened in between.

That gap is the thing that drives me mad in GTM. A signal gets you one step closer to the prospect. It does not put you at the doorstep. A funding round, a new hire, an expansion, a tool change. On their own they are not reasons to reach out, and most of the stack treats them like they are.

There are three separate things, and people collapse them into one:

1. The signal. What changed in the world. Exa, Clay, intent tools find this easily. Detection is a solved problem.
2. The problem. The compelling event behind the signal. You only get this from CRM state, call history, and conversation context. This is the hard part, and it is where most tools go blind.
3. The timing. Whether the signal and the problem line up right now, or whether reaching out today burns the relationship.

When you skip steps 2 and 3 and fire outbound off the raw signal, you do not get pipeline. You get noise in the CRM that nobody acts on, falling reply rates, and a burned domain. And when the output is not there, everyone blames the tools, but the tool is not the problem. The problem is reps using the signal in the wrong way. I checked whether this was just my pet peeve or a real market problem, and practitioners are loud about it: signal tools get stood up, signals fire on day one, then the data dies in dashboards nobody opens while reps work the same static list.

The single line that sums it up, and the one I built everything around: a funding round is not a reason to reach out. A new hire is not a reason to reach out. A product launch is not a reason to reach out. The reason to reach out is the problem and the context behind the signal.

That is the whole bet. And it is exactly where the human belongs in the loop, because qualifying or disqualifying the problem, and judging whether the model read the context right or is bullshitting you, is a judgment call, not an automation. Founders selling into this space describe the same gap from the other side: most outbound tools start blind, and that is the fastest way to burn through your market.

Nobody is naming it precisely though. They feel the problem. They describe it as an AI SDR quality problem or a spam problem. What they are actually describing is a missing layer: nothing reconciles the external signal against internal context before deciding to act.

So I did not build another AI email writer. I built the layer before the email. The part that decides whether a signal deserves outbound at all.

## Where I deliberately left a human in the loop

The weak version of human-in-the-loop is a rubber stamp at the end. The agent makes five hidden decisions, then asks you to click approve on the last one. That is not oversight, it is theater.

I built it the other way around. The agent does the boring reconciliation first. It pulls the signal, checks the account state, reads the conversation context, and produces a decision with the full trace of why. The human is not a button-clicker, the human is the operator. You inspect why the system decided what it decided, what context flipped the call, what actions got blocked, and you override if the machine misread the room. Timing and nuance are exactly where a human still beats the model, so that is where the human sits.

The system is dry-run by default. Nothing auto-sends. A signal becomes a draft, a task, a route-to-owner, a monitor-only flag, or a hard block. Never an automatic touch.

## What I built

A command-line engine that runs the full pipeline across target accounts: real signal detection via Exa, account context from HubSpot, conversation context from Gong, and a decision layer that decides what should happen, ending in a lemlist-ready draft only if the gates pass. HubSpot, Gong, and lemlist are mocked with schema-shaped payloads. I used live Exa because signal quality is the actual point, and mocked the rest because the task is the governance layer, not OAuth setup. It outputs an inspectable HTML decision trace.

Two accounts demonstrate the contrast:

- One has a strong signal but an active deal and a Gong call where the buyer said they are freezing vendor conversations until a migration finishes. The system blocks outbound and instead creates a task for the owner that carries the full picture: the signal, the open deal, the exact buyer quote, and a recommendation to hold and re-engage once the migration wraps. Not a bare task, a directed action. This is the case I care about most. A normal automation would have enrolled them in a sequence.
- The other has a real operational signal, no deal conflict, and a buyer open to follow-up. The system prepares a dry-run draft, still requiring human approval.

Everyone else's demo shows AI writing an email. Mine shows AI refusing to.

## Where it breaks

This is rough and the failure modes are real:

- Exa signals are noisy and can surface generic or stale events.
- Gong transcripts are messy, and an LLM can misread tone, sarcasm, or a soft objection.
- HubSpot data goes stale, and real CRMs have duplicate and missing records that clean mock JSON does not.
- The scoring is heuristic, not learned.

The reason none of those sink it is the design itself. Because the system is dry-run by default and produces an audit trace instead of executing, a wrong read becomes a blocked task in someone's queue, not a spam email to a frozen enterprise deal. The cost of a mistake is contained.

## What I'd build with a week

- Real HubSpot, Gong, and lemlist adapters instead of mocks.
- Async orchestration so it does not stall when evaluating many accounts at once.
- Structured, validated LLM outputs with negative examples to cut transcript misreads.
- Owner rules and cooldown windows so the same account does not get re-triggered on every new signal.
- An override-feedback loop, so that as humans correct decisions and outcomes come in, the scoring thresholds tighten over time.

The goal is not more automation. It is safer automation. The system should know when not to send.
