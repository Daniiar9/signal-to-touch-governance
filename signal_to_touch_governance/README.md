# Signal-to-Touch Governance Engine

A dry-run decision layer between Exa, HubSpot, Gong, and lemlist.

This demo implements two accounts: RetailCo, the blocked-outbound case, and FMCGCo, the approved dry-run draft case.

## What Problem This Solves

Most GTM automation jumps from "we found a signal" to "send outbound." This project adds the missing governance layer before the email. It reconciles an external signal against CRM state and conversation context, then decides whether outbound is justified.

For RetailCo, the external signal is strong, but Gong context says the buyer has frozen vendor conversations until an SAP S/4HANA migration checkpoint. The correct action is `BLOCK_OUTBOUND` and a HubSpot owner task, not a lemlist enrollment.

For FMCGCo, the external signal is strong, HubSpot has no active deal conflict, and Gong context supports a concise operations-focused follow-up. The correct action is `PREPARE_LEMLIST_DRAFT` with `dry_run = true` and human approval required.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add keys to `.env` if you want live Exa and OpenAI calls:

```bash
EXA_API_KEY=...
OPENAI_API_KEY=...
```

The demo remains reproducible without keys by using fixture signal data and a deterministic context fallback.

## Run

```bash
python -m src.main --account RetailCo --dry-run
python -m src.main --all --dry-run
```

The report is written to:

```text
dist/index.html
```

`--all` generates a report with both demo accounts.

## What Is Real Vs Mocked

Real:

- Exa signal search when `EXA_API_KEY` is present.
- OpenAI context evaluation when `OPENAI_API_KEY` is present.
- Static HTML decision trace generation.

Mocked:

- HubSpot account, contact, and deal state.
- Gong call summary and transcript excerpt.
- HubSpot task payload.
- lemlist payload generation.

## Why Dry Run

The engine never sends outbound or writes to external systems. It produces a decision trace and schema-shaped payloads so a human can review the reasoning before anything executes.

## Where It Breaks

- Exa can surface noisy or duplicate signals.
- Real Gong transcripts can be messy, sarcastic, or incomplete.
- LLMs can misread objections without structured validation.
- Mock CRM data is cleaner than real HubSpot.
- Real deployment needs defensive parsing, owner rules, cooldown windows, rate-limit queues, retry logic, and CRM writeback protection.
- At scale, synchronous API calls would need async orchestration.
- The system needs outcome feedback from replies/calls to tune signal thresholds.

## What I Would Build Next With A Week

- Real HubSpot read/write adapter.
- Real Gong transcript adapter.
- Real lemlist dry-run/create-lead adapter.
- Pydantic validation for LLM structured outputs.
- Async orchestration and rate-limit queues.
- Owner routing rules.
- Cooldown windows.
- CRM writeback logs.
- Signal quality feedback loop based on replies and call outcomes.
