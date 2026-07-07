from random import choice
import json

from flask import Blueprint, redirect, request, url_for

from firebase_backend.auth_service import current_user_profile, require_login
from firebase_backend.firestore_service import record_completed_test_result
from math_engine.generators import GENERATORS
from math_engine.models import problem_from_form
from math_engine.renderers import (
    default_question_view_values,
    render_page,
    selected_topic_config_values,
    topic_config_field_names,
    valid_question_view_values,
)
from math_engine.validators import answers_match_problem


practice_bp = Blueprint("practice", __name__)

UNITS = {
    "unit1": {
        "label": "Unit 1: Functions and Graphs",
        "topics": [
            ("evaluating_functions", "Evaluating functions"),
            ("domain_and_range", "Domain and range"),
            ("parent_functions", "Parent functions"),
        ],
    }
}

DEFAULT_GENERATION_DIFFICULTY = "easy"


def topic_label(topic):
    for unit in UNITS.values():
        for value, label in unit["topics"]:
            if value == topic:
                return label
    return "Evaluating functions"


def unit_label(unit):
    return UNITS.get(unit, UNITS["unit1"])["label"]


def valid_topic_for_unit(unit, topic):
    return topic in {value for value, _label in UNITS[unit]["topics"]}


def count_value(state, key):
    try:
        return max(0, int(state.get(key, "0")))
    except ValueError:
        return 0


def problem_already_counted(state):
    return state.get("problem_counted") == "true"


def count_problem_once(state, outcome):
    if problem_already_counted(state):
        return
    if outcome == "solved":
        state["solved_count"] = str(count_value(state, "solved_count") + 1)
    elif outcome == "hint":
        state["hint_count"] = str(count_value(state, "hint_count") + 1)
    elif outcome == "skipped":
        state["skip_count"] = str(count_value(state, "skip_count") + 1)
    state["problem_counted"] = "true"


def mark_help_status(state, status):
    current = state.get("problem_help_status", "none")
    if current == "solution" and status == "hint":
        return
    state["problem_help_status"] = status


def outcome_for_correct_submission(state):
    if state.get("problem_help_status") == "hint":
        return "hint"
    if state.get("problem_help_status") == "solution":
        return "solved"
    return "solved"


def question_view_field(view):
    return f"question_view_{view}"


def selected_question_views(state, topic):
    valid_views = valid_question_view_values(topic)
    has_view_fields = any(question_view_field(view) in state for view in valid_views)
    if not has_view_fields:
        return default_question_view_values(topic)

    selected = tuple(view for view in valid_views if state.get(question_view_field(view)) == "true")
    return selected or valid_views[:1]


def apply_question_view_state(state, choose_new_active=False):
    topic = state["topic"] if state.get("topic") in GENERATORS else "evaluating_functions"
    selected = selected_question_views(state, topic)
    for view in ("equation", "graph", "table"):
        state[question_view_field(view)] = "true" if view in selected else ""

    active_view = state.get("active_question_view")
    if choose_new_active or active_view not in selected:
        active_view = choice(selected)
    state["active_question_view"] = active_view


def generation_options(state):
    topic = state["topic"] if state.get("topic") in GENERATORS else "evaluating_functions"
    topic_config = selected_topic_config_values(state, topic)
    question_views = selected_question_views(state, topic)
    presentation = state.get("active_question_view")
    if presentation not in question_views:
        presentation = question_views[0]
    return {
        "topic_config": topic_config,
        "questionViews": (presentation,),
    }


def generate_problem(topic, state):
    return GENERATORS[topic](DEFAULT_GENERATION_DIFFICULTY, generation_options(state))


def reset_for_new_problem(state):
    unit = state["unit"] if state["unit"] in UNITS else "unit1"
    topic = state["topic"] if valid_topic_for_unit(unit, state["topic"]) else UNITS[unit]["topics"][0][0]

    state["unit"] = unit
    state["topic"] = topic
    apply_question_view_state(state, choose_new_active=True)
    next_problem = generate_problem(topic, state)
    state["problem"] = next_problem
    state["answer"] = next_problem.answer
    state["hint_visible"] = ""
    state["solution_visible"] = ""
    state["answered"] = ""
    state["problem_counted"] = ""
    state["problem_help_status"] = "none"
    state["feedback"] = ""
    state["feedback_type"] = "empty"


