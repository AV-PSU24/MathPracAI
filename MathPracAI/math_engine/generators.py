from dataclasses import dataclass
from math import ceil, floor, isfinite, log10
from random import randint

from math_engine.formatters import (
    format_absolute_value_equation,
    format_cubic_transformed_equation,
    format_function_equation,
    format_function_substitution,
    format_linear_equation,
    format_quadratic_vertex_equation,
    format_square_root_equation,
)
from math_engine.models import Problem, function_graph_config, no_graph_config


GRAPH_PADDING_RATIO = 0.12
GRAPH_MIN_SPAN = 4
GRAPH_SAMPLE_COUNT = 120


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

    def degree_for_family(self, family, difficulty):
        if family == "linear":
            return 1
        if family == "quadratic":
            return 2
        if difficulty == "medium":
            return randint(3, 4)
        if difficulty == "hard":
            return randint(3, 5)
        return 3

    def generate(self, difficulty, options=None):
        options = options if isinstance(options, dict) else {}
        config = options.get("topic_config") if isinstance(options.get("topic_config"), dict) else options
        families = selected_values(config, "functionFamilies", self.supported_families)
        family = random_from(families)
        degree = self.degree_for_family(family, difficulty)
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
    function_families: tuple[str, ...] = ("linear", "quadratic", "absolute_value", "square_root", "cubic")
    function_styles: tuple[str, ...] = ("simple", "transformations")
    domain_restrictions: tuple[str, ...] = ("none", "restricted_interval", "union_of_intervals")
    presentations: tuple[str, ...] = ("equation", "graph")

    def generate(self, difficulty, options=None):
        constraints = self.normalized_constraints(options)
        for _attempt in range(100):
            family = random_from(constraints["functionFamilies"])
            style = random_from(constraints["functionStyles"])
            domain_restriction = random_from(constraints["domainRestrictions"])
            presentation = random_from(constraints["questionViews"])
            function_data = self.generate_function_data(family, difficulty, style)
            domain_segments = restricted_domain_segments(function_data, domain_restriction)
            data = {
                "presentation": presentation,
                "question_targets": list(self.question_targets),
                "function_style": style,
                "domain_restriction": domain_restriction,
                "domain_segments": domain_segments or [],
                "function": function_data,
                "domain": domain_for(function_data, domain_segments),
                "range": range_for(function_data, domain_segments),
            }
            if self.matches_constraints(data, constraints):
                return data

        family = constraints["functionFamilies"][0]
        style = constraints["functionStyles"][0]
        domain_restriction = constraints["domainRestrictions"][0]
        function_data = self.generate_function_data(family, difficulty, style)
        domain_segments = restricted_domain_segments(function_data, domain_restriction)
        return {
            "presentation": constraints["questionViews"][0],
            "question_targets": list(self.question_targets),
            "function_style": style,
            "domain_restriction": domain_restriction,
            "domain_segments": domain_segments or [],
            "function": function_data,
            "domain": domain_for(function_data, domain_segments),
            "range": range_for(function_data, domain_segments),
        }

    def normalized_constraints(self, options):
        options = options if isinstance(options, dict) else {}
        config = options.get("topic_config") if isinstance(options.get("topic_config"), dict) else options
        return {
            "functionFamilies": selected_values(config, "functionFamilies", self.function_families),
            "functionStyles": selected_values(config, "functionStyles", self.function_styles),
            "domainRestrictions": selected_values(config, "domainRestrictions", self.domain_restrictions),
            "questionViews": selected_values(options, "questionViews", self.presentations),
        }

    def matches_constraints(self, data, constraints):
        return (
            data["function"]["family"] in constraints["functionFamilies"]
            and data["function_style"] in constraints["functionStyles"]
            and data["domain_restriction"] in constraints["domainRestrictions"]
            and data["presentation"] in constraints["questionViews"]
        )

    def generate_function_data(self, family, difficulty, style):
        if style == "simple":
            return simple_function_data(family)

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
        if family == "cubic":
            return {
                "family": "cubic",
                "a": nonzero_choice((-2, -1, 1, 2)),
                "h": randint(-5, 5),
                "k": randint(-8, 8),
            }
        return {
            "family": "square_root",
            "a": nonzero_choice((-2, -1, 1, 2)),
            "h": randint(-6, 6),
            "k": randint(-8, 8),
        }


DOMAIN_RANGE_PROBLEM_TYPE = DomainRangeProblemType()


def random_from(values):
    return values[randint(0, len(values) - 1)]


