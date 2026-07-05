from dataclasses import dataclass, field
from html import escape
import json


DEFAULT_GRAPH_CONFIG = {
    "enabled": False,
    "type": "none",
    "equation": "",
    "x_min": -10,
    "x_max": 10,
    "y_min": -10,
    "y_max": 10,
    "points": [],
    "features": {},
}


def no_graph_config():
    config = DEFAULT_GRAPH_CONFIG.copy()
    config["points"] = list(DEFAULT_GRAPH_CONFIG["points"])
    config["features"] = dict(DEFAULT_GRAPH_CONFIG["features"])
    return config


def json_serializable(value, fallback):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return fallback


def graph_bound(value, fallback):
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return int(number) if number.is_integer() else number


def function_graph_config(
    equation,
    x_min=-10,
    x_max=10,
    y_min=-10,
    y_max=10,
    points=None,
    features=None,
):
    config = no_graph_config()
    config.update(
        {
            "enabled": True,
            "type": "function",
            "equation": str(equation),
            "x_min": graph_bound(x_min, DEFAULT_GRAPH_CONFIG["x_min"]),
            "x_max": graph_bound(x_max, DEFAULT_GRAPH_CONFIG["x_max"]),
            "y_min": graph_bound(y_min, DEFAULT_GRAPH_CONFIG["y_min"]),
            "y_max": graph_bound(y_max, DEFAULT_GRAPH_CONFIG["y_max"]),
            "points": json_serializable(points, []) if isinstance(points, list) else [],
            "features": json_serializable(features, {}) if isinstance(features, dict) else {},
        }
    )
    return config


def normalized_graph_config(value):
    if not isinstance(value, dict) or not value.get("enabled"):
        return no_graph_config()

    config = function_graph_config(
        value.get("equation", ""),
        value.get("x_min", -10),
        value.get("x_max", 10),
        value.get("y_min", -10),
        value.get("y_max", 10),
        value.get("points", []),
        value.get("features", {}),
    )
    config["type"] = str(value.get("type") or "function")
    return config


@dataclass
class Problem:
    topic: str
    problem_type: str
    difficulty: str
    display_equation: str
    prompt: str
    answer_fields: list[dict] = field(default_factory=list)
    correct_answer: str = ""
    acceptable_answers: list[str] = field(default_factory=list)
    hint: str = ""
    solution: str = ""
    metadata: dict = field(default_factory=dict)
    assets: list[dict] = field(default_factory=list)
    graph_config: dict = field(default_factory=no_graph_config)

    def __post_init__(self):
        self.graph_config = normalized_graph_config(self.graph_config)

    @property
    def question(self):
        return "\n\n".join(part for part in (self.display_equation, self.prompt) if part)

    @property
    def answer(self):
        return self.correct_answer

    def to_dict(self):
        return {
            "topic": self.topic,
            "problem_type": self.problem_type,
            "difficulty": self.difficulty,
            "display_equation": self.display_equation,
            "prompt": self.prompt,
            "answer_fields": self.answer_fields,
            "correct_answer": self.correct_answer,
            "acceptable_answers": self.acceptable_answers,
            "hint": self.hint,
            "solution": self.solution,
            "metadata": self.metadata,
            "assets": self.assets,
            "graph_config": self.graph_config,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            data = {}

        def text_field(name):
            value = data.get(name, "")
            return "" if value is None else str(value)

        correct_answer = text_field("correct_answer")
        acceptable_answers = data.get("acceptable_answers") or [correct_answer]
        if not isinstance(acceptable_answers, list):
            acceptable_answers = [acceptable_answers]
        answer_fields = data.get("answer_fields")
        if not isinstance(answer_fields, list):
            answer_fields = [{"name": "answer", "label": "Answer", "type": "text"}]
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        assets = data.get("assets")
        if not isinstance(assets, list):
            assets = []
        graph_config = normalized_graph_config(data.get("graph_config"))

        return cls(
            topic=text_field("topic"),
            problem_type=text_field("problem_type"),
            difficulty=text_field("difficulty"),
            display_equation=text_field("display_equation"),
            prompt=text_field("prompt"),
            answer_fields=answer_fields,
            correct_answer=correct_answer,
            acceptable_answers=[str(answer) for answer in acceptable_answers],
            hint=text_field("hint"),
            solution=text_field("solution"),
            metadata=metadata,
            assets=assets,
            graph_config=graph_config,
        )


def encoded_json(value):
    return escape(json.dumps(value))


def encoded_problem(problem):
    return encoded_json(problem.to_dict())


def decoded_json(value, fallback):
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def problem_from_form(data):
    return Problem.from_dict(decoded_json(data.get("problem_json"), {}))
