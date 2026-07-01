const dropdowns = document.querySelectorAll("[data-dropdown]");

function closeDropdown(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");

  dropdown.classList.remove("is-open");
  trigger.setAttribute("aria-expanded", "false");
}

function closeOtherDropdowns(currentDropdown) {
  dropdowns.forEach((dropdown) => {
    if (dropdown !== currentDropdown) {
      closeDropdown(dropdown);
    }
  });
}

function openDropdown(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const selectedOption = dropdown.querySelector('.custom-option[aria-selected="true"]');

  closeOtherDropdowns(dropdown);
  dropdown.classList.add("is-open");
  trigger.setAttribute("aria-expanded", "true");

  if (selectedOption) {
    selectedOption.focus();
  }
}

function toggleDropdown(dropdown) {
  if (dropdown.classList.contains("is-open")) {
    closeDropdown(dropdown);
  } else {
    openDropdown(dropdown);
  }
}

function selectOption(dropdown, option) {
  const hiddenInput = dropdown.querySelector('input[type="hidden"]');
  const selectedLabel = dropdown.querySelector("[data-selected-label]");
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const options = dropdown.querySelectorAll(".custom-option");
  const fieldName = hiddenInput.name;
  const labelText = option.textContent.trim();

  options.forEach((item) => item.setAttribute("aria-selected", "false"));
  option.setAttribute("aria-selected", "true");
  hiddenInput.value = option.dataset.value;
  selectedLabel.textContent = labelText;

  document.querySelectorAll(`input[name="${fieldName}"]`).forEach((input) => {
    input.value = option.dataset.value;
  });

  document.querySelectorAll(`[data-badge="${fieldName}"]`).forEach((badge) => {
    badge.textContent = labelText;
  });

  closeDropdown(dropdown);
  trigger.focus();

  if (fieldName === "unit") {
    updateTopicsForUnit(option);
    return;
  }

  if (fieldName === "topic" || fieldName === "difficulty") {
    submitPracticeConfig(dropdown);
  }
}

function submitPracticeConfig(dropdown) {
  const form = dropdown.closest("form");
  if (form) {
    form.submit();
  }
}

function updateTopicsForUnit(unitOption) {
  const form = unitOption.closest("form");
  const topicDropdown = form?.querySelector('[data-dropdown] input[name="topic"]')?.closest("[data-dropdown]");
  if (!topicDropdown || !unitOption.dataset.topics) {
    return;
  }

  const topics = JSON.parse(unitOption.dataset.topics);
  const topicHiddenInput = topicDropdown.querySelector('input[type="hidden"]');
  const topicSelectedLabel = topicDropdown.querySelector("[data-selected-label]");
  const topicOptions = topicDropdown.querySelector(".custom-options");

  topicOptions.innerHTML = topics.map(([value, label], index) => `
            <button
              class="custom-option"
              id="topic-option-${index}"
              role="option"
              type="button"
              data-value="${value}"
              aria-selected="${index === 0 ? "true" : "false"}"
              tabindex="-1"
            >${label}</button>`).join("");

  topicHiddenInput.value = topics[0][0];
  topicSelectedLabel.textContent = topics[0][1];

  document.querySelectorAll('input[name="topic"]').forEach((input) => {
    input.value = topics[0][0];
  });

  document.querySelectorAll('[data-badge="topic"]').forEach((badge) => {
    badge.textContent = topics[0][1];
  });

  bindDropdownOptions(topicDropdown);
  selectOption(topicDropdown, topicOptions.querySelector(".custom-option"));
}

function moveFocus(dropdown, direction) {
  const options = Array.from(dropdown.querySelectorAll(".custom-option"));
  const currentIndex = options.indexOf(document.activeElement);
  const nextIndex = currentIndex === -1
    ? 0
    : (currentIndex + direction + options.length) % options.length;

  options[nextIndex].focus();
}

function bindDropdownOptions(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const options = dropdown.querySelectorAll(".custom-option");

  options.forEach((option) => {
    option.addEventListener("click", () => {
      selectOption(dropdown, option);
    });

    option.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectOption(dropdown, option);
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveFocus(dropdown, 1);
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();
        moveFocus(dropdown, -1);
      }

      if (event.key === "Escape") {
        closeDropdown(dropdown);
        trigger.focus();
      }
    });
  });
}

dropdowns.forEach((dropdown) => {
  const trigger = dropdown.querySelector(".custom-select-trigger");

  trigger.addEventListener("click", () => {
    toggleDropdown(dropdown);
  });

  trigger.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleDropdown(dropdown);
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      openDropdown(dropdown);
    }

    if (event.key === "Escape") {
      closeDropdown(dropdown);
    }
  });

  bindDropdownOptions(dropdown);
});

document.addEventListener("click", (event) => {
  dropdowns.forEach((dropdown) => {
    if (!dropdown.contains(event.target)) {
      closeDropdown(dropdown);
    }
  });
});

document.querySelectorAll("[data-question-view-group]").forEach((group) => {
  group.addEventListener("change", (event) => {
    if (!event.target.matches("[data-question-view]")) {
      return;
    }

    const checkboxes = Array.from(group.querySelectorAll("[data-question-view]"));
    if (!checkboxes.some((checkbox) => checkbox.checked)) {
      event.target.checked = true;
      return;
    }

    const form = group.closest("form");
    if (form) {
      form.submit();
    }
  });
});

let currentAnswerInput = null;

document.addEventListener("focusin", (event) => {
  if (event.target.matches(".answer-panel input[type='text']")) {
    currentAnswerInput = event.target;
  }
});

function insertAtCursor(input, value) {
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;

  input.value = `${input.value.slice(0, start)}${value}${input.value.slice(end)}`;
  input.focus();
  input.setSelectionRange(start + value.length, start + value.length);
}

document.querySelectorAll("[data-answer-helper]").forEach((button) => {
  button.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });

  button.addEventListener("click", () => {
    const input = button.closest(".answer-field")?.querySelector("input[type='text']")
      || currentAnswerInput
      || button.closest(".answer-row")?.querySelector("input[type='text']");
    if (input) {
      insertAtCursor(input, button.dataset.answerHelper);
    }
  });
});
