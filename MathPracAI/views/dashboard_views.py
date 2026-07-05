from html import escape

from views.shared_views import page_shell, profile_menu


def render_dashboard_page(
    user,
    section,
    students,
    tutors,
    workspace_students,
    workspace_tutors,
    active_student=None,
    active_tutor=None,
    query="",
):
    body = f"""  <main class="dashboard-shell">
    {render_nav_sidebar(user, section, workspace_students, workspace_tutors, active_student, active_tutor)}
    <section class="dashboard-main">
      {render_main_content(user, section, students, tutors, active_student, active_tutor, query)}
    </section>
    {render_code_modals(user)}
  </main>"""
    return page_shell(body, "MathPracAI Dashboard")


def render_nav_sidebar(user, section, workspace_students, workspace_tutors, active_student, active_tutor):
    tutor_section = ""
    if user.get("role") == "admin":
        tutor_items = workspace_items("tutor", workspace_tutors, active_tutor)
        tutor_section = f"""<div class="workspace-section">
          <a class="workspace-heading{' is-current' if section == 'tutors' and not active_tutor else ''}" href="/dashboard/tutors">Tutors</a>
          {tutor_items}
        </div>"""

    return f"""<aside class="dashboard-sidebar">
      <div class="dashboard-brand">
        <div class="brand-mark">M</div>
        <span>MathPracAI</span>
      </div>
      <div class="dashboard-sidebar-divider"></div>
      <div class="workspace-list">
        <div class="workspace-section">
          <a class="workspace-heading{' is-current' if section == 'students' and not active_student else ''}" href="/dashboard/students">Students</a>
          {workspace_items("student", workspace_students, active_student)}
        </div>
        {tutor_section}
      </div>
      <div class="dashboard-sidebar-divider"></div>
      {profile_menu(user)}
    </aside>"""


def workspace_items(item_type, items, active_item):
    if not items:
        label = "students" if item_type == "student" else "tutors"
        return f'<p class="workspace-empty">No {label} open</p>'
    html = []
    active_id = active_item.get("id") if active_item else None
    for item in items:
        active = item.get("id") == active_id
        html.append(
            f"""<div class="workspace-item{' is-active' if active else ''}">
          <a href="/dashboard/workspace/activate/{escape(item_type)}/{escape(item['id'])}">{escape(item['name'])}</a>
          <form action="/dashboard/workspace/close/{escape(item_type)}/{escape(item['id'])}" method="post">
            <button type="submit" aria-label="Close {escape(item['name'])}">x</button>
          </form>
        </div>"""
        )
    return "".join(html)


def render_main_content(user, section, students, tutors, active_student, active_tutor, query):
    if active_student:
        return render_student_profile(active_student)
    if active_tutor:
        return render_tutor_profile(active_tutor)
    if section == "tutors" and user.get("role") == "admin":
        return render_tutors_section(tutors, query)
    return render_students_section(students, query)


def render_students_section(students, query):
    cards = "".join(student_card(student) for student in students)
    if not cards:
        cards = empty_state("students", "No students yet.", "Create Class Code", "class")
    return f"""<div class="dashboard-content">
      <div class="dashboard-heading-row">
        <h1>Students</h1>
        {search_form("/dashboard/students", "Search students...", query)}
      </div>
      <div class="dashboard-card-grid">{cards}</div>
    </div>"""


def render_tutors_section(tutors, query):
    cards = "".join(tutor_card(tutor) for tutor in tutors)
    if not cards:
        cards = empty_state("tutors", "No tutors yet.", "Create Tutor Code", "tutor")
    return f"""<div class="dashboard-content">
      <div class="dashboard-heading-row">
        <h1>Tutors</h1>
        {search_form("/dashboard/tutors", "Search tutors...", query)}
      </div>
      <div class="dashboard-card-grid">{cards}</div>
    </div>"""


def search_form(action, placeholder, query):
    return f"""<form class="dashboard-search" action="{escape(action)}" method="get">
      <span aria-hidden="true">⌕</span>
      <input name="q" value="{escape(query)}" placeholder="{escape(placeholder)}">
    </form>"""


def student_card(student):
    score = student.get("lastTestScore")
    score_html = f'<strong class="{score_class(score)}">{score}%</strong>' if score is not None else ""
    needs_help = student.get("needsHelp")
    status = "red" if score is None else "yellow" if needs_help or score < 80 else "green"
    detail = (
        f'<div><span>Needs Help</span><p>{escape(needs_help)}</p></div>'
        if needs_help
        else '<p class="on-track">On track</p>'
    )
    if score is None:
        detail = '<p class="needs-activity">No activity yet</p>'
    return f"""<form action="/dashboard/workspace/open/student/{escape(student['id'])}" method="post">
      <button class="dashboard-card student-card" type="submit">
        <div class="card-title-row">
          <div class="name-with-status">
            <span class="status-dot {status}"></span>
            <div>
              <h2>{escape(student['name'])}</h2>
              <p>Active {escape(str(student.get('lastActive') or 'No activity yet'))}</p>
            </div>
          </div>
          {score_html}
        </div>
        <div class="dashboard-card-divider"></div>
        {detail}
      </button>
    </form>"""


