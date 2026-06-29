from dataclasses import dataclass
from random import randint

from formatters import (
    format_absolute_value_equation,
    format_function_equation,
    format_function_substitution,
    format_linear_equation,
    format_quadratic_vertex_equation,
    format_square_root_equation,
)
from models import Problem


@dataclass(frozen=True)
class EvaluatingFunctionsProblemType:
    topic: str = "evaluating_functions"
    problem_type: str = "evaluate_function"
    supported_families: tuple[str, ...] = ("linear", "quadratic", "polynomial")

    def degree_for(self, difficulty):
        if difficulty == "easy":
            return randint(1, 2)
        if difficulty == "medium":
            return randint(2, 3)
        return randint(4, 5)

    def family_for_degree(self, degree):
        if degree == 1:
            return "linear"
        if degree == 2:
            return "quadratic"
        return "polynomial"

    def generate(self, difficulty):
        degree = self.degree_for(difficulty)
        family = self.family_for_degree(degree)
        coefficient_limit = 4 if difficulty == "easy" else 7
        input_value = randint(-4 if difficulty != "easy" else 1, 6 if difficulty == "easy" else 8)
        coefficients = [randint(1, coefficient_limit)]
        for _exponent in range(degree - 1, -1, -1):
            coefficients.append(randint(-10, 10))

        return {
            "family": family,
            "coefficients": coefficients,
            "input_value": input_value,
            "correct_answer": evaluate_polynomial(coefficients, input_value),
        }


EVALUATING_FUNCTIONS_PROBLEM_TYPE = EvaluatingFunctionsProblemType()


@dataclass(frozen=True)
class DomainRangeProblemType:
    topic: str = "domain_and_range"
    problem_type: str = "domain_range_equation"
    question_targets: tuple[str, ...] = ("domain", "range")
    function_families: tuple[str, ...] = ("linear", "quadratic", "absolute_value", "square_root")
    presentations: tuple[str, ...] = ("equation",)

    def generate(self, difficulty):
        family = self.function_families[randint(0, len(self.function_families) - 1)]
        function_data = self.generate_function_data(family, difficulty)
        return {
            "presentation": "equation",
            "question_targets": list(self.question_targets),
            "function": function_data,
            "domain": domain_for(function_data),
            "range": range_for(function_data),
        }

    def generate_function_data(self, family, difficulty):
        if family == "linear":
            return {
                "family": "linear",
                "m": nonzero_random(-5, 5),
                "b": randint(-8, 8),
            }
        if family == "quadratic":
            return {
                "family": "quadratic",
                "form": "vertex",
                "a": nonzero_choice((-2, -1, 1, 2)),
                "h": randint(-6, 6),
                "k": randint(-8, 8),
            }
        if family == "absolute_value":
            return {
                "family": "absolute_value",
                "a": nonzero_choice((-2, -1, 1, 2)),
                "h": randint(-6, 6),
                "k": randint(-8, 8),
            }
        return {
            "family": "square_root",
            "a": nonzero_choice((-2, -1, 1, 2)),
            "h": randint(-6, 6),
            "k": randint(-8, 8),
        }


DOMAIN_RANGE_PROBLEM_TYPE = DomainRangeProblemType()


def evaluate_polynomial(coefficients, x):
    value = 0
    degree = len(coefficients) - 1
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        value += coefficient * (x**exponent)
    return value


def nonzero_random(start, stop):
    value = 0
    while value == 0:
        value = randint(start, stop)
    return value


def nonzero_choice(values):
    return values[randint(0, len(values) - 1)]


def interval_all_real():
    return "(-∞, ∞)"


def interval_from(value):
    return f"[{value}, ∞)"


def interval_to(value):
    return f"(-∞, {value}]"


def domain_for(function_data):
    if function_data["family"] == "square_root":
        h = function_data["h"]
        return interval_from(h)
    return interval_all_real()


def range_for(function_data):
    family = function_data["family"]
    if family == "linear":
        return interval_all_real()
    if family in ("quadratic", "absolute_value", "square_root"):
        k = function_data["k"]
        return interval_from(k) if function_data["a"] > 0 else interval_to(k)
    return interval_all_real()


def equation_for(function_data):
    family = function_data["family"]
    if family == "linear":
        return format_linear_equation(function_data)
    if family == "quadratic":
        return format_quadratic_vertex_equation(function_data)
    if family == "absolute_value":
        return format_absolute_value_equation(function_data)
    return format_square_root_equation(function_data)


