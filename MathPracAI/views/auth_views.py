from html import escape

from views.shared_views import page_shell


def auth_shell(content):
    return page_shell(
        f"""  <main class="auth-screen">
    <section class="auth-visual-panel" aria-label="MathPracAI">
      <img class="auth-geometry" src="/static/assets/ui/auth-panel-geometry.svg" alt="" aria-hidden="true">
      <div class="auth-symbol-field" aria-hidden="true">
        <span class="auth-symbol symbol-a">∑</span>
        <span class="auth-symbol symbol-b">π</span>
        <span class="auth-symbol symbol-c">f(x)</span>
        <span class="auth-symbol symbol-d">x²</span>
        <span class="auth-symbol symbol-e">√x</span>
        <span class="auth-symbol symbol-f">Δ</span>
        <span class="auth-symbol symbol-g">∞</span>
        <span class="auth-symbol symbol-h">∫</span>
      </div>
      <div class="auth-panel-brand">
        <img src="/static/assets/logos/mathpracai-wordmark-white.svg" alt="MathPracAI">
      </div>
      <div class="auth-panel-copy">
        <p>Practice until<br>it's effortless.</p>
        <span>Unlimited problems. Every topic.</span>
      </div>
    </section>
    <section class="auth-content-panel">
      <div class="auth-card auth-content-in">
        {content}
      </div>
      {google_name_modal()}
    </section>
  </main>""",
        "MathPracAI Auth",
    )


def auth_error(message):
    return f'<p class="auth-error">{escape(message)}</p>' if message else ""


def render_role_select(error=""):
    return auth_shell(
        f"""<div class="auth-copy">
        <h1>Welcome</h1>
        <p>How are you using MathPracAI?</p>
      </div>
      {auth_error(error)}
      <div class="role-choice-stack">
        {role_choice("student", "Student", "Practice problems and take tests", "graduation-cap")}
        {role_choice("tutor", "Tutor", "Manage students and view progress", "book-open")}
        {role_choice("admin", "Admin", "Full platform access and management", "shield-check")}
      </div>"""
    )


def role_choice(role, label, description, icon_name):
    return f"""<a class="role-choice" href="/auth/{escape(role)}">
          <span class="role-choice-icon">{icon(icon_name)}</span>
          <span>
            <strong>{escape(label)}</strong>
            <small>{escape(description)}</small>
          </span>
        </a>"""


def render_login(role, error=""):
    role_label = role.capitalize()
    tabs = auth_mode_tabs(role, "signin")
    admin_note = '<div class="auth-footer-link"><span>Admin accounts are privately created</span></div>' if role == "admin" else ""

    return auth_shell(
        f"""<div class="auth-header-row">
        <a class="auth-back" href="/auth" aria-label="Back">‹</a>
        <div class="auth-copy">
          <h1>{escape(role_label)}</h1>
          <p>Sign in to your account</p>
        </div>
      </div>
      {tabs}
      {auth_error(error)}
      {auth_provider_choices("/auth/google-login", role=role)}
      <form class="auth-form" id="email-auth-form" action="/auth/login" method="post">
        <input type="hidden" name="selected_role" value="{escape(role)}">
        {auth_input("email", "Email", "email", "you@school.edu")}
        {auth_input("password", "Password", "password", "Password")}
        <button class="btn btn-accent auth-submit" type="submit">Sign In</button>
      </form>
      {admin_note}"""
    )


def auth_mode_tabs(role, active):
    if role == "admin":
        return ""
    signup_href = "#" if role == "admin" else f"/auth/{escape(role)}/signup"
    signin_href = f"/auth/{escape(role)}"
    return f"""<div class="auth-mode-toggle">
        <a class="{'is-active' if active == 'signin' else ''}" href="{signin_href}">Sign In</a>
        <a class="{'is-active' if active == 'signup' else ''}" href="{signup_href}">Sign Up</a>
      </div>"""


def render_student_code_step(error="", values=None):
    values = values or {}
    return auth_shell(
        f"""<div class="auth-header-row">
        <a class="auth-back" href="/auth/student" aria-label="Back">‹</a>
        <div class="auth-copy">
          <h1>Student</h1>
          <p>Enter the class code provided by your teacher.</p>
        </div>
      </div>
      {auth_mode_tabs("student", "signup")}
      {auth_error(error)}
      <form class="auth-form" action="/auth/student/signup" method="post">
        <input type="hidden" name="step" value="code">
        <div class="auth-note">{icon("key-round")}<span>You'll need a class code before creating a student account.</span></div>
        {auth_input("class_code", "Class Code", "text", "7KX9QM", values.get("class_code", ""), "code-input")}
        <button class="btn btn-accent auth-submit" type="submit">Verify Code</button>
      </form>"""
    )


def render_student_signup(error="", values=None):
    values = values or {}
    class_code = values.get("class_code", "")
    return auth_shell(
        f"""<div class="auth-header-row">
        <a class="auth-back" href="/auth/student/signup" aria-label="Back">‹</a>
        <div class="auth-copy">
          <h1>Create Student Account</h1>
          <p class="auth-verified-line">Class code verified</p>
        </div>
      </div>
      {auth_mode_tabs("student", "signup")}
      {auth_error(error)}
      {auth_provider_choices("/auth/student/google-signup", role="student", class_code=class_code)}
      <form class="auth-form" id="email-auth-form" action="/auth/student/signup" method="post">
        <input type="hidden" name="step" value="account">
        <input type="hidden" name="class_code" value="{escape(class_code)}">
        {auth_input("first_name", "First Name", "text", "Jane", values.get("first_name", ""))}
        {auth_input("last_name", "Last Name", "text", "Smith", values.get("last_name", ""))}
        {auth_input("email", "Email", "email", "you@school.edu", values.get("email", ""))}
        {auth_input("password", "Password", "password", "Password")}
        <button class="btn btn-accent auth-submit" type="submit">Create Account</button>
      </form>"""
    )