def tutor_card(tutor):
    return f"""<form action="/dashboard/workspace/open/tutor/{escape(tutor['id'])}" method="post">
      <button class="dashboard-card tutor-card" type="submit">
        <div class="tutor-card-header">
          <span class="profile-avatar">{escape(tutor['name'][:1].upper())}</span>
          <div>
            <h2>{escape(tutor['name'])}</h2>
            <p>Active {escape(str(tutor.get('lastActive') or 'No activity yet'))}</p>
          </div>
        </div>
        <div class="dashboard-card-divider"></div>
        <div class="metric-grid">
          <div><span>Students</span><strong>{escape(str(tutor.get('studentCount', 0)))}</strong></div>
          <div><span>Class Codes</span><strong>{escape(str(tutor.get('activeClassCodes', 0)))}</strong></div>
        </div>
      </button>
    </form>"""


def render_student_profile(student):
    last_test = f"{student.get('lastTestScore')}%" if student.get("lastTestScore") is not None else "-"
    return f"""<div class="profile-page">
      <div class="profile-page-header">
        <a class="profile-back" href="/dashboard/students">‹</a>
        <span class="profile-avatar large">{escape(student['name'][:1].upper())}</span>
        <div>
          <h1>{escape(student['name'])}</h1>
          <p>Student</p>
        </div>
      </div>
      <div class="profile-stat-grid">
        {profile_stat("Last Test", last_test)}
        {profile_stat("Last Active", student.get("lastActive") or "No activity yet")}
        {profile_stat("Needs Help", student.get("needsHelp") or "None")}
      </div>
      {placeholder_panel("Today's Progress")}
      {placeholder_panel("Week Progress")}
      {placeholder_panel("All-Time Progress")}
      <section class="profile-panel">
        <h2>Recent Tests</h2>
        {empty_state("tests", "No tests completed yet.", "", "")}
      </section>
    </div>"""


def render_tutor_profile(tutor):
    return f"""<div class="profile-page">
      <div class="profile-page-header">
        <span class="profile-avatar large">{escape(tutor['name'][:1].upper())}</span>
        <div>
          <h1>{escape(tutor['name'])}</h1>
          <p>Tutor · Active {escape(str(tutor.get('lastActive') or 'No activity yet'))}</p>
        </div>
      </div>
      <div class="profile-stat-grid">
        {profile_stat("Students", tutor.get("studentCount", 0))}
        {profile_stat("Class Codes", tutor.get("activeClassCodes", 0))}
        {profile_stat("Last Active", tutor.get("lastActive") or "No activity yet")}
      </div>
      {placeholder_panel("Students")}
    </div>"""


def profile_stat(label, value):
    return f"""<div class="profile-stat">
      <span>{escape(str(label))}</span>
      <strong>{escape(str(value))}</strong>
    </div>"""


def placeholder_panel(title):
    return f"""<section class="profile-panel">
      <h2>{escape(title)}</h2>
      <p>No data available yet.</p>
    </section>"""


def empty_state(kind, message, action, modal):
    button = ""
    if action and modal:
        button = f'<button class="btn btn-accent" type="button" data-open-code-modal="{escape(modal)}">{escape(action)}</button>'
    return f"""<div class="dashboard-empty dashboard-empty-{escape(kind)}">
      <div class="empty-icon">{'T' if kind == 'tutors' else 'S' if kind == 'students' else '✓'}</div>
      <p>{escape(message)}</p>
      {button}
    </div>"""


def render_code_modals(user):
    class_modal = ""
    tutor_modal = ""
    if user.get("role") in ("tutor", "admin"):
        class_modal = code_modal(
            "class",
            "Create Class Code",
            "/dashboard/codes/class",
            '<label class="auth-field"><span>Class Name</span><input name="label" placeholder="Period 3 - Algebra 2" autocomplete="off"></label>',
        )
    if user.get("role") == "admin":
        tutor_modal = code_modal("tutor", "Create Tutor Code", "/dashboard/codes/tutor", "")
    return class_modal + tutor_modal


def code_modal(modal_type, title, action, fields):
    return f"""<div class="code-modal" data-code-modal="{escape(modal_type)}" hidden>
      <div class="code-modal-backdrop" data-close-code-modal></div>
      <form class="code-dialog" action="{escape(action)}" method="post" data-code-form>
        <div class="dialog-header">
          <div><h2>{escape(title)}</h2></div>
          <button class="icon-button" type="button" data-close-code-modal aria-label="Close">x</button>
        </div>
        <div class="dialog-body">
          {fields}
          <div class="generated-code-box" data-generated-code-box hidden>
            <span>Generated Code</span>
            <strong data-generated-code></strong>
          </div>
          <p class="code-modal-error" data-code-error hidden></p>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" type="button" data-close-code-modal>Cancel</button>
          <button class="btn btn-secondary" type="button" data-copy-code hidden>Copy</button>
          <button class="btn btn-accent" type="submit" data-generate-code>Generate</button>
        </div>
      </form>
    </div>"""


def score_class(score):
    if score is None:
        return ""
    if score >= 80:
        return "score-good"
    if score >= 60:
        return "score-warn"
    return "score-bad"
