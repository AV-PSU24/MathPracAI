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

  if (fieldName === "topic") {
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

    submitPracticeConfig(group);
  });
});

document.querySelectorAll("[data-config-checkbox-group]").forEach((group) => {
  group.addEventListener("change", (event) => {
    if (!event.target.matches("[data-config-checkbox]")) {
      return;
    }

    const checkboxes = Array.from(group.querySelectorAll("[data-config-checkbox]"));
    if (!checkboxes.some((checkbox) => checkbox.checked)) {
      event.target.checked = true;
      return;
    }

    submitPracticeConfig(group);
  });
});

function replaceHiddenFieldValues(form, fieldName, values) {
  Array.from(form.elements).forEach((element) => {
    if (element.type === "hidden" && element.name === fieldName) {
      element.remove();
    }
  });

  values.forEach((value) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = fieldName;
    input.value = value;
    form.appendChild(input);
  });
}

function syncConfigCheckboxesToForm(form) {
  document.querySelectorAll("[data-config-checkbox-group]").forEach((group) => {
    const checkboxes = Array.from(group.querySelectorAll("[data-config-checkbox]"));
    if (!checkboxes.length) {
      return;
    }

    const fieldName = checkboxes[0].name;
    const values = checkboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value);
    replaceHiddenFieldValues(form, fieldName, values);
  });
}

document.querySelectorAll(".answer-panel").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const action = event.submitter?.value;
    if (action !== "skip" && action !== "next") {
      return;
    }

    document.querySelectorAll("[data-question-view]").forEach((checkbox) => {
      form
        .querySelectorAll(`input[type="hidden"][name="${checkbox.name}"]`)
        .forEach((input) => {
          input.value = checkbox.checked ? "true" : "";
        });
    });

    syncConfigCheckboxesToForm(form);
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

const testModal = document.querySelector("[data-test-modal]");

function openTestModal() {
  if (!testModal) {
    return;
  }
  testModal.classList.add("is-open");
  testModal.setAttribute("aria-hidden", "false");
  testModal.querySelector("select, input, button")?.focus();
}

function closeTestModal() {
  if (!testModal) {
    return;
  }
  testModal.classList.remove("is-open");
  testModal.setAttribute("aria-hidden", "true");
}

function selectedTestTopicValues() {
  return Array.from(document.querySelectorAll('[data-test-topic-inputs] input[name="test_topics"]'))
    .map((input) => input.value);
}

function syncPrimaryTestTopic() {
  const first = selectedTestTopicValues()[0];
  const unitInput = document.querySelector("[data-test-primary-unit]");
  const topicInput = document.querySelector("[data-test-primary-topic]");
  if (!first || !unitInput || !topicInput) {
    return;
  }
  const [unit, topic] = first.split("|");
  unitInput.value = unit;
  topicInput.value = topic;
}

function addTestTopicInput(value) {
  const holder = document.querySelector("[data-test-topic-inputs]");
  if (!holder || selectedTestTopicValues().includes(value)) {
    return;
  }
  const input = document.createElement("input");
  input.type = "hidden";
  input.name = "test_topics";
  input.value = value;
  holder.appendChild(input);
}

function removeTestTopicInput(value) {
  const inputs = Array.from(document.querySelectorAll('[data-test-topic-inputs] input[name="test_topics"]'));
  if (inputs.length <= 1) {
    return;
  }
  inputs.forEach((input) => {
    if (input.value === value) {
      input.remove();
    }
  });
}

function updateTopicPickerAddedStates() {
  const selected = new Set(selectedTestTopicValues());
  document.querySelectorAll("[data-topic-picker-topic]").forEach((button) => {
    const value = `${button.dataset.unit}|${button.dataset.topicPickerTopic}`;
    button.classList.toggle("is-added", selected.has(value));
  });
}

function closeTopicPicker(picker) {
  const menu = picker?.querySelector("[data-topic-picker-menu]");
  const units = picker?.querySelector("[data-topic-picker-units]");
  const back = picker?.querySelector("[data-topic-picker-back]");
  const title = picker?.querySelector("[data-topic-picker-title]");
  if (!menu || !units || !back || !title) {
    return;
  }
  menu.hidden = true;
  menu.classList.remove("align-right", "drop-up");
  units.hidden = false;
  back.hidden = true;
  title.textContent = "Select a unit";
  picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
    panel.classList.remove("is-active");
  });
}