def selected_values(options, key, valid_values):
    raw_values = options.get(key) if isinstance(options, dict) else None
    if isinstance(raw_values, str):
        raw_values = (raw_values,)
    elif raw_values:
        raw_values = tuple(raw_values)
    else:
        raw_values = ()

    selected = tuple(value for value in valid_values if value in raw_values)
    return selected or valid_values[:1]


def simple_function_data(family):
    if family == "linear":
        return {"family": "linear", "m": 1, "b": 0}
    if family == "quadratic":
        return {"family": "quadratic", "form": "vertex", "a": 1, "h": 0, "k": 0}
    if family == "absolute_value":
        return {"family": "absolute_value", "a": 1, "h": 0, "k": 0}
    if family == "square_root":
        return {"family": "square_root", "a": 1, "h": 0, "k": 0}
    return {"family": "cubic", "a": 1, "h": 0, "k": 0}


def closed_segment(low, high):
    return {"low": clean_number(low), "high": clean_number(high), "low_closed": True, "high_closed": True}


def minimum_domain_low(function_data):
    return function_data["h"] if function_data["family"] == "square_root" else -6


def restricted_domain_segments(function_data, domain_restriction):
    if domain_restriction == "none":
        return None

    start_floor = minimum_domain_low(function_data)
    start = randint(start_floor, start_floor + 3)
    first_end = start + randint(3, 6)
    if domain_restriction == "restricted_interval":
        return [closed_segment(start, first_end)]

    second_start = first_end + randint(2, 4)
    second_end = second_start + randint(2, 5)
    return [closed_segment(start, first_end), closed_segment(second_start, second_end)]


def evaluate_polynomial(coefficients, x):
    value = 0
    degree = len(coefficients) - 1
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        value += coefficient * (x**exponent)
    return value


def clean_number(value):
    if isinstance(value, bool):
        return value
    number = float(value)
    if abs(number) < 1e-10:
        number = 0
    rounded = round(number)
    if abs(number - rounded) < 1e-10:
        return int(rounded)
    return round(number, 6)


def point(x, y, label=None):
    graph_point = {"x": clean_number(x), "y": clean_number(y)}
    if label:
        graph_point["label"] = label
    return graph_point


