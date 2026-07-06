from html import escape


def page_shell(body, title="MathPracAI"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js" defer></script>
</head>
<body>
{body}
</body>
</html>"""


def profile_menu(user):
    role = user.get("role", "student")
    display_name = full_name(user)
    create_class = ""
    create_tutor = ""
    if role in ("tutor", "admin"):
        create_class = f"""<button type="button" data-open-code-modal="class">{icon("hash")}<span>Create Class Code</span></button>"""
    if role == "admin":
        create_tutor = f"""<button type="button" data-open-code-modal="tutor">{icon("key-round")}<span>Create Tutor Code</span></button>"""
    return f"""<div class="profile-menu" data-profile-menu>
      <button class="profile-trigger" type="button" data-profile-trigger>
        <span class="profile-avatar">{escape(display_name[:1].upper() or 'M')}</span>
        <span class="profile-copy">
          <strong>{escape(display_name)}</strong>
          <small>{escape(role.capitalize())}</small>
        </span>
        <span class="profile-chevron">⌄</span>
      </button>
      <div class="profile-dropdown" data-profile-dropdown hidden>
        <div class="profile-dropdown-header">
          <strong>{escape(display_name)}</strong>
          <small>{escape(role.capitalize())}</small>
        </div>
        <div class="profile-dropdown-actions">
          <span class="profile-role-label">{escape(role.capitalize())}</span>
          {create_class}
          {create_tutor}
          <button type="button" disabled>{icon("settings")}<span>Settings</span><small>Soon</small></button>
          <form action="/auth/logout" method="post">
            <button class="profile-logout" type="submit">{icon("log-out")}<span>Logout</span></button>
          </form>
        </div>
      </div>
    </div>"""


def full_name(user):
    return " ".join(part for part in (user.get("firstName"), user.get("lastName")) if part).strip() or user.get("email", "User")


def icon(name):
    paths = {
        "hash": """<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>""",
        "key-round": """<path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"/><circle cx="16.5" cy="7.5" r=".5"/>""",
        "settings": """<path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.32-1.915Z"/><circle cx="12" cy="12" r="3"/>""",
        "log-out": """<path d="m16 17 5-5-5-5"/><path d="M21 12H9"/><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>""",
    }
    return f"""<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths.get(name, "")}</svg>"""
