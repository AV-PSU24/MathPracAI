from services.ai_tutor.models import PromptComponent


def build_context_components(session):
    components = []
    lesson_context = build_lesson_context(session)
    attempt_context = build_attempt_context(session)
    conversation_context = build_conversation_context(session)
    student_message_context = build_student_message_context(session)

    if lesson_context:
        components.append(PromptComponent("Lesson Context", lesson_context))
    if attempt_context:
        components.append(PromptComponent("Attempt Context", attempt_context))
    if conversation_context:
        components.append(PromptComponent("Conversation Context", conversation_context))
    components.append(PromptComponent("Current Student Message", student_message_context))
    return components


def build_lesson_context(session):
    lines = [section_title("CURRENT LESSON")]
    if session.unit:
        lines.extend(label_block("Unit", session.unit))
    if session.topic:
        lines.extend(label_block("Topic", session.topic))
    if session.problem:
        lines.extend(problem_lines(session.problem))
    return "\n".join(lines)


def build_attempt_context(session):
    lines = [section_title("PREVIOUS SUBMISSIONS")]
    lines.extend(label_block("Attempt Count", str(session.attempt_count)))
    lines.extend(label_block("Solution Unlocked", str(session.solution_unlocked)))
    lines.extend(label_block("Help Status", session.help_status))
    if session.attempts:
        for index, attempt in enumerate(session.attempts, 1):
            if index > 1:
                lines.append("")
            lines.append(f"Attempt {index}")
            lines.extend(attempt_lines(attempt))
    else:
        lines.extend(label_block("Submissions", "No previous submissions."))
    return "\n".join(lines)


def build_conversation_context(session):
    if not session.chat_history:
        return ""
    lines = [section_title("CURRENT CONVERSATION")]
    for turn in session.chat_history[-6:]:
        role = display_role(turn.get("role"))
        message = first_present(turn, "message", "content", "text")
        if message:
            lines.extend(label_block(role, str(message)))
    return "\n".join(lines)


def build_student_message_context(session):
    return "\n".join([section_title("CURRENT STUDENT MESSAGE"), session.student_message])


def section_title(title):
    return f"=========================\n{title}\n========================="


def label_block(label, value):
    return [f"{label}:", str(value)]


def problem_lines(problem):
    lines = []
    prompt = first_present(problem, "prompt", "question", "display_prompt")
    graph = first_present(problem, "graphSummary", "graph_summary", "graph")
    answer_type = first_present(problem, "answerType", "answer_type")
    equation = first_present(problem, "equation", "display_equation")

    if prompt:
        lines.extend(label_block("Problem", prompt))
    if equation:
        lines.extend(label_block("Equation", equation))
    if graph:
        lines.extend(label_block("Graph", graph))
    if answer_type:
        lines.extend(label_block("Answer Type", answer_type))

    omitted_keys = {"prompt", "question", "display_prompt", "graphSummary", "graph_summary", "graph", "answerType", "answer_type", "equation", "display_equation"}
    extra_lines = readable_mapping({key: value for key, value in problem.items() if key not in omitted_keys}, indent="")
    if extra_lines:
        lines.append("Additional Problem Data:")
        lines.extend(extra_lines)
    return lines


def attempt_lines(attempt):
    lines = []
    response = first_present(attempt, "studentResponse", "student_response", "response", "answer", "value")
    result = first_present(attempt, "applicationResult", "application_result", "result")
    feedback = first_present(attempt, "feedback", "message")

    if response:
        lines.extend(label_block("Student Response", response))
    else:
        answer_parts = {
            key: value
            for key, value in attempt.items()
            if key not in {"correct", "feedback", "message", "applicationResult", "application_result", "result"}
        }
        if answer_parts:
            lines.append("Student Response:")
            lines.extend(readable_mapping(answer_parts, indent="- "))

    if result:
        lines.extend(label_block("Application Result", result))
    elif "correct" in attempt:
        lines.extend(label_block("Application Result", "Correct" if attempt.get("correct") else "Incorrect"))

    if feedback:
        lines.extend(label_block("Feedback", feedback))
    return lines


def readable_mapping(value, indent=""):
    lines = []
    for key, item in value.items():
        if isinstance(item, dict):
            lines.append(f"{indent}{key}:")
            lines.extend(readable_mapping(item, indent=f"{indent}  "))
        elif isinstance(item, list):
            lines.append(f"{indent}{key}:")
            lines.extend(readable_list(item, indent=f"{indent}  "))
        else:
            lines.append(f"{indent}{key}: {item}")
    return lines


def readable_list(value, indent=""):
    lines = []
    for index, item in enumerate(value, 1):
        if isinstance(item, dict):
            lines.append(f"{indent}{index}.")
            lines.extend(readable_mapping(item, indent=f"{indent}  "))
        else:
            lines.append(f"{indent}{index}. {item}")
    return lines


def first_present(mapping, *keys):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def display_role(role):
    role = str(role or "").strip().lower()
    if role in ("assistant", "milo", "ai"):
        return "Milo"
    if role == "student":
        return "Student"
    if role:
        return role.title()
    return "Message"
