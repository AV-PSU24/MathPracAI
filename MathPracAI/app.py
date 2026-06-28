from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from random import randint
from urllib.parse import parse_qs, urlparse


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


@dataclass
class Problem:
    question: str
    answer: str
    hint: str
    solution: str


def random_range(difficulty, ranges):
    low, high = ranges[difficulty]
    return randint(low, high)


def signed(value):
    return f"- {abs(value)}" if value < 0 else f"+ {value}"


def compact_signed(value):
    return f"-{abs(value)}" if value < 0 else f"+{value}"


def complex_value(real, imaginary):
    return f"{real}{compact_signed(imaginary)}i"


def create_problem(question, answer, hint, solution):
    return Problem(question, str(answer), hint, solution)


def evaluating_functions(difficulty):
    a = randint(1, 4 if difficulty == "easy" else 7)
    b = randint(-6, 8)
    c = randint(-10, 10)
    x = randint(-4 if difficulty != "easy" else 1, 6 if difficulty == "easy" else 8)
    value = a * x * x + b * x + c
    return create_problem(
        f"Evaluate f({x}) if f(x) = {a}x^2 {signed(b)}x {signed(c)}.",
        value,
        "Substitute the input value anywhere x appears.",
        f"f({x}) = {a}({x})^2 {signed(b)}({x}) {signed(c)} = {value}.",
    )


def domain_and_range(difficulty):
    start = randint(-8, 4)
    return create_problem(
        f"State the domain of f(x) = sqrt(x {signed(-start)}). Use x>=a format.",
        f"x>={start}",
        "For a square root, the expression inside the radical must be greater than or equal to 0.",
        f"x {signed(-start)} >= 0, so x >= {start}.",
    )


def intercepts(difficulty):
    m = randint(1, 8 if difficulty == "hard" else 5)
    x_intercept = randint(-6, 6)
    b = -m * x_intercept
    return create_problem(
        f"Find the x-intercept of y = {m}x {signed(b)}. Enter the x-value only.",
        x_intercept,
        "Set y equal to 0 and solve for x.",
        f"0 = {m}x {signed(b)}, so {m}x = {-b} and x = {x_intercept}.",
    )


def increasing_decreasing(difficulty):
    slope = randint(1, 9)
    if randint(0, 1):
        slope *= -1
    direction = "increasing" if slope > 0 else "decreasing"
    return create_problem(
        f"Is f(x) = {slope}x {signed(randint(-8, 8))} increasing or decreasing?",
        direction,
        "A linear function increases when its slope is positive and decreases when its slope is negative.",
        f"The slope is {slope}, so the function is {direction}.",
    )


def parent_functions(difficulty):
    choices = [
        ("y = (x - 3)^2 + 4", "quadratic"),
        ("y = |x + 2| - 5", "absolute value"),
        ("y = sqrt(x - 1)", "square root"),
        ("y = 2^(x - 4)", "exponential"),
    ]
    equation, answer = choices[randint(0, len(choices) - 1)]
    return create_problem(
        f"Identify the parent function family for {equation}.",
        answer,
        "Ignore shifts, stretches, and reflections. Focus on the core shape.",
        f"The core function family is {answer}.",
    )


def transformations(difficulty):
    right = randint(1, 7)
    up = randint(-6, 6)
    return create_problem(
        f"For g(x) = (x - {right})^2 {signed(up)}, describe the translation from f(x)=x^2. Use: right a, up b",
        f"right {right}, up {up}",
        "Inside the parentheses controls horizontal movement. The outside constant controls vertical movement.",
        f"x - {right} shifts right {right}; {signed(up)} shifts vertically to up {up}.",
    )


def piecewise_functions(difficulty):
    split = randint(-2, 3)
    x = randint(split + 1, split + (4 if difficulty == "easy" else 8))
    a = randint(2, 6)
    b = randint(-5, 5)
    value = a * x + b
    return create_problem(
        f"Given f(x)=x^2 for x <= {split}, and f(x)={a}x {signed(b)} for x > {split}, find f({x}).",
        value,
        f"Since {x} is greater than {split}, use the second rule.",
        f"f({x}) = {a}({x}) {signed(b)} = {value}.",
    )


def average_rate_of_change(difficulty):
    a = randint(1, 4 if difficulty == "easy" else 7)
    start = randint(-3, 3)
    end = start + randint(2, 6)
    f_start = a * start * start
    f_end = a * end * end
    answer = (f_end - f_start) // (end - start)
    return create_problem(
        f"Find the average rate of change of f(x)={a}x^2 from x={start} to x={end}.",
        answer,
        "Use [f(b)-f(a)] / [b-a].",
        f"[f({end}) - f({start})] / [{end} - {start}] = [{f_end} - {f_start}] / {end - start} = {answer}.",
    )


