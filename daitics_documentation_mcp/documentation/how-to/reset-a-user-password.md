---
id: how-to/reset-a-user-password
title: Reset a user password in Daitics DTX Portal
category: how-to
summary: To reset a user password, open Access Management → Users, find the user, open their profile, and click Reset password. The user receives a new sign-in flow from the identity service.
tags: [admin, access-management, password, reset, user]
aliases:
  - password reset
  - send password reset
  - user locked out
  - forgot password admin
  - admin reset password
last_updated: 2026-05-02
version: 1
---

# Reset a user password in Daitics DTX Portal

## What this does {#what-this-does}

Resetting a user password in Daitics DTX Portal sends the user through the identity service's password reset flow. You do not see or set the new password — the user picks it themselves on the identity service side. Their existing password stops working immediately.

This task is for administrators only. Users who want to change their own password do that through the identity service, not through the portal.

## When you would reset a user password {#when-you-would-reset-a-user-password}

You would reset a user password in Daitics DTX Portal when you need to:

- Help a teammate who is locked out and asking for help.
- Force a password change for security reasons (for example, after a suspected compromise).
- Re-onboard someone whose previous credentials are no longer valid.

If the user can sign in but cannot do the things they need to do, the issue is with their roles, not their password. See [Add a user to a role](add-a-user-to-a-role.md).

## Steps to reset a user password {#steps-to-reset-a-user-password}

Follow these steps to reset a user password in Daitics DTX Portal:

1. In the sidebar, click **Access Management → Users**.
2. Search for the user by name, email, or username.
3. Click the user's row to open their profile.
4. Click **Reset password** at the top of the profile.
5. Confirm the action when prompted.

The portal sends the request to the identity service, which then takes over and contacts the user.

## What to expect after resetting a user password {#what-to-expect-after-resetting-a-user-password}

After resetting a user password in Daitics DTX Portal, you should see:

- A green toast confirms the action.
- The user's existing password stops working immediately.
- The user receives a password-reset prompt the next time they try to sign in (the exact experience depends on your identity service settings).
- Active sessions for the user may also end, depending on identity service configuration. To force sign-out everywhere, terminate their sessions explicitly — see [Terminate a user session](terminate-a-user-session.md).

The portal does not show you the new password. The user sets it themselves.

## If something goes wrong resetting a password {#if-something-goes-wrong-resetting-a-password}

If something goes wrong while resetting a user password in Daitics DTX Portal, check the most likely causes:

- **"Reset password" button is greyed out** — your account does not have admin privileges. Ask another administrator.
- **"Failed to reset password"** — the identity service did not respond. Check the toast's details. If the issue persists, ask your platform team.
- **The user did not receive any notification** — confirm their email address is correct on their profile, and check whether the identity service is configured to send password-reset emails.
- **The user reports they still cannot sign in after resetting** — confirm the user's status is **Active**. If the user is **Deactivated**, reactivate them first.

For more help, see [Troubleshooting](../troubleshooting.md).
