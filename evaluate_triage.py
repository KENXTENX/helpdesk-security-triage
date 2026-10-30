"""Compare keyword rules vs AI on the hand-labeled test set. Writes reports/triage_results.md."""
import csv
from pathlib import Path

import anthropic

from test_set import TEST_TICKETS
from triage import ai_triage, keyword_triage


def rate(part, whole):
    return f"{part}/{whole} ({part / whole:.0%})" if whole else "n/a"


def main():
    client = anthropic.Anthropic()
    rows = []
    for i, (category, text, is_security, truth) in enumerate(TEST_TICKETS, 1):
        kw = keyword_triage(text)
        try:
            ai = ai_triage(category, text, client)
        except Exception as error:
            print(f"  AI error on ticket {i}: {error}")
            continue
        rows.append({"id": i, "filed_as": category, "truth": truth, "is_security": is_security,
                     "keywords": kw["is_security_incident"], "ai": ai["is_security_incident"],
                     "ai_priority": ai["priority"], "ai_confidence": ai["confidence"],
                     "ai_reason": ai["reason"], "description": text})
        mark = "ok " if ai["is_security_incident"] == is_security else "MISS"
        print(f"[{i:2}/{len(TEST_TICKETS)}] {mark} truth={'SEC' if is_security else 'ok '} "
              f"kw={'SEC' if kw['is_security_incident'] else 'ok '} ai={'SEC' if ai['is_security_incident'] else 'ok '} "
              f"{ai['priority']}  {text[:60]}")

    Path("reports").mkdir(exist_ok=True)
    with open("reports/triage_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    sec = [r for r in rows if r["is_security"]]
    hidden = [r for r in sec if r["filed_as"] not in
              ("Lost / Stolen Device", "Phishing Report", "Malware Alert", "Suspicious Login")]
    benign = [r for r in rows if not r["is_security"]]
    caught_p1p2 = [r for r in sec if r["ai"] and r["ai_priority"] in ("P1", "P2")]

    lines = [f"Tested on {len(rows)} hand-labeled tickets: {len(hidden)} hidden security incidents, "
             f"{len(sec) - len(hidden)} reported ones, and {len(benign)} ordinary tickets written to sound alarming.",
             "",
             "| Metric | Keyword rules | AI triage |",
             "|---|---|---|",
             f"| Hidden incidents caught | {rate(sum(r['keywords'] for r in hidden), len(hidden))} "
             f"| {rate(sum(r['ai'] for r in hidden), len(hidden))} |",
             f"| All security incidents caught | {rate(sum(r['keywords'] for r in sec), len(sec))} "
             f"| {rate(sum(r['ai'] for r in sec), len(sec))} |",
             f"| False alarms on ordinary tickets | {rate(sum(r['keywords'] for r in benign), len(benign))} "
             f"| {rate(sum(r['ai'] for r in benign), len(benign))} |",
             "",
             f"AI gave caught incidents P1 or P2 priority in {rate(len(caught_p1p2), sum(r['ai'] for r in sec))} of cases."]
    table = "\n".join(lines)
    Path("reports/triage_results.md").write_text(table + "\n")
    print("\n" + table)

    mistakes = [r for r in rows if r["ai"] != r["is_security"]]
    if mistakes:
        print("\nAI mistakes worth reading:")
        for r in mistakes:
            kind = "MISSED" if r["is_security"] else "FALSE ALARM"
            print(f"  {kind}: {r['description'][:90]}")
            print(f"           AI said: {r['ai_reason']}")


if __name__ == "__main__":
    main()