def composition_of_functions(difficulty):
    a = randint(2, 6)
    b = randint(-5, 5)
    c = randint(2, 5)
    d = randint(-5, 5)
    x = randint(1, 6 if difficulty == "easy" else 10)
    gx = c * x + d
    answer = a * gx + b
    return create_problem(
        f"If f(x)={a}x {signed(b)} and g(x)={c}x {signed(d)}, find f(g({x})).",
        answer,
        "Evaluate the inside function first, then plug that result into the outside function.",
        f"g({x}) = {gx}. Then f({gx}) = {a}({gx}) {signed(b)} = {answer}.",
    )


def inverse_functions(difficulty):
    a = randint(2, 8)
    b = randint(-10, 10)
    x = randint(1, 9)
    y = a * x + b
    return create_problem(
        f"If f(x) = {a}x {signed(b)}, find f^-1({y}).",
        x,
        "An inverse reverses the output back to the original input.",
        f"Set {y} = {a}x {signed(b)}. Then {a}x = {y - b}, so x = {x}.",
    )


GENERATORS = {
    "evaluating_functions": evaluating_functions,
    "domain_and_range": domain_and_range,
    "intercepts": intercepts,
    "increasing_decreasing": increasing_decreasing,
    "parent_functions": parent_functions,
    "transformations": transformations,
    "piecewise_functions": piecewise_functions,
    "average_rate_of_change": average_rate_of_change,
    "composition_of_functions": composition_of_functions,
    "inverse_functions": inverse_functions,
}


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


def normalize(value):
    return "".join(str(value).lower().split())


def count_value(state, key):
    try:
        return max(0, int(state.get(key, "0")))
    except ValueError:
        return 0


def answers_match(user_answer, correct_answer):
    user = normalize(user_answer)
    correct = normalize(correct_answer)

    if user == correct:
        return True

    try:
        return abs(float(user) - float(correct)) < 0.001
    except ValueError:
        pass

    if "," in correct:
        return sorted(user.split(",")) == sorted(correct.split(","))

    return False


def select_options(options, selected):
    html = []
    for value, label in options:
        selected_attr = " selected" if value == selected else ""
        html.append(f'<option value="{escape(value)}"{selected_attr}>{escape(label)}</option>')
    return "\n".join(html)


def custom_dropdown(name, label, options, selected):
    selected_label = next((option_label for value, option_label in options if value == selected), options[0][1])
    option_markup = []
    for index, (value, option_label) in enumerate(options):
        is_selected = value == selected
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