def render_tutor_code_step(error="", values=None):
    values = values or {}
    return auth_shell(
        f"""<div class="auth-header-row">
        <a class="auth-back" href="/auth/tutor" aria-label="Back">‹</a>
        <div class="auth-copy">
          <h1>Tutor</h1>
          <p>Enter the invite code provided by an admin.</p>
        </div>
      </div>
      {auth_mode_tabs("tutor", "signup")}
      {auth_error(error)}
      <form class="auth-form" action="/auth/tutor/signup" method="post">
        <input type="hidden" name="step" value="code">
        <div class="auth-note">{icon("key-round")}<span>Tutor accounts require an administrator invite code.</span></div>
        {auth_input("invite_code", "Tutor Invite Code", "text", "M8TR4Y", values.get("invite_code", ""), "code-input")}
        <button class="btn btn-accent auth-submit" type="submit">Verify Code</button>
      </form>"""
    )


def render_tutor_signup(error="", values=None):
    values = values or {}
    invite_code = values.get("invite_code", "")
    return auth_shell(
        f"""<div class="auth-header-row">
        <a class="auth-back" href="/auth/tutor/signup" aria-label="Back">‹</a>
        <div class="auth-copy">
          <h1>Create Tutor Account</h1>
          <p class="auth-verified-line">Invite code verified</p>
        </div>
      </div>
      {auth_mode_tabs("tutor", "signup")}
      {auth_error(error)}
      {auth_provider_choices("/auth/tutor/google-signup", role="tutor", invite_code=invite_code)}
      <form class="auth-form" id="email-auth-form" action="/auth/tutor/signup" method="post">
        <input type="hidden" name="step" value="account">
        <input type="hidden" name="invite_code" value="{escape(invite_code)}">
        {auth_input("first_name", "First Name", "text", "Jane", values.get("first_name", ""))}
        {auth_input("last_name", "Last Name", "text", "Smith", values.get("last_name", ""))}
        {auth_input("email", "Email", "email", "you@school.edu", values.get("email", ""))}
        {auth_input("password", "Password", "password", "Password")}
        <button class="btn btn-accent auth-submit" type="submit">Create Account</button>
      </form>"""
    )


def auth_input(name, label, input_type, placeholder, value="", extra_class=""):
    return f"""<label class="auth-field">
          <span>{escape(label)}</span>
          <input class="{escape(extra_class)}" name="{escape(name)}" type="{escape(input_type)}" value="{escape(value)}" placeholder="{escape(placeholder)}" autocomplete="off">
        </label>"""


def auth_provider_choices(endpoint, role, class_code="", invite_code=""):
    return f"""<div class="auth-provider-stack">
        <button
          class="auth-provider-button google-provider"
          type="button"
          data-google-auth
          data-google-endpoint="{escape(endpoint)}"
          data-role="{escape(role)}"
          data-class-code="{escape(class_code)}"
          data-invite-code="{escape(invite_code)}"
        ><span class="google-mark">G</span>Continue with Google</button>
        <a class="auth-provider-button email-provider" href="#email-auth-form">{icon("mail")}Continue with Email</a>
        <p class="auth-google-error" data-google-auth-error hidden></p>
      </div>
      <div class="auth-divider"><span>or</span></div>"""


def google_name_modal():
    return f"""<div class="google-name-modal" data-google-name-modal hidden>
        <div class="google-name-card">
          <h2>Finish your profile</h2>
          <p>Enter your first and last name to finish Google signup.</p>
          <label class="auth-field">
            <span>First Name</span>
            <input name="google_first_name" type="text" autocomplete="given-name">
          </label>
          <label class="auth-field">
            <span>Last Name</span>
            <input name="google_last_name" type="text" autocomplete="family-name">
          </label>
          <p class="auth-google-error" data-google-name-error hidden></p>
          <div class="google-name-actions">
            <button class="btn btn-secondary" type="button" data-google-name-cancel>Cancel</button>
            <button class="btn btn-accent" type="button" data-google-name-submit>Continue</button>
          </div>
        </div>
      </div>"""


def icon(name):
    paths = {
        "graduation-cap": """<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.084a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>""",
        "book-open": """<path d="M12 7v14"/><path d="M3 18a1 1 0 0 0 1 1h5a3 3 0 0 1 3 3V6a3 3 0 0 0-3-3H4a1 1 0 0 0-1 1z"/><path d="M21 18a1 1 0 0 1-1 1h-5a3 3 0 0 0-3 3V6a3 3 0 0 1 3-3h5a1 1 0 0 1 1 1z"/>""",
        "shield-check": """<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>""",
        "key-round": """<path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"/><circle cx="16.5" cy="7.5" r=".5"/>""",
        "mail": """<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a2 2 0 0 1-2.06 0L2 7"/>""",
    }
    return f"""<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths.get(name, "")}</svg>"""
