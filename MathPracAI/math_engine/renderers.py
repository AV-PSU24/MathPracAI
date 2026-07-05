from html import escape
import ast
import json
import math
import re

from math_engine.models import encoded_problem
from views.shared_views import profile_menu


SQRT_PATTERN = re.compile(r"(?<![A-Za-z_])sqrt(?=\s*\()")
GRAPH_WIDTH = 640
GRAPH_HEIGHT = 400
GRAPH_PADDING = 42
GRAPH_SAMPLE_COUNT = 520
GRAPH_MAX_POWER = 12
GRAPH_DEFAULT_X_MIN = -10
GRAPH_DEFAULT_X_MAX = 10
GRAPH_DEFAULT_Y_MIN = -10
GRAPH_DEFAULT_Y_MAX = 10
GRAPH_EPSILON = 0.000001
GRAPH_POINT_LABEL_HEIGHT = 16
GRAPH_POINT_LABEL_CHAR_WIDTH = 7.2
GRAPH_POINT_LABEL_MARGIN = 3
GRAPH_POINT_LABEL_MIN_WIDTH = 32
GRAPH_TOKEN_PATTERN = re.compile(
    r"""
    (?P<number>(?:\d+(?:\.\d*)?|\.\d+))
    |(?P<name>[A-Za-z_][A-Za-z_0-9]*)
    |(?P<operator>\*\*|[+\-*/^()])
    |(?P<space>\s+)
    |(?P<other>.)
    """,
    re.VERBOSE,
)
SUPERSCRIPT_TRANSLATION = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
DEFAULT_QUESTION_VIEW_OPTIONS = (("equation", "Given equation"),)
QUESTION_VIEW_OPTIONS_BY_TOPIC = {
    "domain_and_range": (("equation", "Given equation"), ("graph", "Given graph")),
}
TOPIC_CONFIG_SECTIONS_BY_TOPIC = {
    "evaluating_functions": (
        {
            "key": "functionFamilies",
            "label": "Function Families",
            "options": (
                ("linear", "Linear"),
                ("quadratic", "Quadratic"),
                ("polynomial", "Polynomial"),
            ),
        },
    ),
    "domain_and_range": (
        {
            "key": "functionFamilies",
            "label": "Function Families",
            "options": (
                ("linear", "Linear"),
                ("quadratic", "Quadratic"),
                ("absolute_value", "Absolute value"),
                ("square_root", "Square root"),
                ("cubic", "Cubic"),
            ),
        },
        {
            "key": "functionStyles",
            "label": "Function Style",
            "options": (
                ("simple", "Simple functions"),
                ("transformations", "Transformations"),
            ),
        },
        {
            "key": "domainRestrictions",
            "label": "Domain Restrictions",
            "options": (
                ("none", "No restriction"),
                ("restricted_interval", "Restricted interval"),
                ("union_of_intervals", "Union of intervals"),
            ),
        },
    ),
    "parent_functions": (
        {
            "key": "parentFamilies",
            "label": "Parent Families",
            "options": (
                ("quadratic", "Quadratic"),
                ("absolute_value", "Absolute value"),
                ("square_root", "Square root"),
                ("exponential", "Exponential"),
            ),
        },
    ),
}


def question_view_options_for_topic(topic):
    return QUESTION_VIEW_OPTIONS_BY_TOPIC.get(topic, DEFAULT_QUESTION_VIEW_OPTIONS)


def valid_question_view_values(topic):
    return tuple(value for value, _label in question_view_options_for_topic(topic))


def default_question_view_values(topic):
    return valid_question_view_values(topic)[:1]


def topic_config_sections(topic):
    return TOPIC_CONFIG_SECTIONS_BY_TOPIC.get(topic, ())


def topic_config_field_names():
    return tuple(
        section["key"]
        for sections in TOPIC_CONFIG_SECTIONS_BY_TOPIC.values()
        for section in sections
    )


def valid_topic_config_values(section):
    return tuple(value for value, _label in section["options"])


def default_topic_config_values(section):
    return valid_topic_config_values(section)[:1]


def selected_topic_config_values(state, topic):
    selections = {}
    for section in topic_config_sections(topic):
        key = section["key"]
        valid_values = valid_topic_config_values(section)
        default_values = default_topic_config_values(section)
        raw_value = state.get(key, default_values)
        if isinstance(raw_value, str):
            raw_values = (raw_value,)
        else:
            raw_values = tuple(raw_value)

        selected = tuple(value for value in valid_values if value in raw_values)
        selections[key] = selected or default_values
    return selections


def render_math_text(value):
    return escape(SQRT_PATTERN.sub("√", str(value)))


def graph_number(value, fallback):
    if isinstance(value, bool):
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if math.isfinite(number) else fallback


def graph_config_number(graph_config, snake_name, camel_name=None):
    value = graph_config.get(snake_name)
    if value is None and camel_name:
        value = graph_config.get(camel_name)
    return graph_number(value, None)


def strip_equation_prefix(equation):
    expression = str(equation or "").strip().translate(SUPERSCRIPT_TRANSLATION)
    if "=" in expression:
        expression = expression.split("=", 1)[1].strip()
    return expression


def tokenize_math_expression(expression):
    tokens = []
    for match in GRAPH_TOKEN_PATTERN.finditer(expression):
        kind = match.lastgroup
        value = match.group()
        if kind == "space":
            continue
        if kind == "other":
            return None
        if kind == "operator":
            if value == "(":
                tokens.append(("lparen", value))
            elif value == ")":
                tokens.append(("rparen", value))
            else:
                tokens.append(("operator", "**" if value == "^" else value))
        elif kind == "name":
            lowered = value.lower()
            if lowered == "x":
                tokens.append(("x", "x"))
            elif lowered in ("sqrt", "abs"):
                tokens.append(("function", lowered))
            else:
                return None
        else:
            tokens.append((kind, value))
    return tokens


def token_ends_factor(token):
    return token[0] in ("number", "x", "rparen")


def token_starts_factor(token):
    return token[0] in ("number", "x", "function", "lparen")


def compiled_function_expression(equation):
    tokens = tokenize_math_expression(strip_equation_prefix(equation))
    if not tokens:
        return None

    pieces = []
    previous = None
    for token in tokens:
        if previous and token_ends_factor(previous) and token_starts_factor(token):
            pieces.append("*")
        pieces.append(token[1])
        previous = token

    try:
        parsed = ast.parse("".join(pieces), mode="eval")
    except SyntaxError:
        return None

    if not graph_ast_is_safe(parsed):
        return None
    return parsed


def graph_ast_is_safe(node):
    if isinstance(node, ast.Expression):
        return graph_ast_is_safe(node.body)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return node.id == "x"
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, (ast.UAdd, ast.USub)) and graph_ast_is_safe(node.operand)
    if isinstance(node, ast.BinOp):
        return (
            isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow))
            and graph_ast_is_safe(node.left)
            and graph_ast_is_safe(node.right)
        )
    if isinstance(node, ast.Call):
        return (
            isinstance(node.func, ast.Name)
            and node.func.id in ("sqrt", "abs")
            and len(node.args) == 1
            and not node.keywords
            and graph_ast_is_safe(node.args[0])
        )
    return False