def unique_points(points):
    seen = set()
    unique = []
    for graph_point in points:
        key = (graph_point.get("x"), graph_point.get("y"), graph_point.get("label", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(graph_point)
    return unique


def labeled_feature_point(feature_point, label):
    if not isinstance(feature_point, dict):
        return None
    return point(feature_point["x"], feature_point["y"], label)


def graph_points_from_features(features):
    points = []
    for label in ("vertex", "endpoint", "y_intercept"):
        graph_point = labeled_feature_point(features.get(label), label)
        if graph_point:
            points.append(graph_point)
    for graph_point in features.get("x_intercepts", []):
        labeled = labeled_feature_point(graph_point, "x_intercept")
        if labeled:
            points.append(labeled)
    return unique_points(points)


def nice_step(raw_step):
    if raw_step <= 0 or not isfinite(raw_step):
        return 1
    magnitude = 10 ** floor(log10(raw_step))
    fraction = raw_step / magnitude
    if fraction <= 1:
        nice_fraction = 1
    elif fraction <= 2:
        nice_fraction = 2
    elif fraction <= 5:
        nice_fraction = 5
    else:
        nice_fraction = 10
    return nice_fraction * magnitude


def padded_graph_bounds(values, min_span=GRAPH_MIN_SPAN):
    finite_values = [value for value in values if isinstance(value, (int, float)) and isfinite(value)]
    if not finite_values:
        return -10, 10

    low = min(finite_values)
    high = max(finite_values)
    if low == high:
        low -= min_span / 2
        high += min_span / 2

    span = high - low
    padding = max(span * GRAPH_PADDING_RATIO, 0.5)
    low -= padding
    high += padding

    if high - low < min_span:
        center = (low + high) / 2
        low = center - min_span / 2
        high = center + min_span / 2

    step = nice_step((high - low) / 8)
    return clean_number(floor(low / step) * step), clean_number(ceil(high / step) * step)


def sample_x_values(x_min, x_max, count=GRAPH_SAMPLE_COUNT):
    if count <= 1:
        return [x_min]
    step = (x_max - x_min) / (count - 1)
    return [x_min + step * index for index in range(count)]


def polynomial_x_bounds(coefficients):
    degree = len(coefficients) - 1
    if degree == 1:
        return -6, 6
    if degree == 2 and coefficients[0] != 0:
        vertex_x = -coefficients[1] / (2 * coefficients[0])
        return padded_graph_bounds([vertex_x - 5, vertex_x + 5])
    if degree == 2:
        return -6, 6
    return -3, 3


def polynomial_graph_bounds(coefficients):
    x_min, x_max = polynomial_x_bounds(coefficients)
    y_values = [evaluate_polynomial(coefficients, x) for x in sample_x_values(x_min, x_max)]
    y_min, y_max = padded_graph_bounds(y_values)
    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
    }


def polynomial_graph_features(coefficients):
    degree = len(coefficients) - 1
    features = {
        "degree": degree,
        "domain": interval_all_real(),
        "x_intercepts": [],
        "y_intercept": point(0, coefficients[-1]),
    }

    if degree == 1:
        m, b = coefficients
        features.update(linear_features({"family": "linear", "m": m, "b": b}))
    elif degree == 2:
        a, b, c = coefficients
        vertex_x = -b / (2 * a)
        vertex_y = evaluate_polynomial(coefficients, vertex_x)
        features.update(
            {
                "vertex": point(vertex_x, vertex_y),
                "axis_of_symmetry": {"x": clean_number(vertex_x)},
                "opens": "up" if a > 0 else "down",
                "x_intercepts": quadratic_standard_x_intercepts(a, b, c),
                "range": interval_from(clean_number(vertex_y)) if a > 0 else interval_to(clean_number(vertex_y)),
            }
        )
    return features


def evaluate_function_data(function_data, x):
    family = function_data["family"]
    if family == "linear":
        return function_data["m"] * x + function_data["b"]

    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    shifted = x - h

    if family == "quadratic":
        return a * (shifted**2) + k
    if family == "absolute_value":
        return a * abs(shifted) + k
    if family == "square_root":
        if shifted < 0:
            return None
        return a * (shifted**0.5) + k
    if family == "cubic":
        return a * (shifted**3) + k
    return None


def function_data_x_bounds(function_data, domain_segments=None):
    if domain_segments:
        return padded_graph_bounds(
            [
                value
                for segment in domain_segments
                for value in (segment.get("low"), segment.get("high"))
            ]
        )

    family = function_data["family"]
    if family == "linear":
        return -6, 6
    if family in ("quadratic", "absolute_value"):
        h = function_data["h"]
        return padded_graph_bounds([h - 5, h + 5])
    if family == "square_root":
        h = function_data["h"]
        return h, h + 9
    if family == "cubic":
        h = function_data["h"]
        return padded_graph_bounds([h - 4, h + 4])
    return -10, 10


def function_data_graph_bounds(function_data, domain_segments=None):
    x_min, x_max = function_data_x_bounds(function_data, domain_segments)
    if domain_segments:
        sample_values = [
            x
            for segment in domain_segments
            for x in sample_x_values(segment["low"], segment["high"])
        ]
    else:
        sample_values = sample_x_values(x_min, x_max)
    y_values = [y for y in (evaluate_function_data(function_data, x) for x in sample_values) if y is not None]
    y_min, y_max = padded_graph_bounds(y_values)
    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
    }


def real_square_root(value):
    if value < 0:
        return None
    return value**0.5


def real_cuberoot(value):
    return value ** (1 / 3) if value >= 0 else -((-value) ** (1 / 3))


def linear_features(function_data):
    m = function_data["m"]
    b = function_data["b"]
    x_intercepts = []
    if m != 0:
        x_intercepts.append(point(-b / m, 0))

    return {
        "y_intercept": point(0, b),
        "x_intercepts": x_intercepts,
        "slope": clean_number(m),
        "domain": interval_all_real(),
        "range": interval_all_real(),
    }


def quadratic_standard_x_intercepts(a, b, c):
    discriminant = b**2 - 4 * a * c
    root = real_square_root(discriminant)
    if root is None:
        return []
    denominator = 2 * a
    return unique_points([point((-b - root) / denominator, 0), point((-b + root) / denominator, 0)])


