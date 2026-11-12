# Password Reset and MFA

This document covers password rules, self-service password reset, and multi-factor authentication (MFA) at Acme Corp.

## Password rules

- Minimum length is 14 characters.
- Passwords must contain at least three of the following: uppercase letters, lowercase letters, digits, symbols.
- Passwords expire every 180 days. You receive an email reminder 14 days before expiry.
- You cannot reuse your last 12 passwords.
- Your account is locked for 15 minutes after 5 failed sign-in attempts.

## Resetting a forgotten password

1. Go to `https://password.acme.example`.
2. Enter your Acme username and click "Forgot password".
3. Verify your identity with the Acme Authenticator app.
4. Choose a new password that follows the rules above.

The new password is active on all systems within 5 minutes.

If you have lost access to your authenticator app, call the helpdesk at +1 555 010 0100. The agent will verify your identity using your employee ID and your manager's name.

## Setting up MFA

MFA is mandatory for all employees.

1. Install the Acme Authenticator app from your phone's app store.
2. Sign in to `https://account.acme.example` and open Security > Add device.
3. Scan the QR code with the app.
4. Enter the 6-digit code shown in the app to confirm.

Register a second device or print the backup codes as a fallback. Backup codes can each be used once.

## Replacing a phone

Before you return or reset your old phone, sign in to `https://account.acme.example`, open Security, and move the authenticator to the new phone. If the old phone is already lost, ask the helpdesk to reset your MFA registration. This request is completed within 1 business hour during support hours.

## Locked accounts

A locked account unlocks automatically after 15 minutes. To unlock it immediately, use the self-service portal or contact the helpdesk.
