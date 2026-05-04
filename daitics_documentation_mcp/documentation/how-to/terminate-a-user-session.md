---
id: how-to/terminate-a-user-session
title: Terminate a user session in Daitics DTX Portal
category: how-to
summary: To terminate a user session, open Access Management → Users, find the user, open their profile, and click Terminate next to the session you want to end.
tags: [admin, access-management, session, sign-out, security]
aliases:
  - end user session
  - force sign out
  - kick user
  - log user out
  - revoke session
  - kill session
last_updated: 2026-05-02
version: 1
---

# Terminate a user session in Daitics DTX Portal

## What this does {#what-this-does}

Terminating a user session in Daitics DTX Portal forces a signed-in user to sign in again. Each session represents one signed-in browser window. Terminating ends just that one session — if the user has other open windows, those keep working unless you terminate them too.

This task is for administrators only.

## When you would terminate a user session {#when-you-would-terminate-a-user-session}

You would terminate a user session in Daitics DTX Portal when you need to:

- Apply a role change immediately, before the user's next natural sign-in.
- Sign out a user who left a session open on a shared computer.
- Respond to a security incident — for example, when a user's account is suspected to be compromised.
- Force someone to sign back in after their permissions changed.

If you want to disable a user entirely, deactivate them on their profile rather than terminating individual sessions.

## Steps to terminate a user session {#steps-to-terminate-a-user-session}

Follow these steps to terminate a user session in Daitics DTX Portal:

1. In the sidebar, click **Access Management → Users**.
2. Search for the user by name, email, or username.
3. Click the user's row to open their profile.
4. Scroll to the **Active sessions** section.
5. Find the session you want to end (each row shows a sign-in time and a session identifier).
6. Click **Terminate** next to that row.
7. Confirm if asked.

To end every session at once, click **Terminate all sessions** at the top of the section if your version of the portal exposes that option.

## What to expect after terminating a session {#what-to-expect-after-terminating-a-session}

After terminating a user session in Daitics DTX Portal, you should see:

- The session disappears from the **Active sessions** list.
- A green toast confirms the action.
- The user is signed out of that browser window the next time they make a request — usually within seconds.

The user can sign back in immediately as long as their account is active and their password still works.

## If something goes wrong terminating a session {#if-something-goes-wrong-terminating-a-session}

If something goes wrong while terminating a user session in Daitics DTX Portal, check the most likely causes:

- **The Terminate action is greyed out** — your account does not have admin privileges, or the session has already ended on its own. Refresh the profile.
- **"Failed to terminate session"** — the identity service did not respond. Check the toast's details. Try again, then ask another administrator if it keeps failing.
- **The user reports they are still signed in after termination** — they may have other sessions you did not terminate. Refresh the profile and check the Active sessions list.
- **You see no Active sessions even though the user is signed in** — refresh the profile. If still empty, the identity service may not be reporting sessions to the portal.

For more help, see [Troubleshooting](../troubleshooting.md).