def evaluate_graph_ast(node, x_value):
    if isinstance(node, ast.Expression):
        return evaluate_graph_ast(node.body, x_value)
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return float(x_value)
    if isinstance(node, ast.UnaryOp):
        value = evaluate_graph_ast(node.operand, x_value)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = evaluate_graph_ast(node.left, x_value)
        right = evaluate_graph_ast(node.right, x_value)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("division by zero")
            return left / right
        if abs(right) > GRAPH_MAX_POWER:
            raise ValueError("power too large")
        return left**right
    if isinstance(node, ast.Call):
        value = evaluate_graph_ast(node.args[0], x_value)
        if node.func.id == "sqrt":
            if value < 0:
                raise ValueError("square root domain")
            return math.sqrt(value)
        return abs(value)
    raise ValueError("unsupported expression")


def evaluated_function_value(compiled_expression, x_value):
    try:
        y_value = evaluate_graph_ast(compiled_expression, x_value)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None
    return y_value if math.isfinite(y_value) else None


def screen_x(x_value, x_min, x_max):
    plot_width = GRAPH_WIDTH - (GRAPH_PADDING * 2)
    return GRAPH_PADDING + ((x_value - x_min) / (x_max - x_min)) * plot_width


def screen_y(y_value, y_min, y_max):
    plot_height = GRAPH_HEIGHT - (GRAPH_PADDING * 2)
    return GRAPH_HEIGHT - GRAPH_PADDING - ((y_value - y_min) / (y_max - y_min)) * plot_height


def plot_left():
    return GRAPH_PADDING


def plot_right():
    return GRAPH_WIDTH - GRAPH_PADDING


def plot_top():
    return GRAPH_PADDING


def plot_bottom():
    return GRAPH_HEIGHT - GRAPH_PADDING


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def nice_tick_step(span):
    rough_step = span / 8
    magnitude = 10 ** math.floor(math.log10(rough_step)) if rough_step > 0 else 1
    for multiplier in (1, 2, 5, 10):
        step = multiplier * magnitude
        if rough_step <= step:
            return step
    return 10 * magnitude


def graph_ticks(min_value, max_value, step, max_count=120):
    if step <= 0:
        return []
    start = math.ceil(min_value / step) * step
    ticks = []
    value = start
    while value <= max_value + step * 0.001 and len(ticks) < max_count:
        if min_value <= value <= max_value:
            ticks.append(0 if abs(value) < step * 0.001 else value)
        value += step
    return ticks


def padded_bounds(min_value, max_value, min_span=2):
    if min_value > max_value:
        min_value, max_value = max_value, min_value
    span = max_value - min_value
    if span < min_span:
        center = (min_value + max_value) / 2
        half_span = min_span / 2
        return center - half_span, center + half_span
    padding = max(span * 0.12, min_span * 0.08)
    return min_value - padding, max_value + padding


def valid_bound_pair(min_value, max_value):
    return min_value is not None and max_value is not None and min_value < max_value


def sampled_function_values(compiled_expression, x_min, x_max, count=GRAPH_SAMPLE_COUNT):
    samples = []
    if x_min >= x_max or count < 2:
        return samples
    step = (x_max - x_min) / (count - 1)
    for index in range(count):
        x_value = x_min + (index * step)
        y_value = evaluated_function_value(compiled_expression, x_value)
        if y_value is not None:
            samples.append((x_value, y_value))
    return samples


def sampled_y_bounds(compiled_expression, x_min, x_max):
    samples = sampled_function_values(compiled_expression, x_min, x_max)
    y_values = [sample[1] for sample in samples]

    if not y_values:
        return GRAPH_DEFAULT_Y_MIN, GRAPH_DEFAULT_Y_MAX

    return padded_bounds(min(y_values), max(y_values), min_span=2)


def graph_step_config(span):
    major_step = nice_tick_step(span)
    minor_step = major_step / 5
    while span / minor_step > 90:
        minor_step *= 2

    return major_step, minor_step


def resolved_graph_view(graph_config, compiled_expression):
    x_min = graph_config_number(graph_config, "x_min")
    x_max = graph_config_number(graph_config, "x_max")
    y_min = graph_config_number(graph_config, "y_min")
    y_max = graph_config_number(graph_config, "y_max")

    if not valid_bound_pair(x_min, x_max):
        x_min, x_max = GRAPH_DEFAULT_X_MIN, GRAPH_DEFAULT_X_MAX

    if not valid_bound_pair(y_min, y_max):
        y_min, y_max = sampled_y_bounds(compiled_expression, x_min, x_max)

    if not valid_bound_pair(y_min, y_max):
        y_min, y_max = GRAPH_DEFAULT_Y_MIN, GRAPH_DEFAULT_Y_MAX

    x_major_step, x_minor_step = graph_step_config(x_max - x_min)
    y_major_step, y_minor_step = graph_step_config(y_max - y_min)

    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "x_major_step": x_major_step,
        "x_minor_step": x_minor_step,
        "y_major_step": y_major_step,
        "y_minor_step": y_minor_step,
    }


def format_tick(value):
    if abs(value - round(value)) < 0.000001:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def svg_line(x1, y1, x2, y2, class_name):
    return (
        f'<line class="{class_name}" x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{x2:.2f}" y2="{y2:.2f}"></line>'
    )


def is_major_tick(value, major_step):
    return abs((value / major_step) - round(value / major_step)) < 0.0001


def render_tick_mark(x1, y1, x2, y2, class_name):
    return svg_line(x1, y1, x2, y2, class_name)


