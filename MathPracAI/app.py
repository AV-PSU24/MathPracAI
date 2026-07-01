from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import errno
from pathlib import Path
from random import choice
from urllib.parse import parse_qs, urlparse

from generators import GENERATORS
from models import problem_from_form
from renderers import (
    default_question_view_values,
    render_page,
    topic_config_field_names,
    valid_question_view_values,
)
from validators import answers_match_problem


ROOT = Path(__file__).parent
PORT = 8010

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

DIFFICULTIES = ("easy", "medium", "hard")


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


def reset_for_new_problem(state):
    unit = state["unit"] if state["unit"] in UNITS else "unit1"
    topic = state["topic"] if valid_topic_for_unit(unit, state["topic"]) else UNITS[unit]["topics"][0][0]
    difficulty = state["difficulty"] if state["difficulty"] in DIFFICULTIES else "easy"
    next_problem = GENERATORS[topic](difficulty)

    state["unit"] = unit
    state["topic"] = topic
    state["difficulty"] = difficulty
    state["problem"] = next_problem
    state["answer"] = next_problem.answer
    state["hint_visible"] = ""
    state["solution_visible"] = ""
    state["answered"] = ""
    state["feedback"] = ""
    state["feedback_type"] = "empty"
    apply_question_view_state(state, choose_new_active=True)


def render_app_page(state):
    apply_question_view_state(state)
    return render_page(
        state,
        UNITS,
        DIFFICULTIES,
        GENERATORS,
        unit_label,
        topic_label,
        valid_topic_for_unit,
        count_value,
    )


def request_values_from_parsed(parsed_values):
    config_fields = set(topic_config_field_names())
    data = {}
    for key, values in parsed_values.items():
        if key in config_fields:
            data[key] = tuple(values)
        else:
            data[key] = values[0]
    return data


def parse_query(query_string):
    return request_values_from_parsed(parse_qs(query_string))


def parse_post(handler):
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length).decode("utf-8")
    return request_values_from_parsed(parse_qs(body))


def user_answer_from_form(data, problem):
    fields = problem.answer_fields or []
    if len(fields) <= 1:
        return data.get("user_answer", "")
    return {field.get("name", ""): data.get(field.get("name", ""), "") for field in fields}


class MathPracHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/styles.css":
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.end_headers()
            self.wfile.write((ROOT / "styles.css").read_bytes())
            return

        if parsed.path == "/script.js":
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.end_headers()
            self.wfile.write((ROOT / "script.js").read_bytes())
            return

        query = parse_query(parsed.query)
        if parsed.path in ("/", "/generate"):
            if parsed.path == "/generate":
                unit = query.get("unit", "unit1")
                difficulty = query.get("difficulty", "easy")
                topic = query.get("topic", "")
                if unit not in UNITS:
                    unit = "unit1"
                if difficulty not in DIFFICULTIES:
                    difficulty = "easy"
                if not valid_topic_for_unit(unit, topic):
                    topic = UNITS[unit]["topics"][0][0]
                query["unit"] = unit
                query["topic"] = topic
                query["difficulty"] = difficulty
                query["problem"] = GENERATORS[topic](difficulty)
                query["feedback"] = ""
                query["feedback_type"] = "empty"
                query["hint_visible"] = ""
                query["solution_visible"] = ""
                query["answered"] = ""
                query["generated"] = "true"
                apply_question_view_state(query, choose_new_active=True)
            self.respond(render_app_page(query))
            return

        self.send_error(404)

    def do_POST(self):
        if self.path != "/check":
            self.send_error(404)
            return

        data = parse_post(self)
        problem = problem_from_form(data)
        action = data.get("action", "check")
        user_answer = user_answer_from_form(data, problem)
        state = {
            "unit": data.get("unit", "unit1"),
            "topic": data.get("topic", "evaluating_functions"),
            "difficulty": data.get("difficulty", "easy"),
            "problem": problem,
            "answer": problem.answer,
            "hint_visible": data.get("hint_visible", ""),
            "solution_visible": data.get("solution_visible", ""),
            "answered": data.get("answered", ""),
            "correct_count": data.get("correct_count", "0"),
            "hint_count": data.get("hint_count", "0"),
            "incorrect_count": data.get("incorrect_count", "0"),
            "skip_count": data.get("skip_count", "0"),
            "generated": data.get("generated", "true"),
            "question_view_equation": data.get("question_view_equation", ""),
            "question_view_graph": data.get("question_view_graph", ""),
            "active_question_view": data.get("active_question_view", ""),
        }
        for field_name in topic_config_field_names():
            if field_name in data:
                state[field_name] = data[field_name]

        if action == "hint":
            state["feedback"] = ""
            state["feedback_type"] = "empty"
            state["hint_visible"] = "true"
            state["hint_count"] = str(count_value(state, "hint_count") + 1)
        elif action == "solution":
            state["feedback"] = ""
            state["feedback_type"] = "empty"
            state["solution_visible"] = "true"
            state["answered"] = "true"
        elif action == "next":
            reset_for_new_problem(state)
            state["generated"] = "true"
        elif action == "skip":
            state["skip_count"] = str(count_value(state, "skip_count") + 1)
            reset_for_new_problem(state)
            state["generated"] = "true"
        elif answers_match_problem(user_answer, problem):
            state["feedback"] = "Correct."
            state["feedback_type"] = "correct"
            state["correct_count"] = str(count_value(state, "correct_count") + 1)
            state["answered"] = "true"
        else:
            state["feedback"] = "Not quite. Try again or open the hint."
            state["feedback_type"] = "incorrect"
            state["incorrect_count"] = str(count_value(state, "incorrect_count") + 1)
            state["answered"] = "true"

        self.respond(render_app_page(state))

    def respond(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    try:
        server = ThreadingHTTPServer(("localhost", PORT), MathPracHandler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            print(
                "Error: another server is already running on port 8010. Stop it or kill the process, then run python3 app.py again.",
                flush=True,
            )
            raise SystemExit(1)
        raise

    print("Local server running at http://localhost:8010/", flush=True)
    server.serve_forever()