def render_app_page(state):
    apply_question_view_state(state)
    state["auth_user"] = current_user_profile()
    return render_page(
        state,
        UNITS,
        GENERATORS,
        unit_label,
        topic_label,
        valid_topic_for_unit,
        count_value,
    )


def request_values_from_parsed(parsed_values):
    config_fields = set(topic_config_field_names())
    data = {}
    for key in parsed_values:
        values = parsed_values.getlist(key)
        if key in config_fields or key == "test_topics":
            data[key] = tuple(values)
        else:
            data[key] = values[0] if values else ""
    return data


def parse_query():
    return request_values_from_parsed(request.args)


def parse_post():
    return request_values_from_parsed(request.form)


def user_answer_from_form(data, problem):
    fields = problem.answer_fields or []
    if len(fields) <= 1:
        return data.get("user_answer", "")
    return {field.get("name", ""): data.get(field.get("name", ""), "") for field in fields}


def add_ui_state(state, data):
    state["ui_mode"] = data.get("ui_mode", "practice")
    state["test_total"] = data.get("test_total", "10")
    state["test_index"] = data.get("test_index", "1")
    state["test_correct"] = data.get("test_correct", "0")
    state["test_incorrect"] = data.get("test_incorrect", "0")
    state["test_skipped"] = data.get("test_skipped", "0")
    state["test_hints"] = data.get("test_hints", "0")
    state["test_elapsed"] = data.get("test_elapsed", "0")
    state["test_timer_mode"] = data.get("test_timer_mode", "stopwatch")
    state["test_time_limit"] = data.get("test_time_limit", "30")
    test_topics = data.get("test_topics", ())
    if isinstance(test_topics, str):
        test_topics = (test_topics,)
    state["test_topics"] = tuple(test_topics)
    state["test_breakdown"] = data.get("test_breakdown", "{}")


def test_topic_values(state):
    topics = state.get("test_topics", ())
    if isinstance(topics, str):
        topics = (topics,)
    return tuple(value for value in topics if "|" in value)


def apply_test_topic_for_index(state):
    topics = test_topic_values(state)
    if not topics:
        return
    index = max(1, count_value(state, "test_index")) - 1
    unit, topic = topics[index % len(topics)].split("|", 1)
    if unit in UNITS and valid_topic_for_unit(unit, topic):
        state["unit"] = unit
        state["topic"] = topic