def render_graph_grid(view):
    x_min = view["x_min"]
    x_max = view["x_max"]
    y_min = view["y_min"]
    y_max = view["y_max"]
    x_major_step = view["x_major_step"]
    x_minor_step = view["x_minor_step"]
    y_major_step = view["y_major_step"]
    y_minor_step = view["y_minor_step"]

    minor_lines = []
    major_lines = []
    axes = []
    tick_marks = []
    labels = []

    x_axis_visible = y_min <= 0 <= y_max
    y_axis_visible = x_min <= 0 <= x_max
    x_axis_y = screen_y(0, y_min, y_max) if x_axis_visible else plot_bottom()
    y_axis_x = screen_x(0, x_min, x_max) if y_axis_visible else plot_left()

    for x_tick in graph_ticks(x_min, x_max, x_minor_step):
        x_pos = screen_x(x_tick, x_min, x_max)
        if abs(x_tick) < GRAPH_EPSILON and y_axis_visible:
            continue
        if is_major_tick(x_tick, x_major_step):
            major_lines.append(svg_line(x_pos, plot_top(), x_pos, plot_bottom(), "graph-grid-line graph-major-grid-line"))
            tick_class = "graph-tick-mark graph-major-tick-mark"
            tick_size = 5
        else:
            minor_lines.append(svg_line(x_pos, plot_top(), x_pos, plot_bottom(), "graph-minor-grid-line"))
            tick_class = "graph-tick-mark graph-minor-tick-mark"
            tick_size = 3
        tick_marks.append(render_tick_mark(x_pos, x_axis_y - tick_size, x_pos, x_axis_y + tick_size, tick_class))
        if is_major_tick(x_tick, x_major_step):
            if x_axis_visible and x_axis_y > plot_bottom() - 22:
                label_y = x_axis_y - 8
            elif x_axis_visible:
                label_y = x_axis_y + 18
            else:
                label_y = plot_bottom() - 8
            label_y = clamp(label_y, plot_top() + 13, plot_bottom() - 6)
            labels.append(
                f'<text class="graph-tick-label graph-x-label" x="{x_pos:.2f}" '
                f'y="{label_y:.2f}">{escape(format_tick(x_tick))}</text>'
            )

    for y_tick in graph_ticks(y_min, y_max, y_minor_step):
        y_pos = screen_y(y_tick, y_min, y_max)
        if abs(y_tick) < GRAPH_EPSILON and x_axis_visible:
            continue
        if is_major_tick(y_tick, y_major_step):
            major_lines.append(svg_line(plot_left(), y_pos, plot_right(), y_pos, "graph-grid-line graph-major-grid-line"))
            tick_class = "graph-tick-mark graph-major-tick-mark"
            tick_size = 5
        else:
            minor_lines.append(svg_line(plot_left(), y_pos, plot_right(), y_pos, "graph-minor-grid-line"))
            tick_class = "graph-tick-mark graph-minor-tick-mark"
            tick_size = 3
        tick_marks.append(render_tick_mark(y_axis_x - tick_size, y_pos, y_axis_x + tick_size, y_pos, tick_class))
        if is_major_tick(y_tick, y_major_step) and not (abs(y_tick) < GRAPH_EPSILON and x_axis_visible):
            if y_axis_visible and y_axis_x < plot_left() + 34:
                label_x = y_axis_x + 8
                anchor = "start"
            elif y_axis_visible:
                label_x = y_axis_x - 8
                anchor = "end"
            else:
                label_x = plot_left() + 8
                anchor = "start"
            label_x = clamp(label_x, plot_left() + 8, plot_right() - 8)
            labels.append(
                f'<text class="graph-tick-label graph-y-label" x="{label_x:.2f}" '
                f'y="{y_pos + 4:.2f}" style="text-anchor: {anchor};">{escape(format_tick(y_tick))}</text>'
            )

    axes.append(svg_line(plot_left(), x_axis_y, plot_right(), x_axis_y, "graph-axis"))
    axes.append(svg_line(y_axis_x, plot_top(), y_axis_x, plot_bottom(), "graph-axis"))

    return "\n".join(minor_lines + major_lines + axes + tick_marks + labels)


def normalized_domain_segments(graph_config, x_min, x_max):
    features = graph_config.get("features", {}) if isinstance(graph_config, dict) else {}
    raw_segments = features.get("domain_segments") if isinstance(features, dict) else None
    segments = []
    for segment in raw_segments if isinstance(raw_segments, list) else []:
        if not isinstance(segment, dict):
            continue
        low = graph_number(segment.get("low"), None)
        high = graph_number(segment.get("high"), None)
        if low is None or high is None or low >= high:
            continue
        segments.append({"low": max(low, x_min), "high": min(high, x_max)})
    return [segment for segment in segments if segment["low"] < segment["high"]]


def sampled_function_segments(compiled_expression, x_min, x_max, y_min, y_max, domain_segments=None):
    segments = []
    sample_ranges = domain_segments or ({"low": x_min, "high": x_max},)
    for sample_range in sample_ranges:
        current_segment = []
        previous_screen_y = None
        sample_min = sample_range["low"]
        sample_max = sample_range["high"]
        step = (sample_max - sample_min) / (GRAPH_SAMPLE_COUNT - 1)

        for index in range(GRAPH_SAMPLE_COUNT):
            x_value = sample_min + (index * step)
            y_value = evaluated_function_value(compiled_expression, x_value)
            visible = y_value is not None and y_min <= y_value <= y_max
            if not visible:
                if len(current_segment) > 1:
                    segments.append(current_segment)
                current_segment = []
                previous_screen_y = None
                continue

            x_pos = screen_x(x_value, x_min, x_max)
            y_pos = screen_y(y_value, y_min, y_max)
            if previous_screen_y is not None and abs(y_pos - previous_screen_y) > GRAPH_HEIGHT * 0.55:
                if len(current_segment) > 1:
                    segments.append(current_segment)
                current_segment = []

            current_segment.append((x_pos, y_pos))
            previous_screen_y = y_pos

        if len(current_segment) > 1:
            segments.append(current_segment)
    return segments


def render_function_paths(segments):
    paths = []
    for segment in segments:
        commands = [f"M {segment[0][0]:.2f} {segment[0][1]:.2f}"]
        commands.extend(f"L {x_pos:.2f} {y_pos:.2f}" for x_pos, y_pos in segment[1:])
        paths.append(f'<path class="graph-curve" d="{" ".join(commands)}"></path>')
    return "\n".join(paths)


def normalized_graph_point(point):
    if isinstance(point, dict):
        x_value = graph_number(point.get("x"), None)
        y_value = graph_number(point.get("y"), None)
        label = point.get("label", "")
    elif isinstance(point, (list, tuple)) and len(point) >= 2:
        x_value = graph_number(point[0], None)
        y_value = graph_number(point[1], None)
        label = ""
    else:
        return None

    if x_value is None or y_value is None:
        return None
    return {"x": x_value, "y": y_value, "label": str(label)}


def estimated_graph_label_width(label):
    return max(GRAPH_POINT_LABEL_MIN_WIDTH, len(label) * GRAPH_POINT_LABEL_CHAR_WIDTH + 10)


def graph_label_rect(label, x_pos, y_pos, anchor):
    width = estimated_graph_label_width(label)
    if anchor == "end":
        left = x_pos - width
    elif anchor == "middle":
        left = x_pos - (width / 2)
    else:
        left = x_pos

    return {
        "left": left,
        "right": left + width,
        "top": y_pos - GRAPH_POINT_LABEL_HEIGHT + 4,
        "bottom": y_pos + 4,
        "width": width,
    }


def rect_overlap_area(rect, other):
    width = min(rect["right"], other["right"]) - max(rect["left"], other["left"])
    height = min(rect["bottom"], other["bottom"]) - max(rect["top"], other["top"])
    if width <= 0 or height <= 0:
        return 0
    return width * height


def rect_overlap_score(rect, placed_rects):
    expanded = {
        "left": rect["left"] - GRAPH_POINT_LABEL_MARGIN,
        "right": rect["right"] + GRAPH_POINT_LABEL_MARGIN,
        "top": rect["top"] - GRAPH_POINT_LABEL_MARGIN,
        "bottom": rect["bottom"] + GRAPH_POINT_LABEL_MARGIN,
    }
    return sum(rect_overlap_area(expanded, placed) for placed in placed_rects)


def rect_outside_score(rect, bounds):
    return (
        max(0, bounds["left"] - rect["left"])
        + max(0, rect["right"] - bounds["right"])
        + max(0, bounds["top"] - rect["top"])
        + max(0, rect["bottom"] - bounds["bottom"])
    )