def quadratic_features(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    root_distance = real_square_root(-k / a)
    x_intercepts = []
    if root_distance is not None:
        x_intercepts = unique_points([point(h - root_distance, 0), point(h + root_distance, 0)])

    return {
        "vertex": point(h, k),
        "axis_of_symmetry": {"x": clean_number(h)},
        "opens": "up" if a > 0 else "down",
        "x_intercepts": x_intercepts,
        "y_intercept": point(0, evaluate_function_data(function_data, 0)),
        "domain": interval_all_real(),
        "range": range_for(function_data),
    }


def absolute_value_features(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    root_distance = -k / a
    x_intercepts = []
    if root_distance >= 0:
        x_intercepts = unique_points([point(h - root_distance, 0), point(h + root_distance, 0)])

    return {
        "vertex": point(h, k),
        "axis_of_symmetry": {"x": clean_number(h)},
        "opens": "up" if a > 0 else "down",
        "x_intercepts": x_intercepts,
        "y_intercept": point(0, evaluate_function_data(function_data, 0)),
        "domain": interval_all_real(),
        "range": range_for(function_data),
    }


def square_root_features(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    endpoint = point(h, k)
    root_value = -k / a
    x_intercepts = []
    if root_value >= 0:
        x_intercepts = [point(h + root_value**2, 0)]

    y_intercept = None
    if h <= 0:
        y_intercept = point(0, evaluate_function_data(function_data, 0))

    return {
        "endpoint": endpoint,
        "endpoints": [endpoint],
        "starts_at": endpoint,
        "direction": "right",
        "x_intercepts": x_intercepts,
        "y_intercept": y_intercept,
        "domain": domain_for(function_data),
        "range": range_for(function_data),
    }


def cubic_features(function_data):
    h = function_data["h"]
    k = function_data["k"]
    return {
        "inflection": point(h, k),
        "y_intercept": point(0, evaluate_function_data(function_data, 0)),
        "x_intercepts": [point(h + real_cuberoot(-k / function_data["a"]), 0)],
        "domain": interval_all_real(),
        "range": interval_all_real(),
    }


def features_for_function(function_data):
    family = function_data["family"]
    if family == "linear":
        return linear_features(function_data)
    if family == "quadratic":
        return quadratic_features(function_data)
    if family == "absolute_value":
        return absolute_value_features(function_data)
    if family == "square_root":
        return square_root_features(function_data)
    if family == "cubic":
        return cubic_features(function_data)
    return {}


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


def interval_between(low, high):
    return f"[{clean_number(low)}, {clean_number(high)}]"


def interval_union(intervals):
    return " ∪ ".join(interval_between(low, high) for low, high in intervals)


def domain_for(function_data, domain_segments=None):
    if domain_segments:
        return interval_union((segment["low"], segment["high"]) for segment in domain_segments)
    if function_data["family"] == "square_root":
        h = function_data["h"]
        return interval_from(h)
    return interval_all_real()


def range_for(function_data, domain_segments=None):
    if domain_segments:
        return interval_union(merged_range_intervals(function_data, domain_segments))

    family = function_data["family"]
    if family in ("linear", "cubic"):
        return interval_all_real()
    if family in ("quadratic", "absolute_value", "square_root"):
        k = function_data["k"]
        return interval_from(k) if function_data["a"] > 0 else interval_to(k)
    return interval_all_real()


def critical_x_values(function_data):
    if function_data["family"] in ("quadratic", "absolute_value"):
        return (function_data["h"],)
    return ()


def range_interval_on_segment(function_data, segment):
    low = segment["low"]
    high = segment["high"]
    candidates = [low, high]
    candidates.extend(x for x in critical_x_values(function_data) if low <= x <= high)
    y_values = [
        y
        for y in (evaluate_function_data(function_data, x) for x in candidates)
        if y is not None
    ]
    return clean_number(min(y_values)), clean_number(max(y_values))


def merged_range_intervals(function_data, domain_segments):
    intervals = sorted(range_interval_on_segment(function_data, segment) for segment in domain_segments)
    merged = []
    for low, high in intervals:
        if not merged or low > merged[-1][1]:
            merged.append([low, high])
        else:
            merged[-1][1] = max(merged[-1][1], high)
    return tuple((low, high) for low, high in merged)


def equation_for(function_data):
    family = function_data["family"]
    if family == "linear":
        return format_linear_equation(function_data)
    if family == "quadratic":
        return format_quadratic_vertex_equation(function_data)
    if family == "absolute_value":
        return format_absolute_value_equation(function_data)
    if family == "square_root":
        return format_square_root_equation(function_data)
    return format_cubic_transformed_equation(function_data)


def signed_raw(value):
    return f"+{value}" if value > 0 else str(value)


def raw_shift_expression(h):
    if h == 0:
        return "x"
    return f"x-{h}" if h > 0 else f"x+{abs(h)}"


def raw_coefficient_prefix(coefficient):
    if coefficient == 1:
        return ""
    if coefficient == -1:
        return "-"
    return str(coefficient)


def raw_polynomial_term(coefficient, exponent):
    absolute = abs(coefficient)
    if exponent == 0:
        return str(absolute)
    if exponent == 1:
        return "x" if absolute == 1 else f"{absolute}x"
    return f"x^{exponent}" if absolute == 1 else f"{absolute}x^{exponent}"


def raw_polynomial_expression(coefficients):
    degree = len(coefficients) - 1
    pieces = []
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        body = raw_polynomial_term(coefficient, degree - index)
        if not pieces:
            pieces.append(f"-{body}" if coefficient < 0 else body)
        else:
            pieces.append(f"-{body}" if coefficient < 0 else f"+{body}")
    return "".join(pieces) if pieces else "0"


def raw_function_expression(function_data):
    family = function_data["family"]
    if family == "linear":
        expression = raw_polynomial_expression([function_data["m"], function_data["b"]])
    elif family == "quadratic":
        base = raw_shift_expression(function_data["h"])
        wrapped_base = base if function_data["h"] == 0 else f"({base})"
        expression = f'{raw_coefficient_prefix(function_data["a"])}{wrapped_base}^2'
    elif family == "absolute_value":
        expression = f'{raw_coefficient_prefix(function_data["a"])}abs({raw_shift_expression(function_data["h"])})'
    elif family == "square_root":
        expression = f'{raw_coefficient_prefix(function_data["a"])}sqrt({raw_shift_expression(function_data["h"])})'
    else:
        base = raw_shift_expression(function_data["h"])
        wrapped_base = base if function_data["h"] == 0 else f"({base})"
        expression = f'{raw_coefficient_prefix(function_data["a"])}{wrapped_base}^3'

    k = function_data.get("k", 0)
    return f"{expression}{signed_raw(k)}" if k else expression


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
    graph_config=None,
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
        graph_config=graph_config if graph_config is not None else no_graph_config(),
    )


def render_evaluating_functions_problem(data, difficulty):
    coefficients = data["coefficients"]
    input_value = data["input_value"]
    correct_answer = data["correct_answer"]
    equation = format_function_equation(coefficients)
    prompt = f"Evaluate f({input_value})."
    substitution = format_function_substitution(coefficients, input_value)
    graph_bounds = polynomial_graph_bounds(coefficients)
    graph_features = polynomial_graph_features(coefficients)

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
        graph_config=function_graph_config(
            raw_polynomial_expression(coefficients),
            **graph_bounds,
            points=graph_points_from_features(graph_features),
            features=graph_features,
        ),
    )


def evaluating_functions(difficulty, options=None):
    data = EVALUATING_FUNCTIONS_PROBLEM_TYPE.generate(difficulty, options)
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
    domain_segments = data.get("domain_segments") or None
    equation = equation_for(function_data)
    answer_fields = domain_range_answer_fields(data)
    answer_summary = "; ".join(f'{field["label"]}: {field["correct_answer"]}' for field in answer_fields)
    graph_bounds = function_data_graph_bounds(function_data, domain_segments)
    graph_features = features_for_function(function_data)
    if domain_segments:
        graph_features["domain_segments"] = domain_segments

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
        graph_config=function_graph_config(
            raw_function_expression(function_data),
            **graph_bounds,
            points=graph_points_from_features(graph_features),
            features=graph_features,
        ),
    )


