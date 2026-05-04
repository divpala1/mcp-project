---
id: how-to/add-a-user-to-a-role
title: Add a user to a role in Daitics DTX Portal
category: how-to
summary: To add a user to a role, open Access Management → Users, find the user, open their profile, then assign a role from the Roles section.
tags: [admin, access-management, role, user, assign]
aliases:
  - assign a role
  - give a user a role
  - grant role
  - set user role
  - add role to user
last_updated: 2026-05-02
version: 1
---

# Add a user to a role in Daitics DTX Portal

## What this does {#what-this-does}

Adding a user to a role in Daitics DTX Portal grants that user every permission the role includes. Roles control what users can see and do in the portal — for example, who can create pipelines, deploy them, or manage other users. A user can have several roles; their effective permissions are the union of all of them.

This task is for administrators only. If the role assignment options are missing for you, your account does not have admin privileges.

## When you would add a user to a role {#when-you-would-add-a-user-to-a-role}

You would add a user to a role in Daitics DTX Portal when you need to:

- Onboard a new teammate and give them the access they need.
- Promote someone (for example, give a data engineer the admin role for a project).
- Replace a role that has been retired with a newer one.
- Restore access for a user whose roles were removed accidentally.

If many users need the same role, consider assigning the role to a group instead — see [Assign a role to a group](assign-a-role-to-a-group.md).

## Steps to add a user to a role {#steps-to-add-a-user-to-a-role}

Follow these steps to add a user to a role in Daitics DTX Portal:

1. In the sidebar, click **Access Management → Users**.
2. Search for the user by name, email, or username.
3. Click the user's row to open their profile.
4. Find the **Roles** section.
5. Click **Assign role**.
6. In the dialog, pick the role from the list. Use the search box if the list is long.
7. Click **Assign**.

The change takes effect immediately for new sign-ins. If the user is currently signed in, ask them to sign out and back in, or terminate their sessions on the same profile page so the change applies right away.

## What to expect after adding a user to a role {#what-to-expect-after-adding-a-user-to-a-role}

After adding a user to a role in Daitics DTX Portal, you should see:

- The role appears in the user's **Roles** section on their profile.
- A green toast confirms "Role assigned".
- The user gains the role's permissions on their next sign-in (or immediately, if you terminate their existing sessions).

To remove a role, click the role chip in the user's Roles section and pick **Revoke**.

## If something goes wrong adding a user to a role {#if-something-goes-wrong-adding-a-user-to-a-role}

If something goes wrong while adding a user to a role in Daitics DTX Portal, check the most likely causes:

- **You cannot find the role you want** — type part of its name into the search box. If still missing, the role may not exist yet — see [Create a custom role](create-a-custom-role.md).
- **"Assign role" is greyed out** — your account may not have admin privileges. Ask another administrator to assign the role.
- **"Failed to assign role"** — your network may have dropped. Try again. If it keeps failing, ask another administrator.
- **The user reports they still cannot do the thing the role allows** — they may be using a session from before the change. Terminate their sessions on the profile page.

For more help, see [Troubleshooting](../troubleshooting.md).