def nudge_label_inside_bounds(candidate, bounds):
    x_pos = candidate["x"]
    y_pos = candidate["y"]
    rect = candidate["rect"]

    if rect["left"] < bounds["left"]:
        x_pos += bounds["left"] - rect["left"]
    if rect["right"] > bounds["right"]:
        x_pos -= rect["right"] - bounds["right"]
    if rect["top"] < bounds["top"]:
        y_pos += bounds["top"] - rect["top"]
    if rect["bottom"] > bounds["bottom"]:
        y_pos -= rect["bottom"] - bounds["bottom"]

    rect = graph_label_rect(candidate["label"], x_pos, y_pos, candidate["anchor"])
    return {**candidate, "x": x_pos, "y": y_pos, "rect": rect}


def graph_point_label_candidates(label, x_pos, y_pos):
    return (
        {"x": x_pos + 10, "y": y_pos - 10, "anchor": "start", "leader": False},
        {"x": x_pos - 10, "y": y_pos - 10, "anchor": "end", "leader": False},
        {"x": x_pos + 10, "y": y_pos + 22, "anchor": "start", "leader": False},
        {"x": x_pos - 10, "y": y_pos + 22, "anchor": "end", "leader": False},
        {"x": x_pos + 16, "y": y_pos + 5, "anchor": "start", "leader": True},
        {"x": x_pos - 16, "y": y_pos + 5, "anchor": "end", "leader": True},
        {"x": x_pos, "y": y_pos - 16, "anchor": "middle", "leader": True},
        {"x": x_pos, "y": y_pos + 26, "anchor": "middle", "leader": True},
    )


def choose_graph_point_label(label, x_pos, y_pos, placed_rects):
    bounds = {
        "left": plot_left() + 4,
        "right": plot_right() - 4,
        "top": plot_top() + 4,
        "bottom": plot_bottom() - 4,
    }
    candidates = []

    for candidate in graph_point_label_candidates(label, x_pos, y_pos):
        rect = graph_label_rect(label, candidate["x"], candidate["y"], candidate["anchor"])
        candidate = {**candidate, "label": label, "rect": rect}
        candidate = nudge_label_inside_bounds(candidate, bounds)
        candidates.append(
            {
                **candidate,
                "overlap": rect_overlap_score(candidate["rect"], placed_rects),
                "outside": rect_outside_score(candidate["rect"], bounds),
            }
        )

    return min(candidates, key=lambda item: (item["outside"], item["overlap"], item["leader"]))


def render_graph_points(points, x_min, x_max, y_min, y_max):
    rendered = []
    placed_label_rects = []
    for point in points if isinstance(points, list) else []:
        normalized = normalized_graph_point(point)
        if not normalized:
            continue
        x_value = normalized["x"]
        y_value = normalized["y"]
        if not (x_min <= x_value <= x_max and y_min <= y_value <= y_max):
            continue
        x_pos = screen_x(x_value, x_min, x_max)
        y_pos = screen_y(y_value, y_min, y_max)
        rendered.append(f'<circle class="graph-point" cx="{x_pos:.2f}" cy="{y_pos:.2f}" r="4.5"></circle>')
        if normalized["label"]:
            label = normalized["label"]
            placement = choose_graph_point_label(label, x_pos, y_pos, placed_label_rects)
            placed_label_rects.append(placement["rect"])
            if placement["leader"]:
                rendered.append(
                    f'<line class="graph-label-leader" x1="{x_pos:.2f}" y1="{y_pos:.2f}" '
                    f'x2="{placement["x"]:.2f}" y2="{placement["y"] - 5:.2f}"></line>'
                )
            rendered.append(
                f'<text class="graph-point-label" x="{placement["x"]:.2f}" y="{placement["y"]:.2f}" '
                f'style="text-anchor: {placement["anchor"]};">{render_math_text(label)}</text>'
            )
    return "\n".join(rendered)


def render_graph(graph_config, show_caption=True):
    if not isinstance(graph_config, dict) or not graph_config.get("enabled"):
        return ""
    if graph_config.get("type") != "function":
        return ""

    compiled_expression = compiled_function_expression(graph_config.get("equation", ""))
    if compiled_expression is None:
        return ""

    view = resolved_graph_view(graph_config, compiled_expression)
    x_min = view["x_min"]
    x_max = view["x_max"]
    y_min = view["y_min"]
    y_max = view["y_max"]
    domain_segments = normalized_domain_segments(graph_config, x_min, x_max)
    segments = sampled_function_segments(compiled_expression, x_min, x_max, y_min, y_max, domain_segments)
    grid = render_graph_grid(view)
    paths = render_function_paths(segments)
    points = render_graph_points(graph_config.get("points", []), x_min, x_max, y_min, y_max)
    equation_label = render_math_text(strip_equation_prefix(graph_config.get("equation", "")))
    caption = f"<figcaption>y = {equation_label}</figcaption>" if show_caption else ""
    aria_label = (
        f'Graph of y equals {escape(strip_equation_prefix(graph_config.get("equation", "")))}'
        if show_caption
        else "Function graph"
    )

    return f"""        <figure class="graph-card" aria-label="Function graph">
          {caption}
          <svg class="math-graph" viewBox="0 0 {GRAPH_WIDTH} {GRAPH_HEIGHT}" role="img" aria-label="{aria_label}">
            <rect class="graph-plot-bg" x="{GRAPH_PADDING}" y="{GRAPH_PADDING}" width="{GRAPH_WIDTH - GRAPH_PADDING * 2}" height="{GRAPH_HEIGHT - GRAPH_PADDING * 2}"></rect>
            {grid}
            {paths}
            {points}
          </svg>
        </figure>"""


def render_asset(asset):
    if not isinstance(asset, dict):
        return ""
    asset_type = asset.get("type", "")
    if asset_type == "image" and asset.get("src"):
        alt = asset.get("alt", "")
        return f'<img src="{escape(asset["src"])}" alt="{escape(alt)}">'
    if asset_type == "text" and asset.get("content"):
        return render_math_text(asset["content"])
    return ""


def render_problem_display(problem, active_question_view="equation"):
    parts = []
    if active_question_view == "equation" and problem.display_equation:
        parts.append(render_math_text(problem.display_equation))
    if problem.prompt:
        parts.append(render_math_text(problem.prompt))
    for asset in problem.assets:
        rendered_asset = render_asset(asset)
        if rendered_asset:
            parts.append(rendered_asset)
    return "<br><br>".join(parts)


def problem_text_view(problem):
    parts = []
    if problem.display_equation:
        parts.append(render_math_text(problem.display_equation))
    if problem.prompt:
        parts.append(render_math_text(problem.prompt))
    for asset in problem.assets:
        rendered_asset = render_asset(asset)
        if rendered_asset:
            parts.append(rendered_asset)
    return "<br><br>".join(parts)


