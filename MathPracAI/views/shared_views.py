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
        create_class = """<button type="button" data-open-code-modal="class">Create Class Code</button>"""
    if role == "admin":
        create_tutor = """<button type="button" data-open-code-modal="tutor">Create Tutor Code</button>"""
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
          <button type="button" disabled>Settings <small>Soon</small></button>
          <form action="/auth/logout" method="post">
            <button class="profile-logout" type="submit">Logout</button>
          </form>
        </div>
      </div>
    </div>"""


def full_name(user):
    return " ".join(part for part in (user.get("firstName"), user.get("lastName")) if part).strip() or user.get("email", "User")
