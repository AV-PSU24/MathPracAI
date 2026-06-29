from html import escape
import json

from models import encoded_problem


def render_asset(asset):
    if not isinstance(asset, dict):
        return ""
    asset_type = asset.get("type", "")
    if asset_type == "image" and asset.get("src"):
        alt = asset.get("alt", "")
        return f'<img src="{escape(asset["src"])}" alt="{escape(alt)}">'
    if asset_type == "text" and asset.get("content"):
        return escape(asset["content"])
    return ""


def render_problem_display(problem):
    parts = []
    if problem.display_equation:
        parts.append(escape(problem.display_equation))
    if problem.prompt:
        parts.append(escape(problem.prompt))
    for asset in problem.assets:
        rendered_asset = render_asset(asset)
        if rendered_asset:
            parts.append(rendered_asset)
    return "<br><br>".join(parts)


def select_options(options, selected):
    html = []
    for value, label in options:
        selected_attr = " selected" if value == selected else ""
        html.append(f'<option value="{escape(value)}"{selected_attr}>{escape(label)}</option>')
    return "\n".join(html)


def custom_dropdown(name, label, options, selected, option_attrs=None):
    selected_label = next((option_label for value, option_label in options if value == selected), options[0][1])
    option_markup = []
    for index, (value, option_label) in enumerate(options):
        is_selected = value == selected
        extra_attrs = f" {option_attrs(value, option_label, index)}" if option_attrs else ""
        option_markup.append(
            f"""
            <button
              class="custom-option"
              id="{escape(name)}-option-{index}"
              role="option"
              type="button"
              data-value="{escape(value)}"
              aria-selected="{str(is_selected).lower()}"
              tabindex="-1"
              {extra_attrs}
            >{escape(option_label)}</button>"""
        )

    return f"""
        <div class="field custom-select" data-dropdown>
          <span class="field-label" id="{escape(name)}-label">{escape(label)}</span>
          <input type="hidden" name="{escape(name)}" value="{escape(selected)}">
          <button
            class="custom-select-trigger"
            type="button"
            aria-haspopup="listbox"
            aria-expanded="false"
            aria-labelledby="{escape(name)}-label {escape(name)}-value"
          >
            <span id="{escape(name)}-value" data-selected-label>{escape(selected_label)}</span>
            <span class="select-chevron" aria-hidden="true"></span>
          </button>
          <div class="custom-options" role="listbox" aria-labelledby="{escape(name)}-label">
            {''.join(option_markup)}
          </div>
        </div>"""


def page_context(state, units, difficulties, generators, valid_topic_for_unit, count_value):
    unit = state.get("unit", "unit1")
    if unit not in units:
        unit = "unit1"

    difficulty = state.get("difficulty", "easy")
    if difficulty not in difficulties:
        difficulty = "easy"

    topic = state.get("topic") or units[unit]["topics"][0][0]
    if not valid_topic_for_unit(unit, topic):
        topic = units[unit]["topics"][0][0]

    problem = state.get("problem")
    feedback = state.get("feedback", "")
    feedback_type = state.get("feedback_type", "empty")
    hint_visible = state.get("hint_visible", "") == "true"
    solution_visible = state.get("solution_visible", "") == "true"
    answered = state.get("answered", "") == "true"
    correct_count = count_value(state, "correct_count")
    hint_count = count_value(state, "hint_count")
    incorrect_count = count_value(state, "incorrect_count")
    skip_count = count_value(state, "skip_count")
    generated = state.get("generated", "") == "true"

    if problem is None:
        problem = generators[topic](difficulty)

    return {
        "unit": unit,
        "topic": topic,
        "difficulty": difficulty,
        "problem": problem,
        "feedback": feedback,
        "feedback_type": feedback_type,
        "hint_visible": hint_visible,
        "solution_visible": solution_visible,
        "answered": answered,
        "correct_count": correct_count,
        "hint_count": hint_count,
        "incorrect_count": incorrect_count,
        "skip_count": skip_count,
        "generated": generated,
    }


def render_control_panel(context, units, difficulties):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    unit_options = tuple((value, data["label"]) for value, data in units.items())
    topic_options = tuple(units[unit]["topics"])
    difficulty_options = tuple((item, item.title()) for item in difficulties)
    unit_dropdown = custom_dropdown("unit", "Unit", unit_options, unit, unit_option_attrs(units))
    topic_dropdown = custom_dropdown("topic", "Topic", topic_options, topic)
    difficulty_dropdown = custom_dropdown("difficulty", "Difficulty", difficulty_options, difficulty)

    return f"""      <form class="control-panel" action="/generate" method="get">
        <div class="panel-title">
          <span>MathPrac AI</span>
        </div>
        <input type="hidden" name="correct_count" value="{context["correct_count"]}">
        <input type="hidden" name="hint_count" value="{context["hint_count"]}">
        <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
        <input type="hidden" name="skip_count" value="{context["skip_count"]}">
        {unit_dropdown}
        {topic_dropdown}
        {difficulty_dropdown}
      </form>"""


def unit_option_attrs(units):
    def attrs(value, _label, _index):
        return f"data-topics='{escape(json.dumps(units[value]['topics']))}'"

    return attrs