def problem_prompt_view(problem):
    parts = []
    if problem.prompt:
        parts.append(render_math_text(problem.prompt))
    for asset in problem.assets:
        rendered_asset = render_asset(asset)
        if rendered_asset:
            parts.append(rendered_asset)
    return "<br><br>".join(parts)


def get_problem_presentation(problem, ui_state):
    allowed_views = tuple(ui_state.get("available_views") or ("equation",))
    views = {"equation": None, "graph": None, "table": None}
    text_html = problem_text_view(problem)
    if text_html:
        views["equation"] = {
            "type": "text",
            "html": text_html,
            "supportsText": True,
            "hasTextView": True,
        }
    if "graph" in allowed_views and problem.graph_config.get("enabled"):
        views["graph"] = {
            "type": "graph",
            "graph": problem.graph_config,
            "promptHtml": problem_prompt_view(problem),
            "supportsGraph": True,
            "hasGraphView": True,
        }

    available_views = tuple(view for view in allowed_views if views.get(view))
    if not available_views and views["equation"]:
        available_views = ("equation",)

    selected_view = ui_state.get("selected_view")
    if selected_view not in available_views:
        selected_view = available_views[0] if available_views else "equation"

    answer_fields = problem.answer_fields or [{"name": "user_answer", "label": "Answer", "type": "text"}]
    return {
        "prompt": problem.prompt,
        "questionPrompt": problem.prompt,
        "views": views,
        "availableViews": available_views,
        "selectedView": selected_view,
        "answerFields": answer_fields,
        "answerInputType": "fields" if len(answer_fields) > 1 else "single",
        "answerPlaceholder": "type answer",
        "supportsText": views["equation"] is not None,
        "hasTextView": views["equation"] is not None,
        "supportsGraph": views["graph"] is not None,
        "hasGraphView": views["graph"] is not None,
        "supportsTable": False,
        "hasTableView": False,
    }


def render_problem_view(presentation):
    selected_view = presentation["selectedView"]
    view = presentation["views"].get(selected_view) or presentation["views"].get("equation")
    if not view:
        return "", ""
    if view["type"] == "graph":
        graph = render_graph(view["graph"], show_caption=False)
        return view["promptHtml"], graph
    return view["html"], ""


def format_duration(seconds):
    try:
        total = max(0, int(seconds))
    except (TypeError, ValueError):
        total = 0
    minutes = total // 60
    remainder = total % 60
    return f"{minutes:02d}:{remainder:02d}"


def short_unit_label(label):
    return re.sub(r"^Unit \d+:\s*", "", label)


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


def page_context(state, units, generators, valid_topic_for_unit, count_value):
    unit = state.get("unit", "unit1")
    if unit not in units:
        unit = "unit1"

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
    active_question_view = state.get("active_question_view", "equation")
    question_view_options = question_view_options_for_topic(topic)
    available_question_views = tuple(value for value, _label in question_view_options)
    question_view_selections = {
        view: state.get(f"question_view_{view}") == "true"
        for view in available_question_views
    }
    problem_config_selections = selected_topic_config_values(state, topic)
    ui_mode = state.get("ui_mode", "practice")
    test_total = max(1, count_value(state, "test_total") or 10)
    test_index = max(1, count_value(state, "test_index") or 1)
    test_correct = count_value(state, "test_correct")
    test_incorrect = count_value(state, "test_incorrect")
    test_skipped = count_value(state, "test_skipped")
    test_hints = count_value(state, "test_hints")
    test_elapsed = count_value(state, "test_elapsed")
    test_timer_mode = state.get("test_timer_mode", "stopwatch")
    if test_timer_mode not in ("stopwatch", "countdown"):
        test_timer_mode = "stopwatch"
    test_time_limit = max(1, count_value(state, "test_time_limit") or 30)
    raw_test_topics = state.get("test_topics", ())
    if isinstance(raw_test_topics, str):
        raw_test_topics = (raw_test_topics,)
    test_topics = tuple(value for value in raw_test_topics if "|" in value) or (f"{unit}|{topic}",)
    test_breakdown = state.get("test_breakdown", "{}")

    if problem is None:
        selected_question_views = tuple(
            view for view, selected in question_view_selections.items() if selected
        ) or default_question_view_values(topic)
        presentation = active_question_view if active_question_view in selected_question_views else selected_question_views[0]
        problem = generators[topic](
            "easy",
            {
                "topic_config": problem_config_selections,
                "questionViews": (presentation,),
            },
        )

    problem_presentation = get_problem_presentation(
        problem,
        {
            "available_views": available_question_views,
            "selected_view": active_question_view,
        },
    )
    active_question_view = problem_presentation["selectedView"]

    return {
        "unit": unit,
        "topic": topic,
        "problem": problem,
        "problem_presentation": problem_presentation,
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
        "active_question_view": active_question_view,
        "question_view_options": question_view_options,
        "question_view_selections": question_view_selections,
        "problem_config_selections": problem_config_selections,
        "ui_mode": ui_mode,
        "test_total": test_total,
        "test_index": test_index,
        "test_correct": test_correct,
        "test_incorrect": test_incorrect,
        "test_skipped": test_skipped,
        "test_hints": test_hints,
        "test_elapsed": test_elapsed,
        "test_timer_mode": test_timer_mode,
        "test_time_limit": test_time_limit,
        "test_topics": test_topics,
        "test_breakdown": test_breakdown,
        "auth_user": state.get("auth_user"),
    }


def render_control_panel(context, units):
    unit = context["unit"]
    topic = context["topic"]
    unit_options = tuple((value, data["label"]) for value, data in units.items())
    topic_options = tuple(units[unit]["topics"])
    unit_dropdown = custom_dropdown("unit", "Unit", unit_options, unit, unit_option_attrs(units))
    topic_dropdown = custom_dropdown("topic", "Topic", topic_options, topic)
    question_view_controls = render_question_view_controls(context)
    problem_config_controls = render_problem_config_controls(context)

    auth_profile = profile_menu(context["auth_user"]) if context.get("auth_user") else ""

    return f"""      <aside class="sidebar-shell">
      <form class="control-panel" action="/generate" method="get">
        <div class="sidebar-brand">
          <div class="brand-mark">M</div>
          <span>MathPracAI</span>
        </div>
        <input type="hidden" name="ui_mode" value="practice">
        <input type="hidden" name="correct_count" value="{context["correct_count"]}">
        <input type="hidden" name="hint_count" value="{context["hint_count"]}">
        <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
        <input type="hidden" name="skip_count" value="{context["skip_count"]}">
        {unit_dropdown}
        {topic_dropdown}
        {problem_config_controls}
        {question_view_controls}
      </form>
      <div class="sidebar-footer">
        <button class="secondary-action" type="button" data-open-test-modal>Start Test</button>
        {auth_profile}
      </div>
      </aside>"""


