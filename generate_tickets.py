"""Generate a realistic, labeled IT help desk ticket dataset.

Each ticket has what the user submitted AND what the analyst found, so we can
measure how many security incidents hide inside ordinary-looking tickets.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)
N_TICKETS = 2000
START = datetime(2026, 1, 5)
END = datetime(2026, 9, 30)

DEPARTMENTS = {"Sales": 22, "Operations": 20, "Field Services": 18, "Finance": 12,
               "HR": 8, "Marketing": 8, "IT": 6, "Executive": 6}
CHANNELS = {"Portal": 45, "Email": 30, "Phone": 15, "Chat": 10}
APPS = ["Outlook", "Teams", "Salesforce", "QuickBooks", "Adobe Acrobat", "Zoom", "SharePoint", "Chrome"]
DEVICES = ["laptop", "desktop", "monitor", "docking station", "headset", "keyboard"]

# Ordinary tickets: category -> (weight, priority weights P1..P4, description templates)
NORMAL = {
    "Password Reset": (18, [0, 5, 35, 60], [
        "I forgot my password and can't log into {app}.",
        "My password expired and it won't let me set a new one.",
        "Locked out after too many attempts, please reset my password.",
    ]),
    "Account Lockout": (8, [5, 30, 50, 15], [
        "My account is locked and I can't log in to my {device}.",
        "Getting 'account disabled' when I sign in to {app}.",
    ]),
    "Software Issue": (16, [2, 18, 50, 30], [
        "{app} keeps crashing when I open it.",
        "{app} is very slow since this morning.",
        "I get an error message every time I try to save in {app}.",
    ]),
    "Software Install": (9, [0, 5, 40, 55], [
        "Can you install {app} on my {device}?",
        "I need {app} for a new project, please install it.",
    ]),
    "Hardware": (11, [3, 17, 50, 30], [
        "My {device} won't turn on.",
        "The screen on my {device} is flickering.",
        "My {device} stopped working after an update.",
    ]),
    "Network / VPN": (10, [10, 35, 45, 10], [
        "VPN keeps disconnecting when I work from home.",
        "No internet on the 3rd floor since 9am.",
        "Wi-Fi is extremely slow in the conference room.",
    ]),
    "Email": (8, [2, 18, 50, 30], [
        "I'm not receiving emails from external senders.",
        "My mailbox is full and I can't send messages.",
        "Shared mailbox disappeared from my Outlook.",
    ]),
    "Printer": (6, [0, 5, 45, 50], [
        "The printer on my floor says offline.",
        "Print jobs are stuck in the queue.",
    ]),
    "Access Request": (8, [0, 10, 50, 40], [
        "I need access to the {app} shared folder for my team.",
        "New hire starting Monday needs {app} access.",
    ]),
}

# Security incidents the user REPORTED as security
REPORTED_SECURITY = {
    "Phishing Report": (40, [15, 50, 30, 5], [
        "Got an email saying my {app} password expires today with a link. Looks fake.",
        "Received an invoice from a vendor we don't use, asking me to open an attachment.",
        "Email claiming to be from our CEO asking me to buy gift cards urgently.",
    ]),
    "Malware Alert": (25, [40, 45, 15, 0], [
        "Antivirus popped up saying it quarantined a file on my {device}.",
        "My {device} shows a ransom message and my files have strange extensions.",
    ]),
    "Lost / Stolen Device": (20, [45, 45, 10, 0], [
        "I left my company {device} on the train this morning.",
        "My work phone was stolen last night.",
    ]),
    "Suspicious Login": (15, [35, 50, 15, 0], [
        "I got an alert that someone signed into my account from another country.",
        "Microsoft says there was an unusual sign-in to my account.",
    ]),
}

# Security incidents HIDDEN inside ordinary tickets: (submitted as, true category, description)
HIDDEN_SECURITY = [
    ("Password Reset", "MFA Fatigue Attack",
     "I keep getting approve sign-in requests on my phone that I didn't start. Can you reset my password?"),
    ("Password Reset", "Account Compromise",
     "I got a password reset email I never requested, and now my password doesn't work."),
    ("Email", "Account Compromise",
     "People are replying to emails I never sent, and my Sent folder has messages I didn't write."),
    ("Email", "Account Compromise",
     "There's a rule in my Outlook forwarding all my mail to an outside address. I didn't create it."),
    ("Software Issue", "Malware",
     "A program I installed from a download site opens pop-ups and my browser homepage changed."),
    ("Hardware", "Unauthorized Remote Access",
     "My mouse moves on its own and windows open by themselves on my {device}."),
    ("Account Lockout", "Credential Attack",
     "My account keeps locking every few minutes even though I'm not trying to log in."),
    ("Software Issue", "Credential Phishing",
     "I clicked a link in an email to fix my {app} login and entered my password, but nothing happened."),
    ("Access Request", "Social Engineering",
     "Someone called saying they're from IT and asked for my login code to finish an upgrade. Is that normal?"),
]

SLA_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}
MEDIAN_HOURS = {"P1": 1.5, "P2": 3.5, "P3": 10, "P4": 28}


def pick(weights_dict):
    return random.choices(list(weights_dict), weights=list(weights_dict.values()))[0]


def random_time():
    while True:
        day = START + timedelta(days=random.randint(0, (END - START).days))
        # Monday is busiest, weekends are quiet
        if random.random() < [1.0, 0.85, 0.8, 0.8, 0.7, 0.12, 0.08][day.weekday()]:
            hour = int(min(max(random.gauss(11, 2.6), 6), 20))
            return day + timedelta(hours=hour, minutes=random.randint(0, 59))


def fill(text):
    return text.format(app=random.choice(APPS), device=random.choice(DEVICES))


def make_ticket(i):
    roll = random.random()
    if roll < 0.06:  # hidden security incident
        submitted, true_cat, text = random.choice(HIDDEN_SECURITY)
        priority = random.choices(["P1", "P2", "P3", "P4"], [0, 10, 55, 35])[0]  # user thinks it's routine
        true_priority = random.choices(["P1", "P2"], [60, 40])[0]
        is_security, hidden = True, True
    elif roll < 0.15:  # reported security incident
        name = random.choices(list(REPORTED_SECURITY), [v[0] for v in REPORTED_SECURITY.values()])[0]
        _, pw, texts = REPORTED_SECURITY[name]
        submitted = true_cat = name
        text = random.choice(texts)
        priority = true_priority = random.choices(["P1", "P2", "P3", "P4"], pw)[0]
        is_security, hidden = True, False
    else:  # ordinary ticket
        name = random.choices(list(NORMAL), [v[0] for v in NORMAL.values()])[0]
        _, pw, texts = NORMAL[name]
        submitted = true_cat = name
        text = random.choice(texts)
        priority = true_priority = random.choices(["P1", "P2", "P3", "P4"], pw)[0]
        is_security, hidden = False, False

    created = random_time()
    # Hidden incidents get worked at the low priority the user chose, so they take longer
    median = MEDIAN_HOURS[priority] * (1.6 if hidden else 1.0)
    hours = max(0.2, random.lognormvariate(0, 0.8) * median)
    closed = created + timedelta(hours=hours)
    open_ticket = closed > END + timedelta(days=1) or (created > END - timedelta(days=3) and random.random() < 0.4)

    breached = hours > SLA_HOURS[true_priority]
    csat = None if open_ticket else max(1, min(5, round(random.gauss(4.3 - (1.3 if breached else 0), 0.7))))
    tier = "Security" if is_security and not hidden else random.choices(["L1", "L2"], [75, 25])[0]

    return {
        "ticket_id": f"INC{100000 + i}",
        "created_at": created,
        "closed_at": None if open_ticket else closed,
        "status": "Open" if open_ticket else "Closed",
        "channel": pick(CHANNELS),
        "department": pick(DEPARTMENTS),
        "submitted_category": submitted,
        "submitted_priority": priority,
        "description": fill(text),
        "true_category": true_cat,
        "true_priority": true_priority,
        "is_security_incident": is_security,
        "hidden_security": hidden,
        "assigned_tier": tier,
        "resolution_hours": None if open_ticket else round(hours, 2),
        "sla_hours": SLA_HOURS[true_priority],
        "sla_breached": None if open_ticket else breached,
        "csat": csat,
    }


if __name__ == "__main__":
    tickets = pd.DataFrame(make_ticket(i) for i in range(N_TICKETS))
    tickets = tickets.sort_values("created_at").reset_index(drop=True)
    Path("data").mkdir(exist_ok=True)
    tickets.to_csv("data/tickets.csv", index=False)

    print(f"Saved {len(tickets):,} tickets to data/tickets.csv")
    print(f"Date range: {tickets.created_at.min():%b %d} to {tickets.created_at.max():%b %d, %Y}")
    print(f"Security incidents: {tickets.is_security_incident.sum()} "
          f"({tickets.hidden_security.sum()} hidden inside ordinary-looking tickets)")
    print("\nTop submitted categories:")
    print(tickets.submitted_category.value_counts().head(8).to_string())
    print(tickets.submitted_category.value_counts().head(8).to_string())