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

  document.querySelectorAll("[data-generate-button]").forEach((button) => {
    button.disabled = false;
  });

  closeDropdown(dropdown);
  trigger.focus();
}

function moveFocus(dropdown, direction) {
  const options = Array.from(dropdown.querySelectorAll(".custom-option"));
  const currentIndex = options.indexOf(document.activeElement);
  const nextIndex = currentIndex === -1
    ? 0
    : (currentIndex + direction + options.length) % options.length;

  options[nextIndex].focus();
}

dropdowns.forEach((dropdown) => {
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const options = dropdown.querySelectorAll(".custom-option");

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
});

document.addEventListener("click", (event) => {
  dropdowns.forEach((dropdown) => {
    if (!dropdown.contains(event.target)) {
      closeDropdown(dropdown);
    }
  });
});