def domain_and_range(difficulty, options=None):
    data = DOMAIN_RANGE_PROBLEM_TYPE.generate(difficulty, options)
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


PARENT_FUNCTION_CHOICES = (
    {"family": "quadratic", "equation": "y = (x - 3)^2 + 4", "answer": "quadratic"},
    {"family": "absolute_value", "equation": "y = |x + 2| - 5", "answer": "absolute value"},
    {"family": "square_root", "equation": "y = sqrt(x - 1)", "answer": "square root"},
    {"family": "exponential", "equation": "y = 2^(x - 4)", "answer": "exponential"},
)


def parent_functions(difficulty, options=None):
    options = options if isinstance(options, dict) else {}
    config = options.get("topic_config") if isinstance(options.get("topic_config"), dict) else options
    valid_families = tuple(choice["family"] for choice in PARENT_FUNCTION_CHOICES)
    selected_families = selected_values(config, "parentFamilies", valid_families)
    choices = tuple(choice for choice in PARENT_FUNCTION_CHOICES if choice["family"] in selected_families)
    choice = random_from(choices)
    equation = choice["equation"]
    answer = choice["answer"]
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
        metadata={"family": choice["family"]},
        graph_config=no_graph_config(),
    )


GENERATORS = {
    "evaluating_functions": evaluating_functions,
    "domain_and_range": domain_and_range,
    "parent_functions": parent_functions,
}