def render_problem_config_controls(context):
    sections = topic_config_sections(context["topic"])
    if not sections:
        return ""

    selections = context["problem_config_selections"]
    rendered_sections = []
    for section in sections:
        key = section["key"]
        controls = []
        selected_values = selections.get(key, default_topic_config_values(section))
        for value, label in section["options"]:
            checked = " checked" if value in selected_values else ""
            controls.append(
                f"""<label class="config-checkbox-option">
              <input type="checkbox" name="{escape(key)}" value="{escape(value)}" data-config-checkbox{checked}>
              <span>{escape(label)}</span>
            </label>"""
            )

        rendered_sections.append(
            f"""<fieldset class="config-checkbox-group" data-config-checkbox-group>
          <legend>{escape(section["label"])}</legend>
          {''.join(controls)}
        </fieldset>"""
        )

    return f"""        <div class="config-checkbox-stack">
          {''.join(rendered_sections)}
        </div>"""


def render_question_view_controls(context):
    options = context["question_view_options"]
    if len(options) <= 1:
        return ""

    selections = context["question_view_selections"]
    controls = []
    for value, label in options:
        checked = " checked" if selections.get(value) else ""
        controls.append(
            f"""<label class="question-view-option">
              <input type="checkbox" name="question_view_{escape(value)}" value="true" data-question-view="{escape(value)}"{checked}>
              <span>{escape(label)}</span>
            </label>"""
        )

    return f"""        <fieldset class="question-view-group" data-question-view-group>
          <legend>Question View</legend>
          {''.join(controls)}
        </fieldset>"""


def unit_option_attrs(units):
    def attrs(value, _label, _index):
        return f"data-topics='{escape(json.dumps(units[value]['topics']))}'"

    return attrs


def render_problem_config_hidden_inputs(context):
    hidden_inputs = []
    for key, values in context["problem_config_selections"].items():
        for value in values:
            hidden_inputs.append(
                f'<input type="hidden" name="{escape(key)}" value="{escape(value)}">'
            )
    return "\n          ".join(hidden_inputs)


def render_answer_form(context):
    unit = context["unit"]
    topic = context["topic"]
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]
    answered = context["answered"]
    generated = context["generated"]
    correct_checked = context["feedback_type"] == "correct"
    hint_disabled = " disabled" if hint_visible or solution_visible or correct_checked else ""
    solution_disabled = " disabled" if solution_visible or correct_checked else ""
    skip_disabled = " disabled" if solution_visible or correct_checked else ""
    primary_action = "next" if correct_checked or solution_visible else "check"
    primary_label = "Next Problem" if primary_action == "next" else "Check"
    if context["ui_mode"] == "test_progress":
        primary_action = "next" if answered else "check"
        primary_label = "Next Question" if primary_action == "next" else "Check Answer"
        if primary_action == "next" and context["test_index"] >= context["test_total"]:
            primary_label = "Finish Test"
    elif primary_action == "check":
        primary_label = "Check Answer"
    answer_controls = render_answer_controls(context["problem_presentation"])
    problem_config_inputs = render_problem_config_hidden_inputs(context)
    test_hidden_inputs = render_test_hidden_inputs(context)
    test_mode = context["ui_mode"] == "test_progress"
    practice_actions = "" if test_mode else f"""
            <button class="btn btn-ghost" name="action" value="hint" type="submit"{hint_disabled}>Hint</button>
            <button class="btn btn-ghost" name="action" value="skip" type="submit"{skip_disabled}>Skip</button>
            <button class="btn btn-ghost" name="action" value="solution" type="submit"{solution_disabled}>Solution</button>"""
    test_actions = (
        f'<button class="btn btn-ghost" name="action" value="skip" type="submit"{skip_disabled}>Skip</button>'
        if test_mode and not answered
        else ""
    )

    return f"""        <form class="answer-panel" action="/check" method="post">
          <input type="hidden" name="unit" value="{escape(unit)}">
          <input type="hidden" name="topic" value="{escape(topic)}">
          <input type="hidden" name="problem_json" value="{encoded_problem(problem)}">
          <input type="hidden" name="hint_visible" value="{str(hint_visible).lower()}">
          <input type="hidden" name="solution_visible" value="{str(solution_visible).lower()}">
          <input type="hidden" name="answered" value="{str(answered).lower()}">
          <input type="hidden" name="correct_count" value="{context["correct_count"]}">
          <input type="hidden" name="hint_count" value="{context["hint_count"]}">
          <input type="hidden" name="incorrect_count" value="{context["incorrect_count"]}">
          <input type="hidden" name="skip_count" value="{context["skip_count"]}">
          <input type="hidden" name="generated" value="{str(generated).lower()}">
          <input type="hidden" name="question_view_equation" value="{str(context["question_view_selections"].get("equation", False)).lower()}">
          <input type="hidden" name="question_view_graph" value="{str(context["question_view_selections"].get("graph", False)).lower()}">
          <input type="hidden" name="active_question_view" value="{escape(context["active_question_view"])}">
          {test_hidden_inputs}
          {problem_config_inputs}
          <div class="answer-card">
            {answer_controls}
            {render_inline_feedback(context)}
            {render_help_stack(context) if not test_mode else ""}
            <div class="utility-row">
              <div class="secondary-actions">
                {practice_actions}
                {test_actions}
              </div>
              <button class="btn btn-accent" name="action" value="{primary_action}" type="submit">{primary_label}</button>
            </div>
          </div>
        </form>"""


def render_test_hidden_inputs(context):
    topic_inputs = "\n          ".join(
        f'<input type="hidden" name="test_topics" value="{escape(value)}">'
        for value in context["test_topics"]
    )
    return f"""
          <input type="hidden" name="ui_mode" value="{escape(context["ui_mode"])}">
          <input type="hidden" name="test_total" value="{context["test_total"]}">
          <input type="hidden" name="test_index" value="{context["test_index"]}">
          <input type="hidden" name="test_correct" value="{context["test_correct"]}">
          <input type="hidden" name="test_incorrect" value="{context["test_incorrect"]}">
          <input type="hidden" name="test_skipped" value="{context["test_skipped"]}">
          <input type="hidden" name="test_hints" value="{context["test_hints"]}">
          <input type="hidden" name="test_elapsed" value="{context["test_elapsed"]}" data-test-elapsed-input>
          <input type="hidden" name="test_timer_mode" value="{escape(context["test_timer_mode"])}">
          <input type="hidden" name="test_time_limit" value="{context["test_time_limit"]}">
          <input type="hidden" name="test_breakdown" value="{escape(context["test_breakdown"])}">
          {topic_inputs}"""


def render_answer_controls(presentation):
    fields = presentation["answerFields"]
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
    return f"""<div class="answer-input-shell">
                  <input id="{escape(field_id)}" name="{escape(field_name)}" type="{escape(field.get("type", "text"))}" autocomplete="off" placeholder="type answer">
                  {helper_buttons}
                </div>"""


def render_answer_helpers(helpers):
    if not helpers:
        return ""
    buttons = "".join(
        f'<button type="button" data-answer-helper="{escape(str(helper))}">{escape(str(helper))}</button>'
        for helper in helpers
    )
    return f'<div class="answer-helper-row">{buttons}</div>'


def render_inline_feedback(context):
    if context["feedback_type"] == "empty":
        return ""
    return f"""        <div class="feedback {escape(context["feedback_type"])}">{escape(context["feedback"])}</div>"""