function positionTopicPickerMenu(picker) {
  const menu = picker?.querySelector("[data-topic-picker-menu]");
  const dialog = picker?.closest(".test-dialog");
  if (!menu || !dialog || menu.hidden) {
    return;
  }

  menu.classList.remove("align-right", "drop-up");
  const dialogRect = dialog.getBoundingClientRect();
  let menuRect = menu.getBoundingClientRect();

  if (menuRect.right > dialogRect.right - 12) {
    menu.classList.add("align-right");
    menuRect = menu.getBoundingClientRect();
  }

  if (menuRect.left < dialogRect.left + 12) {
    menu.classList.remove("align-right");
    menuRect = menu.getBoundingClientRect();
  }

  if (menuRect.bottom > dialogRect.bottom - 12) {
    menu.classList.add("drop-up");
  }
}

function initializeTopicPicker() {
  document.querySelectorAll("[data-topic-picker]").forEach((picker) => {
    const trigger = picker.querySelector("[data-topic-picker-trigger]");
    const menu = picker.querySelector("[data-topic-picker-menu]");
    const units = picker.querySelector("[data-topic-picker-units]");
    const back = picker.querySelector("[data-topic-picker-back]");
    const title = picker.querySelector("[data-topic-picker-title]");
    if (!trigger || !menu || !units || !back || !title) {
      return;
    }

    trigger.addEventListener("click", () => {
      const nextOpen = menu.hidden;
      document.querySelectorAll("[data-topic-picker]").forEach(closeTopicPicker);
      menu.hidden = !nextOpen;
      updateTopicPickerAddedStates();
      positionTopicPickerMenu(picker);
    });

    picker.querySelectorAll("[data-topic-picker-unit]").forEach((button) => {
      button.addEventListener("click", () => {
        units.hidden = true;
        back.hidden = false;
        title.textContent = button.textContent.trim().replace(/^Unit \\d+:\\s*/, "");
        picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
          panel.classList.toggle("is-active", panel.dataset.topicPickerPanel === button.dataset.topicPickerUnit);
        });
        positionTopicPickerMenu(picker);
      });
    });

    back.addEventListener("click", () => {
      units.hidden = false;
      back.hidden = true;
      title.textContent = "Select a unit";
      picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
        panel.classList.remove("is-active");
      });
      positionTopicPickerMenu(picker);
    });

    picker.querySelectorAll("[data-topic-picker-topic]").forEach((button) => {
      button.addEventListener("click", () => {
        const value = `${button.dataset.unit}|${button.dataset.topicPickerTopic}`;
        addTestTopicInput(value);
        const chip = document.createElement("span");
        chip.className = "selected-topic-chip";
        chip.dataset.testTopicChip = "";
        chip.dataset.value = value;
        chip.innerHTML = `${button.dataset.label}<button type="button" data-remove-test-topic aria-label="Remove ${button.dataset.label}">×</button>`;
        picker.parentElement.insertBefore(chip, picker);
        syncPrimaryTestTopic();
        updateTopicPickerAddedStates();
        closeTopicPicker(picker);
      });
    });
  });
}

document.addEventListener("click", (event) => {
  if (event.target.matches("[data-remove-test-topic]")) {
    const chip = event.target.closest("[data-test-topic-chip]");
    if (chip && selectedTestTopicValues().length > 1) {
      removeTestTopicInput(chip.dataset.value);
      chip.remove();
      syncPrimaryTestTopic();
      updateTopicPickerAddedStates();
    }
    return;
  }

  document.querySelectorAll("[data-topic-picker]").forEach((picker) => {
    if (!picker.contains(event.target)) {
      closeTopicPicker(picker);
    }
  });
});

function updateTimerModeUI() {
  const checked = document.querySelector('input[name="test_timer_mode"]:checked');
  const timeLimitField = document.querySelector("[data-time-limit-field]");
  document.querySelectorAll(".timer-option").forEach((label) => {
    const input = label.querySelector('input[name="test_timer_mode"]');
    label.classList.toggle("is-selected", input?.checked);
  });
  if (timeLimitField && checked) {
    timeLimitField.hidden = checked.value !== "countdown";
  }
}

document.querySelectorAll('input[name="test_timer_mode"]').forEach((input) => {
  input.addEventListener("change", updateTimerModeUI);
});

document.querySelectorAll("[data-open-test-modal]").forEach((button) => {
  button.addEventListener("click", openTestModal);
});

