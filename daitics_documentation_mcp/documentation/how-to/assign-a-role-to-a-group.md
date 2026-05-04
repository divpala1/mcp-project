---
id: how-to/assign-a-role-to-a-group
title: Assign a role to a group in Daitics DTX Portal
category: how-to
summary: To assign a role to a group, open Access Management → User Groups, click the group, and assign the role from the group's Roles section. Every member inherits the role.
tags: [admin, access-management, group, role, inherit]
aliases:
  - group role
  - assign role to user group
  - bulk role assignment
  - team role
  - inherited role
last_updated: 2026-05-02
version: 1
---

# Assign a role to a group in Daitics DTX Portal

## What this does {#what-this-does}

Assigning a role to a group in Daitics DTX Portal grants every member of the group the permissions of that role. Group-level roles are inherited automatically — you do not need to assign the role to each member individually. Adding a new user to the group later gives them the role too.

This task is for administrators only.

## When you would assign a role to a group {#when-you-would-assign-a-role-to-a-group}

You would assign a role to a group in Daitics DTX Portal when you need to:

- Give an entire team the same access at once.
- Avoid managing roles user-by-user as people join and leave.
- Roll out a new permission to many users without touching each profile.

If only one or two users need the role, assign it to them directly instead — see [Add a user to a role](add-a-user-to-a-role.md).

## Steps to assign a role to a group {#steps-to-assign-a-role-to-a-group}

Follow these steps to assign a role to a group in Daitics DTX Portal:

1. In the sidebar, click **Access Management → User Groups**.
2. Search for the group by name.
3. Click the group's row to open its detail page.
4. Find the **Roles** section.
5. Click **Assign role**.
6. Pick the role from the list (use the search box if it is long).
7. Click **Assign**.

The change applies to every current member and to any user added to the group later. To remove a role from the group, click the role chip in the Roles section and pick **Revoke**.

## What to expect after assigning a role to a group {#what-to-expect-after-assigning-a-role-to-a-group}

After assigning a role to a group in Daitics DTX Portal, you should see:

- The role appears in the group's **Roles** section.
- A green toast confirms "Role assigned".
- Every member of the group gains the role's permissions on their next sign-in.
- Open any member's profile to confirm — the role appears as inherited from the group.

To apply the role immediately for users who are currently signed in, terminate their sessions on their profile pages.

## If something goes wrong assigning a role to a group {#if-something-goes-wrong-assigning-a-role-to-a-group}

If something goes wrong while assigning a role to a group in Daitics DTX Portal, check the most likely causes:

- **"Assign role" is greyed out** — your account does not have admin privileges, or the group is read-only at the identity service level. Ask another administrator.
- **"Failed to assign role"** — your network may have dropped. Try again. If it keeps failing, ask another administrator.
- **Members do not see the role's permissions** — they may be using a session from before the change. Terminate their sessions, or ask them to sign out and back in.
- **You cannot find the group you want** — your identity service may use a hierarchical group structure. Search by part of the path, not just the leaf name.

For more help, see [Troubleshooting](../troubleshooting.md).