def render_feedback(context):
    return f"""        <div class="feedback {escape(context["feedback_type"])}">{escape(context["feedback"])}</div>"""


def render_help_stack(context):
    problem = context["problem"]
    hint_visible = context["hint_visible"]
    solution_visible = context["solution_visible"]
    hint_html = f'<div class="help-box hint-box">{render_math_text(problem.hint)}</div>' if hint_visible else ""
    solution_text = f"{problem.solution} Answer: {problem.answer}"
    solution_html = f'<div class="help-box solution-box">{render_math_text(solution_text)}</div>' if solution_visible else ""

    return f"""        <div class="help-stack">
          {hint_html}
          {solution_html}
        </div>"""


def render_stats(context):
    return f"""        <div class="stats-panel" aria-label="Practice stats">
          <span class="stat-correct">Correct: {context["correct_count"]}</span>
          <span class="stat-hints">Hints: {context["hint_count"]}</span>
          <span class="stat-incorrect">Incorrect: {context["incorrect_count"]}</span>
          <span class="stat-skips">Skips: {context["skip_count"]}</span>
        </div>"""


def render_breadcrumb(context, unit_label, topic_label):
    unit = short_unit_label(unit_label(context["unit"]))
    topic = topic_label(context["topic"])
    return f"""        <nav class="breadcrumb" aria-label="Current practice path">
          <span>Algebra 2</span>
          <span>{escape(unit)}</span>
          <span>{escape(topic)}</span>
        </nav>"""


def render_problem_panel(context, unit_label, topic_label):
    answer_form = render_answer_form(context)
    stats = render_stats(context)
    question_html, graph = render_problem_view(context["problem_presentation"])
    view_class = "graph-view" if graph else "text-view"

    return f"""      <section class="problem-panel" aria-live="polite">
        {render_breadcrumb(context, unit_label, topic_label)}
        <div class="problem-stack">
          <div class="question-card {view_class}">
            <h1>{question_html}</h1>
            {graph}
          </div>
          {answer_form}
          {stats}
        </div>
      </section>"""


def render_test_top_bar(context):
    progress = min(100, max(0, (context["test_index"] / context["test_total"]) * 100))
    return f"""      <header class="test-top-bar" data-test-timer data-timer-mode="{escape(context["test_timer_mode"])}" data-time-limit="{context["test_time_limit"]}" data-initial-elapsed="{context["test_elapsed"]}">
        <div class="test-brand">
          <div class="brand-mark small">M</div>
          <span>MathPracAI</span>
        </div>
        <div class="test-progress-label">Question <strong>{context["test_index"]}</strong> <span>/ {context["test_total"]}</span></div>
        <div class="test-progress-track"><div style="width: {progress:.2f}%"></div></div>
        <div class="test-timer"><span aria-hidden="true">◷</span><strong data-test-time>{format_duration(context["test_elapsed"])}</strong></div>
        <div class="test-score">
          <span class="score-ok">✓ {context["test_correct"]}</span>
          <span class="score-bad">× {context["test_incorrect"]}</span>
        </div>
      </header>"""