def render_answer_form(context):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]
    answered = context["answered"]
    generated = context["generated"]
    correct_checked = context["feedback_type"] == "correct"
    hint_disabled = " disabled" if hint_visible or solution_visible or correct_checked else ""
    solution_disabled = " disabled" if solution_visible or correct_checked else ""
    skip_disabled = " disabled" if solution_visible or correct_checked else ""
    check_disabled = " disabled" if solution_visible or correct_checked else ""
    next_disabled = "" if correct_checked or solution_visible else " disabled"
    answer_controls = render_answer_controls(problem)

    return f"""        <form class="answer-panel" action="/check" method="post">
          <input type="hidden" name="unit" value="{escape(unit)}">
          <input type="hidden" name="topic" value="{escape(topic)}">
          <input type="hidden" name="difficulty" value="{escape(difficulty)}">
          <input type="hidden" name="problem_json" value="{encoded_problem(problem)}">
          <input type="hidden" name="hint_visible" value="{str(hint_visible).lower()}">
          <input type="hidden" name="solution_visible" value="{str(solution_visible).lower()}">
          <input type="hidden" name="answered" value="{str(answered).lower()}">
          <input type="hidden" name="correct_count" value="{context["correct_count"]}">
          <input type="hidden" name="hint_count" value="{context["hint_count"]}">
          <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
          <input type="hidden" name="skip_count" value="{context["skip_count"]}">
          <input type="hidden" name="generated" value="{str(generated).lower()}">
          <div class="answer-row">
            {answer_controls}
            <button name="action" value="check" type="submit"{check_disabled}>Check</button>
          </div>
          <div class="utility-row">
            <button name="action" value="hint" type="submit"{hint_disabled}>Hint</button>
            <button name="action" value="skip" type="submit"{skip_disabled}>Skip</button>
            <button name="action" value="solution" type="submit"{solution_disabled}>Solution</button>
            <button name="action" value="next" type="submit"{next_disabled}>Next Problem</button>
          </div>
        </form>"""


def render_answer_controls(problem):
    fields = problem.answer_fields or [{"name": "user_answer", "label": "Answer", "type": "text"}]
    if len(fields) == 1:
        return render_answer_control(fields[0], "user_answer")

    return f"""<div class="answer-fields">
              {''.join(render_labeled_answer_control(field) for field in fields)}
            </div>"""


def render_labeled_answer_control(field):
    field_name = field.get("name", "answer")
    field_id = f"answer_{field_name}"
    return f"""<div class="answer-field">
                <label for="{escape(field_id)}">{escape(field.get("label", "Answer"))}</label>
                <div class="answer-field-row">
                  {render_answer_control(field, field_name, field_id)}
                </div>
              </div>"""


def render_answer_control(field, field_name, field_id="user_answer"):
    helpers = field.get("helpers") if isinstance(field, dict) else None
    helper_buttons = render_answer_helpers(helpers if isinstance(helpers, list) else [])
    return f"""<input id="{escape(field_id)}" name="{escape(field_name)}" type="{escape(field.get("type", "text"))}" autocomplete="off" placeholder="type answer">
              {helper_buttons}"""


def render_answer_helpers(helpers):
    if not helpers:
        return ""
    buttons = "".join(
        f'<button type="button" data-answer-helper="{escape(str(helper))}">{escape(str(helper))}</button>'
        for helper in helpers
    )
    return f'<div class="answer-helper-row">{buttons}</div>'


def render_feedback(context):
    return f"""        <div class="feedback {escape(context["feedback_type"])}">{escape(context["feedback"])}</div>"""


def render_help_stack(context):
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]

    return f"""        <div class="help-stack">
          {f'<div class="help-box hint-box">{escape(problem.hint)}</div>' if hint_visible else ''}
          {f'<div class="help-box solution-box">{escape(problem.solution)} Answer: {escape(problem.answer)}</div>' if solution_visible else ''}
        </div>"""


def render_stats(context):
    return f"""        <div class="stats-panel" aria-label="Practice stats">
          <span class="stat-correct">Correct: {context["correct_count"]}</span>
          <span class="stat-hints">Hints: {context["hint_count"]}</span>
          <span class="stat-incorrect">Incorrect: {context["incorrect_count"]}</span>
          <span class="stat-skips">Skips: {context["skip_count"]}</span>
        </div>"""


def render_problem_panel(context, unit_label, topic_label):
    unit = context["unit"]
    topic = context["topic"]
    difficulty = context["difficulty"]
    problem = context["problem"]
    answer_form = render_answer_form(context)
    feedback = render_feedback(context)
    help_stack = render_help_stack(context)
    stats = render_stats(context)

    return f"""      <section class="problem-panel" aria-live="polite">
        <div class="badges">
          <span>Algebra 2</span>
          <span data-badge="unit">{escape(unit_label(unit))}</span>
          <span data-badge="topic">{escape(topic_label(topic))}</span>
          <span data-badge="difficulty">{escape(difficulty.title())}</span>
        </div>

        <h1>{render_problem_display(problem)}</h1>

{answer_form}

{feedback}
{help_stack}
{stats}
      </section>"""


def render_page(state, units, difficulties, generators, unit_label, topic_label, valid_topic_for_unit, count_value):
    context = page_context(state, units, difficulties, generators, valid_topic_for_unit, count_value)
    control_panel = render_control_panel(context, units, difficulties)
    problem_panel = render_problem_panel(context, unit_label, topic_label)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MathPracAI</title>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js" defer></script>
</head>
<body>
  <main class="app-frame">
    <section class="generator">
{control_panel}

{problem_panel}
    </section>
  </main>
</body>
</html>"""