def create_problem(
    topic,
    problem_type,
    difficulty,
    display_equation,
    prompt,
    answer_fields,
    correct_answer,
    acceptable_answers,
    hint,
    solution,
    metadata=None,
    assets=None,
):
    answers = [str(answer) for answer in acceptable_answers]
    correct = str(correct_answer)
    if correct not in answers:
        answers.insert(0, correct)

    return Problem(
        topic=topic,
        problem_type=problem_type,
        difficulty=difficulty,
        display_equation=display_equation,
        prompt=prompt,
        answer_fields=answer_fields,
        correct_answer=correct,
        acceptable_answers=answers,
        hint=hint,
        solution=solution,
        metadata=metadata or {},
        assets=assets or [],
    )


def render_evaluating_functions_problem(data, difficulty):
    coefficients = data["coefficients"]
    input_value = data["input_value"]
    correct_answer = data["correct_answer"]
    equation = format_function_equation(coefficients)
    prompt = f"Evaluate f({input_value})."
    substitution = format_function_substitution(coefficients, input_value)

    return create_problem(
        topic=EVALUATING_FUNCTIONS_PROBLEM_TYPE.topic,
        problem_type=EVALUATING_FUNCTIONS_PROBLEM_TYPE.problem_type,
        difficulty=difficulty,
        display_equation=equation,
        prompt=prompt,
        answer_fields=[{"name": "value", "label": "Answer", "type": "text"}],
        correct_answer=correct_answer,
        acceptable_answers=[correct_answer],
        hint="Substitute the input value anywhere x appears.",
        solution=f"f({input_value}) = {substitution} = {correct_answer}.",
        metadata=data,
    )


def evaluating_functions(difficulty):
    data = EVALUATING_FUNCTIONS_PROBLEM_TYPE.generate(difficulty)
    return render_evaluating_functions_problem(data, difficulty)


def domain_range_answer_fields(data):
    helpers = ["∞", "-∞", "∪"]
    fields = []
    if "domain" in data["question_targets"]:
        fields.append(
            {
                "name": "domain",
                "label": "Domain",
                "type": "text",
                "correct_answer": data["domain"],
                "helpers": helpers,
            }
        )
    if "range" in data["question_targets"]:
        fields.append(
            {
                "name": "range",
                "label": "Range",
                "type": "text",
                "correct_answer": data["range"],
                "helpers": helpers,
            }
        )
    return fields


def render_domain_range_problem(data, difficulty):
    function_data = data["function"]
    equation = equation_for(function_data)
    answer_fields = domain_range_answer_fields(data)
    answer_summary = "; ".join(f'{field["label"]}: {field["correct_answer"]}' for field in answer_fields)

    return create_problem(
        topic=DOMAIN_RANGE_PROBLEM_TYPE.topic,
        problem_type=DOMAIN_RANGE_PROBLEM_TYPE.problem_type,
        difficulty=difficulty,
        display_equation=equation,
        prompt="State the domain and range using interval notation.",
        answer_fields=answer_fields,
        correct_answer=answer_summary,
        acceptable_answers=[answer_summary],
        hint=domain_range_hint(function_data),
        solution=domain_range_solution(function_data, data["domain"], data["range"]),
        metadata=data,
    )


def domain_and_range(difficulty):
    data = DOMAIN_RANGE_PROBLEM_TYPE.generate(difficulty)
    return render_domain_range_problem(data, difficulty)


def domain_range_hint(function_data):
    family = function_data["family"]
    if family == "linear":
        return "Linear functions continue forever in both directions."
    if family == "square_root":
        return "For square root functions, start with the value that makes the expression inside the radical equal 0."
    if function_data["a"] > 0:
        return "The vertex gives the minimum output value."
    return "The vertex gives the maximum output value."


def domain_range_solution(function_data, domain, range_value):
    family = function_data["family"].replace("_", " ")
    return f"This {family} function has domain {domain} and range {range_value}."


def parent_functions(difficulty):
    choices = [
        ("y = (x - 3)^2 + 4", "quadratic"),
        ("y = |x + 2| - 5", "absolute value"),
        ("y = sqrt(x - 1)", "square root"),
        ("y = 2^(x - 4)", "exponential"),
    ]
    equation, answer = choices[randint(0, len(choices) - 1)]
    return create_problem(
        topic="parent_functions",
        problem_type="identify_parent_family",
        difficulty=difficulty,
        display_equation=equation,
        prompt="Identify the parent function family.",
        answer_fields=[{"name": "family", "label": "Family", "type": "text"}],
        correct_answer=answer,
        acceptable_answers=[answer],
        hint="Ignore shifts, stretches, and reflections. Focus on the core shape.",
        solution=f"The core function family is {answer}.",
        metadata={},
    )


GENERATORS = {
    "evaluating_functions": evaluating_functions,
    "domain_and_range": domain_and_range,
    "parent_functions": parent_functions,
}
