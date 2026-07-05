from html import escape

from views.shared_views import page_shell


def auth_shell(content):
    return page_shell(
        f"""  <main class="auth-screen">
    <div class="auth-brand">
      <div class="brand-mark auth-brand-mark">M</div>
      <span>MathPracAI</span>
    </div>
    <section class="auth-card">
      {content}
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
        {role_choice("student", "Student", "Practice problems and take tests", "S")}
        {role_choice("tutor", "Tutor", "Manage students and view progress", "T")}
        {role_choice("admin", "Admin", "Full platform access and management", "A")}
      </div>"""
    )


def role_choice(role, label, description, initial):
    return f"""<a class="role-choice" href="/auth/{escape(role)}">
          <span class="role-choice-icon">{escape(initial)}</span>
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
      <form class="auth-form" action="/auth/login" method="post">
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
        <div class="auth-note">You'll need a class code before creating a student account.</div>
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
      <form class="auth-form" action="/auth/student/signup" method="post">
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
        <div class="auth-note">Tutor accounts require an administrator invite code.</div>
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
      <form class="auth-form" action="/auth/tutor/signup" method="post">
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