def render_test_progress_page(context, unit_label, topic_label):
    question_html, graph = render_problem_view(context["problem_presentation"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MathPracAI Test</title>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js" defer></script>
</head>
<body>
  <main class="test-screen">
{render_test_top_bar(context)}
    <section class="test-workspace">
      {render_breadcrumb(context, unit_label, topic_label)}
      <div class="problem-stack">
        <div class="question-card {'graph-view' if graph else 'text-view'}">
          <h1>{question_html}</h1>
          {graph}
        </div>
        {render_answer_form(context)}
      </div>
    </section>
    <form class="exit-test-form" action="/generate" method="get">
      <input type="hidden" name="unit" value="{escape(context["unit"])}">
      <input type="hidden" name="topic" value="{escape(context["topic"])}">
      <input type="hidden" name="ui_mode" value="practice">
      <button class="exit-test" type="submit">Exit Test</button>
    </form>
  </main>
</body>
</html>"""


def result_grade(accuracy):
    if accuracy >= 90:
        return "Excellent", "grade-excellent"
    if accuracy >= 75:
        return "Good", "grade-good"
    if accuracy >= 60:
        return "Fair", "grade-fair"
    return "Needs Work", "grade-needs-work"


def topic_parts(value):
    if "|" not in value:
        return "unit1", "evaluating_functions"
    return value.split("|", 1)


def decoded_test_breakdown(context):
    try:
        value = json.loads(context.get("test_breakdown", "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        value = {}
    return value if isinstance(value, dict) else {}


def render_test_topic_hidden_inputs(context):
    return "\n          ".join(
        f'<input type="hidden" name="test_topics" value="{escape(value)}">'
        for value in context["test_topics"]
    )


def render_topic_breakdown_rows(context, unit_label, topic_label):
    breakdown = decoded_test_breakdown(context)
    rows = []
    topic_values = tuple(breakdown.keys()) or context["test_topics"]
    for value in topic_values:
        unit, topic = topic_parts(value)
        data = breakdown.get(value, {}) if isinstance(breakdown.get(value, {}), dict) else {}
        correct = int(data.get("correct", 0))
        incorrect = int(data.get("incorrect", 0))
        skipped = int(data.get("skipped", 0))
        total = max(1, correct + incorrect + skipped)
        pct = round((correct / total) * 100)
        rows.append(
            f"""        <div class="topic-row">
          <div>
            <span>{escape(unit_label(unit))}</span>
            <strong>{escape(topic_label(topic))}</strong>
          </div>
          <div class="topic-meter"><div style="width: {pct}%"></div></div>
          <span>{correct}/{total}</span>
        </div>"""
        )
    return "\n".join(rows)


def render_test_results_page(context, unit_label, topic_label):
    total_attempted = context["test_correct"] + context["test_incorrect"] + context["test_skipped"]
    total = max(context["test_total"], total_attempted, 1)
    accuracy = round((context["test_correct"] / total) * 100)
    grade_label, grade_class = result_grade(accuracy)
    topic_inputs = render_test_topic_hidden_inputs(context)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MathPracAI Test Results</title>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js" defer></script>
</head>
<body>
  <main class="results-screen">
    <header class="results-top-bar">
      <div class="test-brand"><div class="brand-mark small">M</div><span>MathPracAI</span></div>
      <span>Test Results</span>
    </header>
    <section class="results-content">
      <div class="results-hero">
        <div class="complete-pill">Test Complete</div>
        <p class="result-percent {grade_class}">{accuracy}%</p>
        <p class="result-grade {grade_class}">{grade_label}</p>
        <p>{context["test_correct"]} of {total} questions answered correctly</p>
      </div>
      <div class="results-grid primary-results">
        <div><span>Score</span><strong>{context["test_correct"]}/{total}</strong></div>
        <div><span>Accuracy</span><strong>{accuracy}%</strong></div>
        <div><span>Time Taken</span><strong>{format_duration(context["test_elapsed"])}</strong></div>
        <div><span>Hints Used</span><strong>{context["test_hints"]}</strong></div>
      </div>
      <div class="results-grid secondary-results">
        <div><span>Correct</span><strong class="score-ok">{context["test_correct"]}</strong></div>
        <div><span>Incorrect</span><strong class="score-bad">{context["test_incorrect"]}</strong></div>
        <div><span>Skipped</span><strong>{context["test_skipped"]}</strong></div>
      </div>
      <section class="topic-breakdown">
        <h2>Topic Breakdown</h2>
{render_topic_breakdown_rows(context, unit_label, topic_label)}
      </section>
      <div class="results-actions">
        <form action="/generate" method="get">
          <input type="hidden" name="unit" value="{escape(context["unit"])}">
          <input type="hidden" name="topic" value="{escape(context["topic"])}">
          <input type="hidden" name="ui_mode" value="practice">
          <button class="btn btn-secondary" type="submit">Back to Practice</button>
        </form>
        <form action="/generate" method="get">
          <input type="hidden" name="unit" value="{escape(context["unit"])}">
          <input type="hidden" name="topic" value="{escape(context["topic"])}">
          <input type="hidden" name="ui_mode" value="test_progress">
          <input type="hidden" name="test_total" value="{context["test_total"]}">
          <input type="hidden" name="test_index" value="1">
          <input type="hidden" name="test_timer_mode" value="{escape(context["test_timer_mode"])}">
          <input type="hidden" name="test_time_limit" value="{context["test_time_limit"]}">
          <input type="hidden" name="test_breakdown" value="{{}}">
          {topic_inputs}
          <button class="btn btn-accent" type="submit">Retake Test</button>
        </form>
      </div>
    </section>
  </main>
</body>
</html>"""


def render_test_setup_modal(context, units):
    config_inputs = render_problem_config_hidden_inputs(context)
    topic_inputs = render_test_topic_hidden_inputs(context)
    selected_topic_chips = render_selected_test_topic_chips(context, units)
    topic_picker = render_test_topic_picker(units)
    return f"""      <div class="test-modal" data-test-modal aria-hidden="true">
        <div class="test-modal-backdrop" data-close-test-modal></div>
        <form class="test-dialog" action="/generate" method="get" role="dialog" aria-modal="true" aria-labelledby="test-dialog-title">
          <div class="dialog-header">
            <div>
              <h2 id="test-dialog-title">Start Test</h2>
              <p>Configure your test settings</p>
            </div>
            <button type="button" class="icon-button" data-close-test-modal aria-label="Close test setup">×</button>
          </div>
          <input type="hidden" name="ui_mode" value="test_progress">
          <input type="hidden" name="unit" value="{escape(context["unit"])}" data-test-primary-unit>
          <input type="hidden" name="topic" value="{escape(context["topic"])}" data-test-primary-topic>
          <input type="hidden" name="test_index" value="1">
          <input type="hidden" name="test_correct" value="0">
          <input type="hidden" name="test_incorrect" value="0">
          <input type="hidden" name="test_skipped" value="0">
          <input type="hidden" name="test_hints" value="0">
          <input type="hidden" name="test_elapsed" value="0">
          <input type="hidden" name="test_breakdown" value="{{}}">
          <input type="hidden" name="question_view_equation" value="{str(context["question_view_selections"].get("equation", False)).lower()}">
          <input type="hidden" name="question_view_graph" value="{str(context["question_view_selections"].get("graph", False)).lower()}">
          <div data-test-topic-inputs>
            {topic_inputs}
          </div>
          {config_inputs}
          <div class="dialog-body">
            <section class="modal-field">
              <span>Selected Topics</span>
              <div class="selected-topic-row" data-selected-test-topics>
                {selected_topic_chips}
                {topic_picker}
              </div>
            </section>
            <label class="modal-field">Number of Questions
              <input type="number" name="test_total" min="1" max="100" value="10">
            </label>
            <div class="modal-field">
              <span>Timer Mode</span>
              <div class="timer-choice-row">
                <label class="timer-option"><input type="radio" name="test_timer_mode" value="stopwatch" checked> Timer</label>
                <label class="timer-option"><input type="radio" name="test_timer_mode" value="countdown"> Time Limit</label>
              </div>
            </div>
            <label class="modal-field time-limit-field" data-time-limit-field hidden>Time Limit (minutes)
              <input type="number" name="test_time_limit" min="1" value="30">
            </label>
          </div>
          <div class="dialog-actions">
            <button class="btn btn-secondary" type="button" data-close-test-modal>Cancel</button>
            <button class="btn btn-accent" type="submit">Start Test</button>
          </div>
        </form>
      </div>"""


def render_selected_test_topic_chips(context, units):
    chips = []
    for value in context["test_topics"]:
        unit, topic = topic_parts(value)
        if unit not in units:
            continue
        label = next((topic_label for topic_value, topic_label in units[unit]["topics"] if topic_value == topic), topic)
        chips.append(
            f"""<span class="selected-topic-chip" data-test-topic-chip data-value="{escape(value)}">
                  {escape(label)}
                  <button type="button" data-remove-test-topic aria-label="Remove {escape(label)}">×</button>
                </span>"""
        )
    return "".join(chips)


def render_test_topic_picker(units):
    unit_buttons = []
    topic_panels = []
    for unit, data in units.items():
        unit_buttons.append(
            f"""<button type="button" class="topic-picker-option" data-topic-picker-unit="{escape(unit)}">
                <span>{escape(data["label"])}</span><span aria-hidden="true">›</span>
              </button>"""
        )
        topic_buttons = "".join(
            f"""<button type="button" class="topic-picker-option" data-topic-picker-topic="{escape(topic)}" data-unit="{escape(unit)}" data-label="{escape(label)}">
                  <span>{escape(label)}</span><span class="already-added" aria-hidden="true">✓</span>
                </button>"""
            for topic, label in data["topics"]
        )
        topic_panels.append(
            f"""<div class="topic-picker-panel" data-topic-picker-panel="{escape(unit)}">
              {topic_buttons}
            </div>"""
        )

    return f"""<div class="topic-picker" data-topic-picker>
              <button type="button" class="topic-picker-trigger" data-topic-picker-trigger aria-label="Add topic">+</button>
              <div class="topic-picker-menu" data-topic-picker-menu hidden>
                <div class="topic-picker-header">
                  <button type="button" data-topic-picker-back hidden>‹</button>
                  <span data-topic-picker-title>Select a unit</span>
                </div>
                <div class="topic-picker-step" data-topic-picker-units>
                  {''.join(unit_buttons)}
                </div>
                {''.join(topic_panels)}
              </div>
            </div>"""


def render_page(state, units, generators, unit_label, topic_label, valid_topic_for_unit, count_value):
    context = page_context(state, units, generators, valid_topic_for_unit, count_value)
    if context["ui_mode"] == "test_progress":
        return render_test_progress_page(context, unit_label, topic_label)
    if context["ui_mode"] == "test_results":
        return render_test_results_page(context, unit_label, topic_label)

    control_panel = render_control_panel(context, units)
    problem_panel = render_problem_panel(context, unit_label, topic_label)
    test_modal = render_test_setup_modal(context, units)

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
{test_modal}
  </main>
</body>
</html>"""
