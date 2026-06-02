# Signal-to-Touch Governance Engine

The layer before the email. It decides whether a signal deserves outbound at all.

A signal gets you one step closer to a prospect. It does not put you at the doorstep. A funding round, a new hire, an expansion. On their own, none of those is a reason to reach out. Most of the GTM stack treats a raw signal like a green light to send, which is how you get noise in the CRM, falling reply rates, and burned domains.

This is a small dry-run governance layer that sits between signal detection and outbound execution. It takes a signal, reconciles it against account and conversation context, and decides what should happen: block, monitor, create a task, route to the owner, or prepare a draft. Nothing auto-sends. A human approves first.

Read [NOTE.md](NOTE.md) for the full thinking: why I picked this problem, where I deliberately left a human in the loop, and where it breaks at scale.

## How it works

```
EXA          ->  HUBSPOT        ->  GONG            ->  DECISION       ->  LEMLIST
signal           account            conversation        the layer          execution
detection        context            context             (the brain)        (dry-run only)
```

- **Exa** finds the signal. What changed at the account.
- **HubSpot** gives CRM truth. Owner, active deal, stage, lifecycle.
- **Gong** gives conversation truth. What the buyer actually said on calls.
- **Decision layer** reconciles all three and chooses the safest next action.
- **lemlist** is execution, and only runs if the gates pass. Dry-run by default.

The human is the operator, not a rubber stamp. The agent does the reconciliation, then hands over a full decision trace. The human inspects why it decided what it did, what flipped the call, what got blocked, and overrides if the model misread the room.

## Run it

```bash
python -m src.main --all --dry-run
```

This evaluates two demo accounts and writes an HTML decision trace to `dist/index.html`.

Expected output:

```
RetailCo: BLOCK_OUTBOUND
FMCGCo:   PREPARE_LEMLIST_DRAFT
```

- **RetailCo** has a strong signal but an active deal and a Gong call where the buyer said they are freezing vendor conversations until a migration finishes. The system blocks outbound and routes a task to the owner that carries the signal, the deal, the buyer quote, and a recommendation on timing. A normal automation would have enrolled them in a sequence and burned the deal.
- **FMCGCo** has a real signal, no deal conflict, and a buyer open to follow-up. Signal and context line up, so it prepares a lemlist draft. Still dry-run, still needs human approval.

## What's real and what's mocked

- **Real:** Exa signal detection (with a fallback fixture so the demo is reproducible), and the LLM reasoning layer.
- **Mocked:** HubSpot, Gong, and lemlist, with schema-shaped payloads. The point of this build is the decision layer, not OAuth setup.

## Stack

Python. Exa for signals, OpenAI for the reasoning layer, Jinja2 for the report. See `signal_to_touch_governance/` for the source.

## Setup

```bash
cd signal_to_touch_governance
pip install -r requirements.txt
cp .env.example .env   # add your EXA_API_KEY and OPENAI_API_KEY
python -m src.main --all --dry-run
```
