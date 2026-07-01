def signed(value):
    return f"- {abs(value)}" if value < 0 else f"+ {value}"


def signed_spaced(value):
    return f" - {abs(value)}" if value < 0 else f" + {value}"


def superscript_number(value):
    digits = str(value)
    superscripts = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    return digits.translate(superscripts)


def polynomial_term(coefficient, exponent, is_first):
    sign = "-" if coefficient < 0 else "+"
    absolute = abs(coefficient)

    if exponent == 0:
        body = str(absolute)
    elif exponent == 1:
        body = "x" if absolute == 1 else f"{absolute}x"
    else:
        body = f"x{superscript_number(exponent)}" if absolute == 1 else f"{absolute}x{superscript_number(exponent)}"

    if is_first:
        return f"-{body}" if sign == "-" else body
    return f" {sign} {body}"


def format_function_equation(coefficients):
    degree = len(coefficients) - 1
    terms = []
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        terms.append(polynomial_term(coefficient, degree - index, not terms))
    return f"f(x) = {''.join(terms) if terms else '0'}"


def format_function_substitution(coefficients, x):
    degree = len(coefficients) - 1
    pieces = []
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        if coefficient == 0:
            continue

        absolute = abs(coefficient)
        if exponent == 0:
            body = str(absolute)
        elif exponent == 1:
            body = f"{absolute}({x})"
        else:
            body = f"{absolute}({x}){superscript_number(exponent)}"

        if not pieces:
            pieces.append(f"-{body}" if coefficient < 0 else body)
        else:
            pieces.append(f" {'-' if coefficient < 0 else '+'} {body}")
    return "".join(pieces) if pieces else "0"


def format_linear_equation(function_data):
    m = function_data["m"]
    b = function_data["b"]
    if m == 1:
        slope = "x"
    elif m == -1:
        slope = "-x"
    else:
        slope = f"{m}x"
    return f"f(x) = {slope}{signed_spaced(b)}" if b else f"f(x) = {slope}"


def format_quadratic_vertex_equation(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    coefficient = "" if a == 1 else "-" if a == -1 else str(a)
    return f"f(x) = {coefficient}(x{signed_spaced(-h)})²{signed_spaced(k)}" if k else f"f(x) = {coefficient}(x{signed_spaced(-h)})²"


def format_absolute_value_equation(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    coefficient = "" if a == 1 else "-" if a == -1 else str(a)
    return f"f(x) = {coefficient}|x{signed_spaced(-h)}|{signed_spaced(k)}" if k else f"f(x) = {coefficient}|x{signed_spaced(-h)}|"


def format_square_root_equation(function_data):
    a = function_data["a"]
    h = function_data["h"]
    k = function_data["k"]
    coefficient = "" if a == 1 else "-" if a == -1 else str(a)
    return f"f(x) = {coefficient}sqrt(x{signed_spaced(-h)}){signed_spaced(k)}" if k else f"f(x) = {coefficient}sqrt(x{signed_spaced(-h)})"
