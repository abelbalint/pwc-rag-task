# Wi-Fi and Guest Network

Acme Corp offers separate wireless networks for employees and visitors.

## Available networks

| Network name | Who can use it | Authentication |
|---|---|---|
| Acme-Corp | Employees with company devices | Certificate, installed automatically |
| Acme-BYOD | Employees with personal devices | Acme username and password plus MFA |
| Acme-Guest | Visitors | Daily access code |

## Connecting a company laptop

Company laptops connect to Acme-Corp automatically inside the office. No password is needed. If the laptop does not connect, restart it and check that Wi-Fi is turned on. If it still fails, contact the helpdesk.

## Connecting a personal device

1. Select the Acme-BYOD network.
2. Sign in with your Acme username and password.
3. Approve the MFA prompt.

Personal devices have access to the internet and a limited set of internal services, such as email and the intranet. They cannot reach file servers.

## Guest access

Visitors use the Acme-Guest network. A host employee creates a guest code:

1. Open `https://guest.acme.example` and sign in.
2. Click "New guest" and enter the visitor's name and visit date.
3. Give the 8-character code to the visitor.

A guest code is valid for 1 day. Guest traffic is separated from the company network, and each guest can use up to 5 GB per day.

## Troubleshooting

- Slow connection: move closer to an access point, or use a wired port at your desk.
- "Cannot obtain IP address": turn Wi-Fi off and on, then reconnect.
- Repeated password prompts on Acme-BYOD: reset your password at `https://password.acme.example`.

Report dead zones in the office to the helpdesk and include the floor and the nearest meeting room.