def decoded_breakdown(state):
    try:
        value = json.loads(state.get("test_breakdown", "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        value = {}
    return value if isinstance(value, dict) else {}


def add_breakdown_result(state, result):
    breakdown = decoded_breakdown(state)
    key = f'{state.get("unit", "unit1")}|{state.get("topic", "evaluating_functions")}'
    row = breakdown.get(key) if isinstance(breakdown.get(key), dict) else {}
    row["correct"] = int(row.get("correct", 0)) + (1 if result == "correct" else 0)
    row["incorrect"] = int(row.get("incorrect", 0)) + (1 if result == "incorrect" else 0)
    row["skipped"] = int(row.get("skipped", 0)) + (1 if result == "skipped" else 0)
    breakdown[key] = row
    state["test_breakdown"] = json.dumps(breakdown, separators=(",", ":"))


def test_is_complete(state):
    return count_value(state, "test_index") >= max(1, count_value(state, "test_total"))


def next_test_problem(state):
    if test_is_complete(state):
        state["ui_mode"] = "test_results"
        state["answered"] = "true"
        return
    state["test_index"] = str(count_value(state, "test_index") + 1)
    apply_test_topic_for_index(state)
    reset_for_new_problem(state)
    state["ui_mode"] = "test_progress"
    state["generated"] = "true"


def persist_completed_test_if_needed(state):
    if state.get("ui_mode") != "test_results":
        return
    user = current_user_profile()
    if not user or user.get("role") != "student":
        return
    total = max(count_value(state, "test_total"), 1)
    correct = count_value(state, "test_correct")
    result_json = {
        "breakdown": decoded_breakdown(state),
        "elapsedSeconds": count_value(state, "test_elapsed"),
        "timerMode": state.get("test_timer_mode", "stopwatch"),
        "topics": list(test_topic_values(state)),
    }
    try:
        record_completed_test_result(
            student_id=user["uid"],
            tutor_id=user.get("tutorId"),
            score=round((correct / total) * 100),
            total_questions=total,
            correct_count=correct,
            topic=", ".join(test_topic_values(state)) or state.get("topic", ""),
            result_json=result_json,
        )
    except Exception:
        return


@practice_bp.get("/")
@require_login
def index():
    user = current_user_profile()
    if user and user.get("role") in ("tutor", "admin"):
        return redirect(url_for("dashboard.dashboard"))
    return render_app_page(parse_query())


@practice_bp.get("/generate")
@require_login
def generate():
    query = parse_query()
    unit = query.get("unit", "unit1")
    topic = query.get("topic", "")
    if unit not in UNITS:
        unit = "unit1"
    if not valid_topic_for_unit(unit, topic):
        topic = UNITS[unit]["topics"][0][0]
    query["unit"] = unit
    query["topic"] = topic
    add_ui_state(query, query)
    apply_question_view_state(query, choose_new_active=True)
    query["problem"] = generate_problem(topic, query)
    query["feedback"] = ""
    query["feedback_type"] = "empty"
    query["hint_visible"] = ""
    query["solution_visible"] = ""
    query["answered"] = ""
    query["problem_counted"] = ""
    query["problem_help_status"] = "none"
    query["generated"] = "true"
    return render_app_page(query)


@practice_bp.post("/check")
@require_login
def check():
    data = parse_post()
    problem = problem_from_form(data)
    action = data.get("action", "check")
    user_answer = user_answer_from_form(data, problem)
    state = {
        "unit": data.get("unit", "unit1"),
        "topic": data.get("topic", "evaluating_functions"),
        "problem": problem,
        "answer": problem.answer,
        "hint_visible": data.get("hint_visible", ""),
        "solution_visible": data.get("solution_visible", ""),
        "answered": data.get("answered", ""),
        "solved_count": data.get("solved_count", "0"),
        "hint_count": data.get("hint_count", "0"),
        "skip_count": data.get("skip_count", "0"),
        "problem_counted": data.get("problem_counted", ""),
        "problem_help_status": data.get("problem_help_status", "none"),
        "generated": data.get("generated", "true"),
        "question_view_equation": data.get("question_view_equation", ""),
        "question_view_graph": data.get("question_view_graph", ""),
        "active_question_view": data.get("active_question_view", ""),
    }
    add_ui_state(state, data)
    for field_name in topic_config_field_names():
        if field_name in data:
            state[field_name] = data[field_name]

    if action == "hint":
        state["feedback"] = ""
        state["feedback_type"] = "empty"
        state["hint_visible"] = "true"
        mark_help_status(state, "hint")
        count_problem_once(state, "hint")
        if state.get("ui_mode") == "test_progress":
            state["test_hints"] = str(count_value(state, "test_hints") + 1)
    elif action == "solution":
        state["feedback"] = ""
        state["feedback_type"] = "empty"
        state["solution_visible"] = "true"
        state["answered"] = "true"
        mark_help_status(state, "solution")
        count_problem_once(state, "solved")
    elif action == "next":
        if state.get("ui_mode") == "test_progress":
            next_test_problem(state)
        else:
            reset_for_new_problem(state)
            state["generated"] = "true"
    elif action == "skip":
        if state.get("ui_mode") == "test_progress":
            state["test_skipped"] = str(count_value(state, "test_skipped") + 1)
            add_breakdown_result(state, "skipped")
            next_test_problem(state)
        else:
            mark_help_status(state, "skipped")
            count_problem_once(state, "skipped")
            reset_for_new_problem(state)
            state["generated"] = "true"
    elif answers_match_problem(user_answer, problem):
        state["feedback"] = "Correct."
        state["feedback_type"] = "correct"
        count_problem_once(state, outcome_for_correct_submission(state))
        state["answered"] = "true"
        if state.get("ui_mode") == "test_progress":
            state["test_correct"] = str(count_value(state, "test_correct") + 1)
            add_breakdown_result(state, "correct")
    else:
        state["feedback"] = "Not quite. Try again or open the hint."
        state["feedback_type"] = "incorrect"
        state["answered"] = "true"
        if state.get("ui_mode") == "test_progress":
            state["test_incorrect"] = str(count_value(state, "test_incorrect") + 1)
            add_breakdown_result(state, "incorrect")

    persist_completed_test_if_needed(state)
    return render_app_page(state)
