"""Analyze the help desk tickets and write the findings to reports/findings.md."""
from pathlib import Path

import pandas as pd

t = pd.read_csv("data/tickets.csv", parse_dates=["created_at", "closed_at"])
closed = t[t.status == "Closed"].copy()
closed["sla_breached"] = closed["sla_breached"].astype(str).str.lower() == "true"

normal = closed[~closed.is_security_incident]
reported = closed[closed.is_security_incident & ~closed.hidden_security]
hidden = closed[closed.hidden_security]

lines = []


def say(text=""):
    print(text)
    lines.append(text)


def pct(x):
    return f"{x:.0%}"


def table(df):
    """Markdown table without extra libraries."""
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n" + "\n".join(out) + "\n"  # blank lines so GitHub renders it as a table


# 1. Overview
say("# Help Desk Findings")
say()
say("## 1. Overview")
say(f"- **{len(t):,} tickets** from {t.created_at.min():%b %d} to {t.created_at.max():%b %d, %Y} "
    f"({(t.status == 'Open').sum()} still open)")
say(f"- Median resolution time: **{closed.resolution_hours.median():.1f} hours**")
say(f"- SLA breached on **{pct(closed.sla_breached.mean())}** of closed tickets")
say(f"- Average satisfaction (CSAT): **{closed.csat.mean():.2f} / 5**")

# 2. When tickets arrive
by_day = t.created_at.dt.day_name().value_counts()
busiest_hour = t.created_at.dt.hour.value_counts().idxmax()
say()
say("## 2. When tickets arrive")
say(f"- Busiest day: **{by_day.index[0]}** ({by_day.iloc[0]} tickets, "
    f"{by_day.iloc[0] / by_day.loc[['Tuesday', 'Wednesday', 'Thursday', 'Friday']].mean():.1f}x an average Tue–Fri)")
say(f"- Busiest hour: **{busiest_hour}:00–{busiest_hour + 1}:00**")
say(f"- Weekends: only **{pct(by_day.loc[['Saturday', 'Sunday']].sum() / len(t))}** of tickets")

# 3. What people ask for
cats = (closed.groupby("submitted_category")
        .agg(tickets=("ticket_id", "count"),
             median_hours=("resolution_hours", "median"),
             sla_breach=("sla_breached", "mean"))
        .sort_values("tickets", ascending=False).head(8).reset_index())
cats["median_hours"] = cats.median_hours.round(1)
cats["sla_breach"] = cats.sla_breach.map(pct)
say()
say("## 3. Top ticket categories (as submitted)")
say(table(cats.rename(columns={"submitted_category": "Category", "tickets": "Tickets",
                               "median_hours": "Median hours", "sla_breach": "SLA breached"})))

# 4. SLA and satisfaction
say()
say("## 4. SLA performance and satisfaction")
for p in ["P1", "P2", "P3", "P4"]:
    group = closed[closed.true_priority == p]
    say(f"- **{p}** (target {group.sla_hours.iloc[0]}h): {pct(group.sla_breached.mean())} breached")
p1 = closed[closed.true_priority == "P1"]
p1_breaches = p1[p1.sla_breached]
say(f"- **{pct(p1_breaches.hidden_security.mean())} of P1 breaches were hidden security incidents.** "
    f"Without them, the P1 breach rate drops to {pct(p1[~p1.hidden_security].sla_breached.mean())}.")
say(f"- CSAT when SLA was met: **{closed[~closed.sla_breached].csat.mean():.2f}**, "
    f"when breached: **{closed[closed.sla_breached].csat.mean():.2f}**")

# 5. The headline: security incidents hiding in the queue
security_total = t.is_security_incident.sum()
hidden_total = t.hidden_security.sum()
say()
say("## 5. Security incidents hiding in the help desk queue")
say(f"- **{security_total} security incidents** ({pct(security_total / len(t))} of all tickets). "
    f"**{hidden_total} ({pct(hidden_total / security_total)}) were filed as ordinary IT problems.**")
compare = pd.DataFrame({
    "Group": ["Normal IT tickets", "Security incidents (reported)", "Security incidents (hidden)"],
    "Tickets": [len(normal), len(reported), len(hidden)],
    "Median hours": [round(g.resolution_hours.median(), 1) for g in (normal, reported, hidden)],
    "SLA breached": [pct(g.sla_breached.mean()) for g in (normal, reported, hidden)],
})
say(table(compare))
say(f"- Hidden incidents took **{hidden.resolution_hours.median() / reported.resolution_hours.median():.1f}x longer** "
    f"to resolve than reported ones, because they were worked at the low priority the user picked.")

disguises = (t[t.hidden_security].groupby(["submitted_category", "true_category"]).size()
             .sort_values(ascending=False).reset_index(name="Tickets"))
say()
say("**What the hidden incidents were disguised as:**")
say(table(disguises.rename(columns={"submitted_category": "Filed as", "true_category": "Actually was"})))

# 6. Where security incidents come from
dept = (t.groupby("department").is_security_incident.agg(["sum", "mean"])
        .sort_values("sum", ascending=False).reset_index())
top = dept.iloc[0]
say()
say("## 6. Departments")
say(f"- Most security incidents: **{top.department}** ({int(top['sum'])}, {pct(top['mean'])} of its tickets)")

Path("reports").mkdir(exist_ok=True)
Path("reports/findings.md").write_text("\n".join(lines) + "\n")
print("\nSaved reports/findings.md")