def render_page(state):
    unit = state.get("unit", "unit1")
    if unit not in UNITS:
        unit = "unit1"

    difficulty = state.get("difficulty", "easy")
    if difficulty not in DIFFICULTIES:
        difficulty = "easy"

    topic = state.get("topic") or UNITS[unit]["topics"][0][0]
    if not valid_topic_for_unit(unit, topic):
        topic = UNITS[unit]["topics"][0][0]

    problem = state.get("problem")
    feedback = state.get("feedback", "")
    feedback_type = state.get("feedback_type", "empty")
    hint_visible = state.get("hint_visible", "") == "true"
    solution_visible = state.get("solution_visible", "") == "true"
    answered = state.get("answered", "") == "true"
    answer_value = state.get("answer", "")
    correct_count = count_value(state, "correct_count")
    hint_count = count_value(state, "hint_count")
    incorrect_count = count_value(state, "incorrect_count")
    skip_count = count_value(state, "skip_count")
    generated = state.get("generated", "") == "true"
    hint_disabled = " disabled" if hint_visible or solution_visible or answered else ""
    solution_disabled = " disabled" if solution_visible or answered else ""
    check_disabled = " disabled" if solution_visible else ""
    next_disabled = "" if answered or solution_visible else " disabled"
    generate_disabled = " disabled" if generated else ""

    if problem is None:
        problem = GENERATORS[topic](difficulty)
    if not answer_value:
        answer_value = problem.answer

    unit_options = tuple((value, data["label"]) for value, data in UNITS.items())
    topic_options = tuple(UNITS[unit]["topics"])
    difficulty_options = tuple((item, item.title()) for item in DIFFICULTIES)
    unit_dropdown = custom_dropdown("unit", "Unit", unit_options, unit)
    topic_dropdown = custom_dropdown("topic", "Topic", topic_options, topic)
    difficulty_dropdown = custom_dropdown("difficulty", "Difficulty", difficulty_options, difficulty)

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
      <form class="control-panel" action="/generate" method="get">
        <div class="panel-title">
          <span>MathPrac AI</span>
        </div>
        <input type="hidden" name="correct_count" value="{correct_count}">
        <input type="hidden" name="hint_count" value="{hint_count}">
        <input type="hidden" name="incorrect_count" value="{incorrect_count}">
        <input type="hidden" name="skip_count" value="{skip_count}">
        {unit_dropdown}
        {topic_dropdown}
        {difficulty_dropdown}
        <button type="submit" data-generate-button{generate_disabled}>Generate Practice Problems</button>
      </form>

      <section class="problem-panel" aria-live="polite">
        <div class="badges">
          <span>Algebra 2</span>
          <span data-badge="unit">{escape(unit_label(unit))}</span>
          <span data-badge="topic">{escape(topic_label(topic))}</span>
          <span data-badge="difficulty">{escape(difficulty.title())}</span>
        </div>

        <h1>{escape(problem.question)}</h1>

        <form class="answer-panel" action="/check" method="post">
          <input type="hidden" name="unit" value="{escape(unit)}">
          <input type="hidden" name="topic" value="{escape(topic)}">
          <input type="hidden" name="difficulty" value="{escape(difficulty)}">
          <input type="hidden" name="question" value="{escape(problem.question)}">
          <input type="hidden" name="answer" value="{escape(answer_value)}">
          <input type="hidden" name="hint" value="{escape(problem.hint)}">
          <input type="hidden" name="solution" value="{escape(problem.solution)}">
          <input type="hidden" name="hint_visible" value="{str(hint_visible).lower()}">
          <input type="hidden" name="solution_visible" value="{str(solution_visible).lower()}">
          <input type="hidden" name="answered" value="{str(answered).lower()}">
          <input type="hidden" name="correct_count" value="{correct_count}">
          <input type="hidden" name="hint_count" value="{hint_count}">
          <input type="hidden" name="incorrect_count" value="{incorrect_count}">
          <input type="hidden" name="skip_count" value="{skip_count}">
          <input type="hidden" name="generated" value="{str(generated).lower()}">
          <label for="user_answer">answer_input</label>
          <div class="answer-row">
            <input id="user_answer" name="user_answer" type="text" autocomplete="off" placeholder="type answer">
            <button name="action" value="check" type="submit"{check_disabled}>Check</button>
          </div>
          <div class="utility-row">
            <button name="action" value="hint" type="submit"{hint_disabled}>Hint</button>
            <button name="action" value="skip" type="submit">Skip</button>
            <button name="action" value="solution" type="submit"{solution_disabled}>Solution</button>
            <button name="action" value="next" type="submit"{next_disabled}>Next Problem</button>
          </div>
        </form>

        <div class="feedback {escape(feedback_type)}">{escape(feedback)}</div>
        <div class="help-stack">
          {f'<div class="help-box hint-box">{escape(problem.hint)}</div>' if hint_visible else ''}
          {f'<div class="help-box solution-box">{escape(problem.solution)} Answer: {escape(problem.answer)}</div>' if solution_visible else ''}
        </div>
        <div class="stats-panel" aria-label="Practice stats">
          <span class="stat-correct">Correct: {correct_count}</span>
          <span class="stat-hints">Hints: {hint_count}</span>
          <span class="stat-incorrect">Incorrect: {incorrect_count}</span>
          <span class="stat-skips">Skips: {skip_count}</span>
        </div>
      </section>
    </section>
  </main>
</body>
</html>"""


def parse_post(handler):
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length).decode("utf-8")
    return {key: values[0] for key, values in parse_qs(body).items()}


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
            self.respond(render_page(query))
            return

        self.send_error(404)

    def do_POST(self):
        if self.path != "/check":
            self.send_error(404)
            return

        data = parse_post(self)
        problem = Problem(
            data.get("question", ""),
            data.get("answer", ""),
            data.get("hint", ""),
            data.get("solution", ""),
        )
        action = data.get("action", "check")
        user_answer = data.get("user_answer", "")
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
        elif answers_match(user_answer, problem.answer):
            state["feedback"] = "Correct."
            state["feedback_type"] = "correct"
            state["correct_count"] = str(count_value(state, "correct_count") + 1)
            state["answered"] = "true"
        else:
            state["feedback"] = "Not quite. Try again or open the hint."
            state["feedback_type"] = "incorrect"
            state["incorrect_count"] = str(count_value(state, "incorrect_count") + 1)
            state["answered"] = "true"

        self.respond(render_page(state))

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
