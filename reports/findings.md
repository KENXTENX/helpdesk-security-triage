# Help Desk Findings

## 1. Overview
- **2,000 tickets** from Jan 05 to Sep 30, 2026 (19 still open)
- Median resolution time: **11.8 hours**
- SLA breached on **18%** of closed tickets
- Average satisfaction (CSAT): **4.04 / 5**

## 2. When tickets arrive
- Busiest day: **Monday** (448 tickets, 1.2x an average Tue–Fri)
- Busiest hour: **11:00–12:00**
- Weekends: only **5%** of tickets

## 3. Top ticket categories (as submitted)

| Category | Tickets | Median hours | SLA breached |
|---|---|---|---|
| Password Reset | 359 | 19.9 | 24% |
| Software Issue | 320 | 10.8 | 18% |
| Hardware | 202 | 9.8 | 19% |
| Software Install | 187 | 18.1 | 13% |
| Access Request | 160 | 13.9 | 16% |
| Account Lockout | 159 | 7.8 | 20% |
| Network / VPN | 159 | 6.3 | 13% |
| Email | 157 | 13.0 | 28% |


## 4. SLA performance and satisfaction
- **P1** (target 4h): 45% breached
- **P2** (target 8h): 24% breached
- **P3** (target 24h): 14% breached
- **P4** (target 72h): 12% breached
- **87% of P1 breaches were hidden security incidents.** Without them, the P1 breach rate drops to 10%.
- CSAT when SLA was met: **4.26**, when breached: **3.04**

## 5. Security incidents hiding in the help desk queue
- **306 security incidents** (15% of all tickets). **124 (41%) were filed as ordinary IT problems.**

| Group | Tickets | Median hours | SLA breached |
|---|---|---|---|
| Normal IT tickets | 1677 | 12.8 | 14% |
| Security incidents (reported) | 181 | 3.6 | 10% |
| Security incidents (hidden) | 123 | 21.6 | 88% |

- Hidden incidents took **6.0x longer** to resolve than reported ones, because they were worked at the low priority the user picked.

**What the hidden incidents were disguised as:**

| Filed as | Actually was | Tickets |
|---|---|---|
| Email | Account Compromise | 28 |
| Password Reset | Account Compromise | 21 |
| Hardware | Unauthorized Remote Access | 16 |
| Password Reset | MFA Fatigue Attack | 14 |
| Account Lockout | Credential Attack | 13 |
| Software Issue | Malware | 13 |
| Software Issue | Credential Phishing | 10 |
| Access Request | Social Engineering | 9 |


## 6. Departments
- Most security incidents: **Operations** (64, 16% of its tickets)
