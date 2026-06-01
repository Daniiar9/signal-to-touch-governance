import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from src.config import DATA_DIR, DIST_DIR, TEMPLATES_DIR, load_env
from src.evaluators.action_planner import plan_action
from src.evaluators.context_eval import evaluate_context
from src.evaluators.draft_generator import generate_draft_payload
from src.evaluators.signal_eval import find_signal


def main() -> None:
    load_env()
    args = _parse_args()

    hubspot_accounts = _load_accounts(DATA_DIR / "hubspot_mock.json")
    gong_accounts = _load_accounts(DATA_DIR / "gong_mock.json")

    selected_accounts = _select_accounts(hubspot_accounts, args.account, args.all)
    reports = [
        _run_account(account, gong_accounts[account["account_name"]], args.dry_run)
        for account in selected_accounts
    ]

    DIST_DIR.mkdir(exist_ok=True)
    output_path = DIST_DIR / "index.html"
    output_path.write_text(_render_report(reports), encoding="utf-8")

    print(f"Wrote {output_path}")
    for report in reports:
        print(f"{report['account']['account_name']}: {report['action']['decision']}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Signal-to-Touch Governance Engine")
    account_group = parser.add_mutually_exclusive_group(required=True)
    account_group.add_argument("--account", help="Account name to evaluate, for example RetailCo")
    account_group.add_argument("--all", action="store_true", help="Evaluate all configured accounts")
    parser.add_argument("--dry-run", action="store_true", help="Never execute outbound actions")
    return parser.parse_args()


def _load_accounts(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {account["account_name"]: account for account in payload["accounts"]}


def _select_accounts(
    hubspot_accounts: dict[str, dict[str, Any]],
    account_name: str | None,
    all_accounts: bool,
) -> list[dict[str, Any]]:
    if all_accounts:
        return list(hubspot_accounts.values())
    if account_name not in hubspot_accounts:
        available = ", ".join(sorted(hubspot_accounts))
        raise SystemExit(f"Unknown account '{account_name}'. Available accounts: {available}")
    return [hubspot_accounts[account_name]]


def _run_account(
    hubspot_account: dict[str, Any],
    gong_context: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    signal = find_signal(hubspot_account)
    context = evaluate_context(hubspot_account, gong_context, signal)
    action = plan_action(hubspot_account, gong_context, signal, context, dry_run)
    action["lemlist_payload"] = generate_draft_payload(hubspot_account, signal, action)

    return {
        "account": hubspot_account,
        "gong": gong_context,
        "signal": signal,
        "context": context,
        "action": action,
    }


def _render_report(reports: list[dict[str, Any]]) -> str:
    template_path = TEMPLATES_DIR / "report_template.html"
    template_source = template_path.read_text(encoding="utf-8")
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )
        env.filters["json_pretty"] = lambda value: json.dumps(value, indent=2)
        template = env.get_template("report_template.html")
        return template.render(reports=reports)
    except ImportError:
        return _render_without_jinja(reports, template_source)


def _render_without_jinja(reports: list[dict[str, Any]], _template_source: str) -> str:
    cards = []
    for report in reports:
        action = report["action"]
        account = report["account"]
        signal = report["signal"]
        context = report["context"]
        gong_call = report["gong"].get("recent_call", {})
        blocked = action["decision"] == "BLOCK_OUTBOUND"

        cards.append(
            f"""
            <section class="account-card {'blocked' if blocked else ''}">
              <div class="card-header">
                <div>
                  <p class="eyebrow">Account</p>
                  <h2>{escape(account['account_name'])}</h2>
                  <p>Public search company: <strong>{escape(account['public_search_company'])}</strong></p>
                </div>
                <div class="decision">{escape(action['decision'])}</div>
              </div>
              <div class="badges">
                <span>Dry run</span>
                <span>Human approval required</span>
                <span>{escape(signal['source'])}</span>
              </div>
              <div class="grid">
                <article>
                  <h3>Signal Found</h3>
                  <p><strong>{escape(signal['signal_title'])}</strong></p>
                  <p>{escape(signal['signal_summary'])}</p>
                  <p>Score: <strong>{signal['score']}/10</strong></p>
                  <p><a href="{escape(signal['signal_url'])}">{escape(signal['signal_url'])}</a></p>
                </article>
                <article>
                  <h3>HubSpot State</h3>
                  <pre>{escape(json.dumps(account, indent=2))}</pre>
                </article>
                <article>
                  <h3>Gong Context</h3>
                  <p>{escape(context['context_summary'])}</p>
                  <blockquote>{escape(gong_call.get('transcript_excerpt', ''))}</blockquote>
                </article>
                <article>
                  <h3>Decision Trace</h3>
                  <p>{escape(action['reasoning'])}</p>
                  <pre>{escape(json.dumps(action, indent=2))}</pre>
                </article>
              </div>
            </section>
            """
        )

    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Signal-to-Touch Governance Engine</title>
        <style>{_base_css()}</style>
      </head>
      <body>
        <main>
          <header class="page-header">
            <p class="eyebrow">Dry-run decision layer</p>
            <h1>Signal-to-Touch Governance Engine</h1>
            <p>I did not build another AI email writer. I built the layer before the email: the part that decides whether a signal deserves outbound at all.</p>
          </header>
          {''.join(cards)}
        </main>
      </body>
    </html>
    """


def _base_css() -> str:
    return """
    :root {
      color-scheme: light;
      --ink: #17201c;
      --muted: #66746e;
      --paper: #f7f8f5;
      --panel: #ffffff;
      --line: #d7ddd7;
      --block: #b42318;
      --block-soft: #fff1ed;
      --accent: #006b5f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    main { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 40px 0; }
    .page-header { margin-bottom: 28px; }
    .page-header h1 { margin: 0 0 10px; font-size: clamp(32px, 6vw, 56px); line-height: 1; }
    .page-header p { max-width: 780px; color: var(--muted); }
    .eyebrow { margin: 0 0 8px; color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: 0; text-transform: uppercase; }
    .account-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(23, 32, 28, 0.06);
    }
    .account-card.blocked { border-color: #f3b6ad; box-shadow: 0 0 0 4px var(--block-soft); }
    .card-header { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; margin-bottom: 18px; }
    h2 { margin: 0 0 4px; font-size: 30px; }
    h3 { margin: 0 0 10px; font-size: 16px; }
    .decision {
      min-width: 190px;
      text-align: center;
      border: 1px solid var(--block);
      color: var(--block);
      background: var(--block-soft);
      border-radius: 6px;
      padding: 10px 12px;
      font-weight: 800;
    }
    .badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
    .badges span {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: #fbfcfa;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    article { border: 1px solid var(--line); border-radius: 8px; padding: 16px; min-width: 0; }
    article p { margin: 0 0 10px; }
    a { color: var(--accent); overflow-wrap: anywhere; }
    pre {
      margin: 0;
      max-height: 360px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #f4f6f2;
      border-radius: 6px;
      padding: 12px;
      font-size: 12px;
    }
    blockquote {
      margin: 10px 0 0;
      border-left: 4px solid var(--block);
      padding-left: 12px;
      color: #46312e;
    }
    @media (max-width: 760px) {
      main { width: min(100% - 20px, 1180px); padding: 24px 0; }
      .card-header { display: block; }
      .decision { margin-top: 14px; width: 100%; }
      .grid { grid-template-columns: 1fr; }
    }
    """


if __name__ == "__main__":
    main()
