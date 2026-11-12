# VPN Setup

This guide explains how to connect to the Acme Corp network from outside the office using the Acme SecureConnect VPN client.

## Requirements

- A company laptop managed by IT, or an approved personal device with a registered certificate.
- An active Acme account with multi-factor authentication (MFA) enabled.
- A stable internet connection of at least 5 Mbit/s.

## Installing the client

1. Open the Software Center on your company laptop.
2. Search for "Acme SecureConnect" and click Install.
3. Restart the laptop when the installation finishes.

The client is preinstalled on all laptops issued after January 2024.

## Connecting

1. Start Acme SecureConnect from the system tray.
2. Enter the gateway address `vpn.acme.example`.
3. Sign in with your Acme username and password.
4. Approve the push notification in the Acme Authenticator app.

The connection is established within about 10 seconds. A green lock icon in the tray means you are connected.

## Session limits

- A VPN session ends automatically after 12 hours. Reconnect to continue working.
- A session is disconnected after 30 minutes of inactivity.
- Only one active VPN session per user is allowed.

## Troubleshooting

### Error 691 or "Authentication failed"

Your password may have expired or your account may be locked. Reset the password at `https://password.acme.example` and try again.

### Connection drops repeatedly

Switch from Wi-Fi to a wired connection if possible, and disable any third-party VPN or firewall software. If the problem remains, open a ticket at `https://helpdesk.acme.example` and attach the client log from Help > Export Logs.

### No access to internal sites after connecting

Wait one minute for the DNS settings to refresh, then restart your browser. If the sites are still unreachable, contact the helpdesk.
