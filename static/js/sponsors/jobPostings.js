// Add/remove rows for the sponsor job postings field (apps/sponsors/job_postings.py).
// Without JavaScript the form still works: saving always renders one extra blank row.
(function () {
  "use strict";

  const PART_LABELS = { title: "title", location: "location", url: "link" };

  function setUp(container) {
    const body = container.querySelector("[data-job-postings-rows]");
    const template = container.querySelector("template[data-job-postings-template]");
    const addButton = container.querySelector("[data-job-postings-add]");
    const baseId = container.dataset.jobPostingsId;

    function rows() {
      return body.querySelectorAll("[data-job-postings-row]");
    }

    function renumber() {
      rows().forEach(function (row, index) {
        const number = index + 1;
        row.querySelector("[data-job-postings-number]").textContent = number;
        row.querySelectorAll("[data-job-postings-input]").forEach(function (input) {
          const part = input.dataset.jobPostingsInput;
          if (baseId) {
            input.id = baseId + "_" + index + "_" + part;
          }
          input.setAttribute("aria-label", "Job " + number + " " + PART_LABELS[part]);
        });
        const removeButton = row.querySelector("[data-job-postings-remove]");
        removeButton.setAttribute("aria-label", "Remove job " + number);
        removeButton.hidden = false;
      });
    }

    addButton.addEventListener("click", function () {
      const row = template.content.querySelector("[data-job-postings-row]").cloneNode(true);
      body.appendChild(row);
      renumber();
      row.querySelector("[data-job-postings-input]").focus();
    });

    body.addEventListener("click", function (event) {
      const removeButton = event.target.closest("[data-job-postings-remove]");
      if (!removeButton) {
        return;
      }
      const row = removeButton.closest("[data-job-postings-row]");
      if (rows().length > 1) {
        row.remove();
      } else {
        row.querySelectorAll("[data-job-postings-input]").forEach(function (input) {
          input.value = "";
        });
      }
      renumber();
      addButton.focus();
    });

    addButton.hidden = false;
    renumber();
  }

  function setUpAll() {
    document.querySelectorAll("[data-job-postings]").forEach(setUp);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setUpAll);
  } else {
    setUpAll();
  }
})();
