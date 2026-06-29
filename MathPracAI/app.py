from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from generators import GENERATORS
from models import problem_from_form
from renderers import render_page
from validators import answers_match_problem


ROOT = Path(__file__).parent
PORT = int(os.environ.get("PORT", "8010"))

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


def render_app_page(state):
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


def parse_post(handler):
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length).decode("utf-8")
    return {key: values[0] for key, values in parse_qs(body).items()}


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

        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
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
        }

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
    server = ThreadingHTTPServer(("localhost", PORT), MathPracHandler)
    print(f"MathPracAI running at http://localhost:{PORT}")
    server.serve_forever()