document.querySelectorAll("[data-close-test-modal]").forEach((button) => {
  button.addEventListener("click", closeTestModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeTestModal();
  }
});

function formatTimer(seconds) {
  const safeSeconds = Math.max(0, seconds);
  const minutes = String(Math.floor(safeSeconds / 60)).padStart(2, "0");
  const remainder = String(safeSeconds % 60).padStart(2, "0");
  return `${minutes}:${remainder}`;
}

const testTimer = document.querySelector("[data-test-timer]");
let currentElapsed = Number(testTimer?.dataset.initialElapsed || "0");

function syncElapsedInputs() {
  document.querySelectorAll("[data-test-elapsed-input]").forEach((input) => {
    input.value = String(currentElapsed);
  });
}

if (testTimer) {
  const output = document.querySelector("[data-test-time]");
  const mode = testTimer.dataset.timerMode || "stopwatch";
  const limitMinutes = Number(testTimer.dataset.timeLimit || "30");

  syncElapsedInputs();
  window.setInterval(() => {
    currentElapsed += 1;
    const remaining = Math.max(0, limitMinutes * 60 - currentElapsed);
    if (output) {
      output.textContent = formatTimer(mode === "countdown" ? remaining : currentElapsed);
    }
    syncElapsedInputs();
  }, 1000);
}

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", syncElapsedInputs);
});

initializeTopicPicker();
updateTopicPickerAddedStates();
syncPrimaryTestTopic();
updateTimerModeUI();

document.querySelectorAll("[data-profile-menu]").forEach((menu) => {
  const trigger = menu.querySelector("[data-profile-trigger]");
  const dropdown = menu.querySelector("[data-profile-dropdown]");
  if (!trigger || !dropdown) {
    return;
  }

  trigger.addEventListener("click", () => {
    const willOpen = dropdown.hidden;
    document.querySelectorAll("[data-profile-dropdown]").forEach((other) => {
      other.hidden = true;
    });
    dropdown.hidden = !willOpen;
  });

  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) {
      dropdown.hidden = true;
    }
  });
});

document.querySelectorAll(".code-input").forEach((input) => {
  input.addEventListener("input", () => {
    input.value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6);
  });
});

function openCodeModal(type) {
  const modal = document.querySelector(`[data-code-modal="${type}"]`);
  if (!modal) {
    return;
  }
  modal.hidden = false;
  modal.querySelector("input, button")?.focus();
}

function closeCodeModal(modal) {
  if (!modal) {
    return;
  }
  modal.hidden = true;
}

document.querySelectorAll("[data-open-code-modal]").forEach((button) => {
  button.addEventListener("click", () => openCodeModal(button.dataset.openCodeModal));
});

document.querySelectorAll("[data-close-code-modal]").forEach((button) => {
  button.addEventListener("click", () => closeCodeModal(button.closest("[data-code-modal]")));
});

document.querySelectorAll("[data-code-modal]").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target.matches(".code-modal-backdrop")) {
      closeCodeModal(modal);
    }
  });
});

document.querySelectorAll("[data-code-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const generateButton = form.querySelector("[data-generate-code]");
    const errorBox = form.querySelector("[data-code-error]");
    const codeBox = form.querySelector("[data-generated-code-box]");
    const codeValue = form.querySelector("[data-generated-code]");
    const copyButton = form.querySelector("[data-copy-code]");

    if (errorBox) {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }
    if (generateButton) {
      generateButton.disabled = true;
      generateButton.textContent = "Generating...";
    }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Unable to generate code.");
      }
      if (codeValue) {
        codeValue.textContent = data.code;
      }
      if (codeBox) {
        codeBox.hidden = false;
      }
      if (copyButton) {
        copyButton.hidden = false;
        copyButton.textContent = "Copy";
      }
      if (generateButton) {
        generateButton.textContent = "Regenerate";
      }
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      }
      if (generateButton) {
        generateButton.textContent = "Generate";
      }
    } finally {
      if (generateButton) {
        generateButton.disabled = false;
      }
    }
  });
});

document.querySelectorAll("[data-copy-code]").forEach((button) => {
  button.addEventListener("click", async () => {
    const dialog = button.closest("[data-code-modal]");
    const code = dialog?.querySelector("[data-generated-code]")?.textContent?.trim();
    if (!code) {
      return;
    }
    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1600);
    } catch (_error) {
      button.textContent = code;
    }
  });
});
