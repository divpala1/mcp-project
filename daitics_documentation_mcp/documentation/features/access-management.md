---
id: features/access-management
title: Access Management in Daitics DTX Portal
category: features
summary: Access Management is where administrators add and remove users, group them, assign roles and permissions, and end active sessions in Daitics DTX Portal.
tags: [access-management, users, groups, roles, permissions, sessions]
aliases:
  - user management
  - role management
  - permissions
  - rbac
  - keycloak users
  - admin panel
last_updated: 2026-05-02
version: 1
---

# Access Management in Daitics DTX Portal

## What Access Management is in Daitics DTX Portal {#what-access-management-is-in-daitics-dtx-portal}

Access Management in Daitics DTX Portal is where administrators decide who can use the portal and what each person can do. It covers four things: users, groups, roles, and active sessions. Most pages here are admin-only — if you are not an administrator, you will only see your own profile.

User accounts in Access Management mirror your organization's identity service (Keycloak). Changes you make here apply to the portal immediately and to other Daitics tools that use the same identity service.

## When you would use Access Management in Daitics DTX Portal {#when-you-would-use-access-management-in-daitics-dtx-portal}

You would use Access Management in Daitics DTX Portal as an administrator to:

- Add or remove portal users.
- Assign someone to a role so they can use a specific feature.
- Group users together (by team, project, or department) and assign roles to the whole group.
- Reset a user's password if they are locked out.
- End an active session if you suspect a security issue or if a user left their device signed in.
- Build a custom role with the exact set of permissions your team needs.

## Where to find Access Management in Daitics DTX Portal {#where-to-find-access-management-in-daitics-dtx-portal}

Access Management in Daitics DTX Portal lives under **Access Management** in the sidebar. The section has three pages you will use:

- **Users** — every account in the portal.
- **User Groups** — groups that bundle users together.
- **Roles & Permissions** — the catalog of roles and what each one can do.

## What you can do on the Users page {#what-you-can-do-on-the-users-page}

The Users page in Daitics DTX Portal lists every portal user. You can:

- **Search** by name, email, or username.
- **Filter** by status (Active, Deactivated) or by group membership.
- **Click a user** to open their profile, which shows roles, group memberships, and active sessions.
- **Assign or revoke a role** from the profile page.
- **Reset a password** to send the user a new sign-in flow.
- **Reactivate a deactivated user** to restore their access.
- **Terminate a session** to force a user to sign in again.

## What you can do on the User Groups page {#what-you-can-do-on-the-user-groups-page}

The User Groups page in Daitics DTX Portal lists every group, with hierarchical paths so you can see parent and child groups. You can:

- **Search** for a group by name.
- **Click a group** to see its members and any sub-groups.
- **Assign a role to the group** so every member inherits it.

Groups are useful when you want to grant the same access to many users at once. Adding a user to a group automatically gives them every role the group has.

## What you can do on the Roles and Permissions page {#what-you-can-do-on-the-roles-and-permissions-page}

The Roles & Permissions page in Daitics DTX Portal lists every role and what it can do. You can:

- **Search** for a role by name.
- **Toggle "show system roles"** to switch between built-in roles and custom ones your team created.
- **Create a custom role** with a granular permission picker. Permissions are grouped by resource (read, write, delete, admin).
- **Edit a custom role** to change its permissions.
- **View role assignments** to see which users and groups have a role.
- **Delete a custom role** when it is no longer needed.

System roles are read-only. You cannot edit or delete them.

## Sessions in Daitics DTX Portal {#sessions-in-daitics-dtx-portal}

A session in Daitics DTX Portal represents one signed-in window for one user. You see active sessions on each user's profile page. Each session shows the time the user signed in and a session identifier. Click **Terminate** on a session to force the user to sign back in. Terminating sessions is useful when:

- A user reports their account was used without their permission.
- A user left a session open on a shared computer.
- You need to apply a role change immediately, before the next sign-in.

## Limits and things to know about Access Management {#limits-and-things-to-know-about-access-management}

A few things to keep in mind when working with Access Management in Daitics DTX Portal:

- You cannot create users from inside the portal directly — user provisioning happens in the identity service. Once a user exists, you manage their portal access here.
- System roles cannot be modified or deleted.
- Deactivating a user does not delete their data or their portal history. It only blocks future sign-ins until you reactivate them.
- Password resets do not show you the new password. The user receives a new sign-in flow through the identity service.

## Related how-to guides {#related-how-to-guides}

For step-by-step instructions on common Access Management tasks in Daitics DTX Portal:

- [Add a user to a role](../how-to/add-a-user-to-a-role.md)
- [Create a custom role](../how-to/create-a-custom-role.md)
- [Reset a user password](../how-to/reset-a-user-password.md)
- [Assign a role to a group](../how-to/assign-a-role-to-a-group.md)
- [Terminate a user session](../how-to/terminate-a-user-session.md)
