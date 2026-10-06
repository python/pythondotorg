// Package builder: focused screens retain the native form and its selections, and the summary is
// rebuilt from the form itself, then priced by the server's quote endpoint.
(() => {
  "use strict";

  const form = document.getElementById("order-form");
  if (!form || !form.classList.contains("package-builder")) return;
  form.classList.add("is-enhanced");

  const $$ = (selector, root = form) => [...root.querySelectorAll(selector)];
  const conditions = JSON.parse(document.getElementById("order-parameter-conditions")?.textContent || "{}");

  const summary = document.getElementById("package-summary");
  const summaryTitle = document.getElementById("summary-title");
  const body = document.getElementById("pb-summary-body");
  const totals = document.getElementById("pb-totals");
  const status = document.getElementById("pb-quote-status");
  const announcer = document.getElementById("pb-announce");
  const attest = document.getElementById("discount-attest");
  const bar = document.getElementById("pb-bar");
  const barTotal = document.getElementById("pb-bar-total");
  const agreementsEmpty = document.getElementById("pb-agreements-empty");

  const families = $$("[data-family]").map((el) => {
    const extraGroup = document.getElementById(`extras-${el.dataset.family}`);
    return {
      el,
      slug: el.dataset.family,
      name: el.dataset.familyName,
      title: el.dataset.familyTitle,
      include: el.querySelector(".pb-include-input"),
      radios: $$(".pb-tier-input", el),
      extraGroup,
      extras: extraGroup ? $$(".pb-extra", extraGroup) : [],
    };
  });

  const extraBox = (row) => row.querySelector(".pb-extra-toggle input[type='checkbox']");
  const extraName = (row) => row.querySelector(".pb-extra-name").textContent.trim();
  const tierOf = (family) => family.radios.find((radio) => radio.checked) || null;
  const tierColumn = (radio) => radio.closest(".pb-tier");
  const included = () => families.filter((family) => family.include.checked && tierOf(family));
  const familyOf = (node) => {
    const group = node.closest("[data-family], [data-extras-for]");
    return group && families.find((family) => family.slug === (group.dataset.family || group.dataset.extrasFor));
  };

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function announce(message) {
    // Clearing first makes repeated identical messages audible.
    announcer.textContent = "";
    window.setTimeout(() => {
      announcer.textContent = message;
    }, 60);
  }

  // ---------- Selection state ----------

  // A family is in the package exactly when its checkbox is checked and one tier is chosen. Removing
  // a family unchecks its tier but remembers it, so adding it back restores every earlier choice.
  function ensureTier(family) {
    if (tierOf(family)) return;
    const key = family.el.dataset.lastTier || family.el.dataset.defaultTier;
    const radio = family.radios.find((candidate) => candidate.value === key) || family.radios[0];
    if (radio) radio.checked = true;
  }

  function setIncluded(family, on) {
    family.include.checked = on;
    if (on) {
      ensureTier(family);
      return;
    }
    const current = tierOf(family);
    if (current) {
      family.el.dataset.lastTier = current.value;
      current.checked = false;
    }
  }

  function paramKind(field) {
    if (field.tagName === "TEXTAREA") return "lines";
    if (field.tagName === "SELECT") return "choice";
    return field.type === "number" ? "count" : "text";
  }

  function syncParams(family, row, active) {
    const fields = $$("[data-param-key]", row);
    if (!fields.length) return;
    const byKey = Object.fromEntries(fields.map((field) => [field.dataset.paramKey, field]));
    const rules = conditions[family.slug]?.[row.dataset.addon] || {};
    const memo = {};
    // Mirror the server: a condition holds only when the parameter it depends on is itself submitted.
    const applies = (key, seen = new Set()) => {
      if (key in memo) return memo[key];
      if (seen.has(key)) return false;
      seen.add(key);
      memo[key] = Object.entries(rules[key] || {}).every(
        ([dependency, value]) =>
          byKey[dependency] && applies(dependency, seen) && byKey[dependency].value === String(value),
      );
      return memo[key];
    };
    fields.forEach((field) => {
      const applicable = applies(field.dataset.paramKey);
      field.closest(".pb-param").hidden = !applicable;
      field.disabled = !active || !applicable;
    });
    const params = row.querySelector(".pb-params");
    if (params) params.hidden = !active;
  }

  function syncFamily(family) {
    const on = family.include.checked;
    const tier = on ? tierOf(family) : null;
    family.el.classList.toggle("is-included", Boolean(on && tier));
    if (family.extraGroup) family.extraGroup.hidden = !tier;
    family.extras.forEach((row) => {
      const box = extraBox(row);
      const includedIn = (row.dataset.includedIn || "").split(" ").filter(Boolean);
      const withTier = Boolean(tier) && includedIn.includes(tier.value);
      box.disabled = !tier || withTier;
      row.classList.toggle("is-included", withTier);
      row.classList.toggle("is-selected", on && box.checked && !withTier);
      row.classList.toggle("is-kept", !on && box.checked);
      const now = row.querySelector(".pb-extra-now");
      if (now) {
        now.hidden = !withTier;
        if (withTier) now.querySelector(".pb-extra-now-tier").textContent = tierColumn(tier).dataset.tierName;
      }
      syncParams(family, row, Boolean(tier) && box.checked && !withTier);
    });
  }

  function syncDiscount() {
    if (!attest) return;
    const needed = form.querySelector("input[name='discount']:checked")?.dataset.attestation === "true";
    attest.hidden = !needed;
    attest.querySelectorAll("input").forEach((input) => {
      input.disabled = !needed;
    });
  }

  function syncAgreements() {
    const chosen = new Set(included().map((family) => family.slug));
    $$("[data-agreement-for]").forEach((item) => {
      item.hidden = !chosen.has(item.dataset.agreementFor);
    });
    if (agreementsEmpty) agreementsEmpty.hidden = chosen.size > 0;
  }

  function syncAll() {
    families.forEach(syncFamily);
    syncDiscount();
    syncAgreements();
    const extrasEmpty = document.getElementById("pb-extras-empty");
    if (extrasEmpty) extrasEmpty.hidden = included().some((family) => family.extras.length);
  }

  // ---------- Contacts ----------

  function setupContacts() {
    const rows = $$(".pb-contact");
    const button = document.getElementById("add-contact");
    if (!button || !rows.length) return;
    const used = (row) => $$("input", row).some((input) => input.value.trim()) || row.querySelector(".errorlist");
    let visible = Math.max(1, ...rows.map((row, index) => (used(row) ? index + 1 : 0)));
    const render = () => {
      rows.forEach((row, index) => {
        row.hidden = index >= visible;
      });
      button.hidden = visible >= rows.length;
    };
    button.addEventListener("click", () => {
      visible = Math.min(rows.length, visible + 1);
      render();
      rows[visible - 1].querySelector("input")?.focus();
    });
    render();
    return (target) => {
      const index = rows.findIndex((row) => row.contains(target));
      if (index < visible) return;
      visible = index + 1;
      render();
    };
  }

  // ---------- Steps and in-page navigation ----------

  function setupSteps(revealContact) {
    const steps = ["services", "extras", "term", "organization", "contacts"];
    const names = ["Services", "Extras", "Term", "Organization", "Contacts & billing"];
    const panels = $$("[data-step-panel]");
    const navigation = form.querySelector(".pb-steps");
    const progress = document.getElementById("pb-progress-text");
    const actions = document.getElementById("pb-wizard-actions");
    const back = actions.querySelector("[data-step-back]");
    const forward = actions.querySelector("[data-step-next]");
    const errors = document.getElementById("pb-errors");
    const panelFor = (step) => panels.find((panel) => panel.dataset.stepPanel === step);
    const currentIndex = () => steps.indexOf(form.dataset.step);

    function focusTarget(target) {
      const heading = target.matches("section, aside, fieldset")
        ? target.querySelector("h2, h3, legend")
        : null;
      const focus = heading || target;
      if (!focus.matches("a[href], button, input, select, textarea, summary, [tabindex]")) {
        focus.tabIndex = -1;
      }
      focus.focus({ preventScroll: true });
      requestAnimationFrame(() => {
        (target.matches("[data-step-panel]") ? navigation : focus).scrollIntoView({ block: "start", behavior: "instant" });
      });
    }

    function showStep(step) {
      const panel = panelFor(step);
      if (!panel) return;
      const index = steps.indexOf(step);
      form.dataset.step = step;
      panels.forEach((candidate) => {
        candidate.hidden = candidate !== panel;
      });
      $$("[data-step-go]", navigation).forEach((button) => {
        if (button.dataset.stepGo === step) button.setAttribute("aria-current", "step");
        else button.removeAttribute("aria-current");
      });
      const current = navigation.querySelector('[aria-current="step"]');
      if (current.offsetLeft < navigation.scrollLeft || current.offsetLeft + current.offsetWidth > navigation.scrollLeft + navigation.clientWidth) {
        navigation.scrollLeft = current.offsetLeft;
      }
      progress.textContent = `Step ${index + 1} of ${steps.length} — ${names[index]}`;
      back.hidden = index === 0;
      back.textContent = `Back to ${names[index - 1]?.toLowerCase() || "services"}`;
      forward.type = step === "contacts" ? "submit" : "button";
      forward.textContent = step === "contacts" ? "Continue to review" : `Continue to ${names[index + 1].toLowerCase()}`;
    }

    function openDisclosures(target) {
      let disclosure = target.closest("details");
      while (disclosure) {
        disclosure.open = true;
        disclosure = disclosure.parentElement?.closest("details");
      }
    }

    function revealTarget(target, focus = true) {
      // An old extras link must not silently add a service that has since been removed.
      const extraGroup = target.closest("[data-extras-for]");
      const family = extraGroup && familyOf(extraGroup);
      if (family && (!family.include.checked || !tierOf(family))) target = family.el;
      const panel = target.closest("[data-step-panel]");
      if (panel) showStep(panel.dataset.stepPanel);
      openDisclosures(target);
      revealContact?.(target);
      if (focus) focusTarget(target);
    }

    function hashTarget(hash) {
      if (!hash || hash === "#") return null;
      try {
        const target = document.getElementById(decodeURIComponent(hash.slice(1)));
        return target && form.contains(target) ? target : null;
      } catch {
        return null;
      }
    }

    function navigate(target) {
      const hash = `#${encodeURIComponent(target.id)}`;
      if (window.location.hash !== hash) window.history.pushState(null, "", hash);
      revealTarget(target);
    }

    function packageReady() {
      const unresolved = families.find((family) => family.include.checked && !tierOf(family));
      if (!unresolved && included().length) return true;
      const message = unresolved
        ? `Choose a tier for ${unresolved.name} before continuing.`
        : "Choose at least one service tier before continuing.";
      state.failure = message;
      render();
      const family = unresolved || families[0];
      const target = family?.radios[0] || family?.include || panelFor("services");
      revealTarget(target);
      announce(message);
      return false;
    }

    function validFields(root) {
      const invalid = $$("input, select, textarea", root)
        .find((field) => field.willValidate && !field.validity.valid);
      if (!invalid) return true;
      revealTarget(invalid);
      invalid.reportValidity();
      return false;
    }

    function goToStep(step) {
      const index = steps.indexOf(step);
      if (index < 0) return;
      if (index > 0 && !packageReady()) return;
      if (index > currentIndex() && !validFields(panelFor(form.dataset.step))) return;
      navigate(panelFor(step));
    }

    function advance() {
      const index = currentIndex();
      if (index < steps.length - 1) goToStep(steps[index + 1]);
    }

    navigation.hidden = false;
    progress.hidden = false;
    actions.hidden = false;
    // Validate one revealed field at a time, rather than letting the browser focus hidden screens.
    form.noValidate = true;
    $$("[data-step-go]", navigation).forEach((button) => {
      button.addEventListener("click", () => goToStep(button.dataset.stepGo));
    });
    back.addEventListener("click", () => goToStep(steps[currentIndex() - 1]));
    forward.addEventListener("click", (event) => {
      if (forward.type !== "submit") {
        event.preventDefault();
        advance();
      }
    });
    $$("[data-choose-family][data-choose-tier]").forEach((button) => {
      button.hidden = false;
      button.addEventListener("click", () => {
        const family = families.find((candidate) => candidate.slug === button.dataset.chooseFamily);
        const radio = family?.radios.find((candidate) => candidate.value === button.dataset.chooseTier);
        if (!radio) return;
        radio.checked = true;
        family.include.checked = true;
        syncAll();
        refresh(0);
        announce(`${family.name} added at the ${tierColumn(radio).dataset.tierName} tier.`);
      });
    });

    document.addEventListener("click", (event) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target.closest("a[href]");
      if (!link || link.hasAttribute("download") || (link.target && link.target !== "_self")) return;
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin || url.pathname !== window.location.pathname || url.search !== window.location.search) return;
      const target = hashTarget(url.hash);
      if (!target) return;
      event.preventDefault();
      navigate(target);
    });

    window.addEventListener("hashchange", () => {
      revealTarget(hashTarget(window.location.hash) || panelFor("services"));
    });

    form.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || event.isComposing || event.defaultPrevented || form.dataset.step === "contacts") return;
      if (!event.target.matches("input:not([type='button']):not([type='submit']):not([type='reset'])")) return;
      event.preventDefault();
      advance();
    });
    form.addEventListener("submit", (event) => {
      if (form.dataset.step !== "contacts") {
        event.preventDefault();
        advance();
      } else if (!packageReady() || !validFields(form)) {
        event.preventDefault();
      }
    });

    form.addEventListener("invalid", (event) => {
      revealTarget(event.target, false);
    }, true);

    $$(".errorlist, [aria-invalid='true']").forEach(openDisclosures);
    const firstError = errors && $$("a[href^='#']", errors)
      .map((link) => hashTarget(link.hash))
      .find(Boolean);
    const initialTarget = firstError || hashTarget(window.location.hash);
    showStep("services");
    if (initialTarget) revealTarget(initialTarget, !errors);
    errors?.focus();
  }

  // ---------- Money ----------

  // Exact cent arithmetic on the server's decimal strings; only used to split recurring from one-time.
  function cents(value) {
    const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(String(value ?? "").trim());
    if (!match) return 0n;
    const fraction = (match[3] || "").padEnd(3, "0");
    let amount = BigInt(match[2]) * 100n + BigInt(fraction.slice(0, 2));
    if (Number(fraction[2]) >= 5) amount += 1n;
    return match[1] ? -amount : amount;
  }

  function formatCents(amount) {
    const negative = amount < 0n;
    const absolute = negative ? -amount : amount;
    const whole = (absolute / 100n).toLocaleString("en-US");
    const fraction = absolute % 100n;
    const text = fraction ? `$${whole}.${String(fraction).padStart(2, "0")}` : `$${whole}`;
    return negative ? `−${text}` : text;
  }

  // ---------- Quote ----------

  // Free text never leaves the page: lines and text parameters are replaced by neutral placeholders
  // that price identically (pricing only counts lines and checks that text is present).
  function quoteValue(field) {
    const kind = paramKind(field);
    if (kind === "lines") {
      return field.value
        .split(/\r?\n/)
        .filter((line) => line.trim())
        .map(() => "-")
        .join("\n");
    }
    if (kind === "text") return field.value.trim() ? "-" : "";
    return field.value;
  }

  function quoteParams(chosen) {
    const params = new URLSearchParams();
    chosen.forEach((family) => params.append(family.include.name, family.slug));
    const discount = form.querySelector("input[name='discount']:checked");
    if (discount) params.set(discount.name, discount.value);
    chosen.forEach((family) => {
      const tier = tierOf(family);
      params.append(tier.name, tier.value);
      family.extras.forEach((row) => {
        const box = extraBox(row);
        if (!box.checked || box.disabled) return;
        params.append(box.name, "on");
        $$("[data-param-key]", row).forEach((field) => {
          if (!field.disabled) params.append(field.name, quoteValue(field));
        });
      });
    });
    if (form.dataset.order) params.set("order", form.dataset.order);
    return params;
  }

  function fieldLabel(slug, fieldName) {
    const field = form.querySelector(`[name="${CSS.escape(`${slug}-${fieldName}`)}"]`);
    const row = field?.closest(".pb-extra");
    if (!row) return "";
    const param = field.closest(".pb-param")?.querySelector("label")?.textContent.trim();
    return param ? `${extraName(row)}, ${param}` : extraName(row);
  }

  function quoteProblems(payload) {
    const problems = [];
    Object.entries(payload?.errors || {}).forEach(([slug, value]) => {
      const family = families.find((candidate) => candidate.slug === slug);
      const prefix = family ? `${family.name}: ` : "";
      if (Array.isArray(value)) {
        value.forEach((message) => problems.push(prefix + (typeof message === "string" ? message : message.message)));
        return;
      }
      Object.entries(value || {}).forEach(([field, errors]) => {
        const label = field === "__all__" ? "" : fieldLabel(slug, field);
        errors.forEach(({ message }) => {
          const text = label && !message.startsWith(label.split(",")[0]) ? `${label}: ${message}` : message;
          problems.push(prefix + text);
        });
      });
    });
    return problems;
  }

  const state = { quote: null, pending: false, problems: [], failure: "", announced: "" };
  let timer;
  let controller;
  let generation = 0;

  function refresh(delay = 180) {
    window.clearTimeout(timer);
    controller?.abort();
    const current = ++generation;
    const chosen = included();
    state.problems = [];
    state.failure = "";
    const unresolved = families.filter((family) => family.include.checked && !tierOf(family));
    if (unresolved.length) {
      state.quote = null;
      state.pending = false;
      state.failure = `Choose a tier for ${unresolved.map((family) => family.name).join(", ")} to calculate the complete package.`;
      render();
      return;
    }
    if (!chosen.length) {
      state.quote = null;
      state.pending = false;
      render();
      return;
    }
    state.quote = null;
    state.pending = true;
    render();
    timer = window.setTimeout(async () => {
      controller = new AbortController();
      try {
        const response = await fetch(`${form.dataset.quoteUrl}?${quoteParams(chosen)}`, {
          signal: controller.signal,
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        });
        const payload = await response.json().catch(() => null);
        if (current !== generation) return;
        if (response.ok && payload) {
          state.quote = payload;
        } else {
          state.quote = null;
          state.problems = response.status === 400 ? quoteProblems(payload) : [];
          if (!state.problems.length) {
            state.failure = "Prices are unavailable right now. You can still continue; the next page shows every fee.";
          }
        }
      } catch (error) {
        if (error.name === "AbortError" || current !== generation) return;
        state.quote = null;
        state.failure = "We couldn't reach the price calculator. Check your connection; you can still continue.";
      }
      state.pending = false;
      render();
    }, delay);
  }

  // ---------- Summary ----------

  function amountNode(text, unit, className = "") {
    const cell = el("span", `pb-amount ${className}`.trim());
    if (text === null) {
      cell.append(el("span", "pb-skeleton"));
      cell.setAttribute("aria-label", "Calculating");
      return cell;
    }
    cell.append(el("span", "pb-amount-value", text));
    if (unit) cell.append(el("span", "pb-amount-unit", ` ${unit}`));
    return cell;
  }

  function line(label, amount, { detail = "", className = "" } = {}) {
    const item = el("li", `pb-line ${className}`.trim());
    const name = el("span", "pb-line-name", label);
    if (detail) name.append(el("span", "pb-line-detail", detail));
    item.append(name, amount);
    return item;
  }

  // The summary repeats what the customer chose, in their own words, without sending them anywhere.
  function localDetail(row) {
    return $$("[data-param-key]", row)
      .filter((field) => !field.disabled)
      .map((field) => {
        const label = field.closest(".pb-param").querySelector("label").textContent.trim();
        const kind = paramKind(field);
        let value = field.value.trim();
        if (kind === "choice") value = field.selectedOptions[0]?.textContent.trim() || value;
        if (kind === "lines") value = field.value.split(/\r?\n/).map((part) => part.trim()).filter(Boolean).join(", ");
        return value ? `${label}: ${value}` : "";
      })
      .filter(Boolean);
  }

  function itemDetail(row, item) {
    const labels = $$(".pb-param label", row).map((label) => `${label.textContent.trim()}: `);
    const fromRule = (item?.detail || "")
      .split("; ")
      .filter((part) => part && part !== "Included at this service tier" && !labels.some((label) => part.startsWith(label)));
    return [...fromRule, ...localDetail(row)].join(" · ");
  }

  function renderFamily(family, quoted) {
    const tier = tierOf(family);
    const column = tierColumn(tier);
    const group = el("section", "pb-sum-family");
    group.setAttribute("aria-label", family.name);
    const head = el("div", "pb-sum-head");
    head.append(el("h3", "pb-sum-name", family.name));
    const actions = el("span", "pb-sum-actions");
    const change = el("a", "pb-sum-change", "Change");
    change.href = `#family-${family.slug}`;
    change.setAttribute("aria-label", `Change ${family.name}`);
    change.dataset.focusKey = `change-${family.slug}`;
    const remove = el("button", "pb-linkbutton", "Remove");
    remove.type = "button";
    remove.dataset.remove = family.slug;
    remove.dataset.focusKey = `remove-${family.slug}`;
    remove.setAttribute("aria-label", `Remove ${family.name} from your package`);
    actions.append(change, remove);
    head.append(actions);
    group.append(head);

    const list = el("ul", "pb-lines");
    list.append(
      line(`${column.dataset.tierName} tier`, amountNode(quoted?.display.tier_fee || column.dataset.fee, "a year"), {
        className: "pb-line-tier",
      }),
    );

    const priced = [...(quoted?.items || [])];
    family.extras.forEach((row) => {
      if (row.classList.contains("is-included")) {
        list.append(line(extraName(row), amountNode("Included", ""), { className: "pb-line-included" }));
      }
    });
    family.extras.forEach((row) => {
      const box = extraBox(row);
      if (!box.checked || box.disabled) return;
      const name = extraName(row);
      const index = priced.findIndex((item) => item.name === name);
      const item = index >= 0 ? priced.splice(index, 1)[0] : null;
      let amount;
      if (!item) amount = amountNode(state.problems.length || state.failure ? "—" : null, "");
      else if (item.amount === null) amount = amountNode(item.display, "", "is-unpriced");
      else amount = amountNode(item.display, item.basis === "per year" ? "a year" : item.basis);
      list.append(line(name, amount, { detail: itemDetail(row, item) }));
    });

    if (quoted && Number(quoted.discount_percent) > 0) {
      list.append(
        line(`${quoted.discount_name}, ${quoted.discount_percent}% off the tier`, amountNode(`−${quoted.display.discount_amount}`, "a year"), {
          className: "pb-line-discount",
        }),
      );
    }
    group.append(list);
    return group;
  }

  function renderTotals(chosen) {
    const quote = state.quote;
    totals.replaceChildren();
    totals.hidden = !chosen.length;
    if (!chosen.length) return "";
    const rows = el("dl", "pb-total-rows");
    const add = (label, value, className = "") => {
      const row = el("div", `pb-total ${className}`.trim());
      row.append(el("dt", "", label), el("dd", "num", value));
      rows.append(row);
    };
    if (!quote) {
      const waiting = state.pending ? "Calculating…" : "—";
      add("Total", waiting, "pb-total-grand");
      totals.append(rows);
      return "";
    }
    let recurring = 0n;
    let oneTime = 0n;
    const unpriced = [];
    quote.agreements.forEach((agreement) => {
      recurring += cents(agreement.tier_fee) - cents(agreement.discount_amount);
      agreement.items.forEach((item) => {
        if (item.amount === null) unpriced.push(item.name);
        else if (item.recurring) recurring += cents(item.amount);
        else oneTime += cents(item.amount);
      });
    });
    const months = Number(quote.term_months) || 12;
    if (months > 12) {
      add("Each year", formatCents(recurring));
      if (oneTime) add("One-time", formatCents(oneTime));
      add(`${months}-month initial term, prepaid`, quote.display.term_total, "pb-total-grand");
    } else if (oneTime) {
      add("Each year", formatCents(recurring));
      add("One-time", formatCents(oneTime));
      add("First year", quote.display.total_annual, "pb-total-grand");
    } else {
      add("Each year", quote.display.total_annual, "pb-total-grand");
    }
    totals.append(rows);
    if (unpriced.length) {
      totals.append(el("p", "pb-total-note", `Not included above, quoted separately: ${unpriced.join(", ")}.`));
    }
    const grand = rows.querySelector(".pb-total-grand");
    return `${grand.querySelector("dt").textContent}: ${grand.querySelector("dd").textContent}`;
  }

  function renderStatus() {
    status.replaceChildren();
    status.classList.toggle("is-error", Boolean(state.failure));
    if (state.problems.length) {
      status.append(el("p", "pb-status-title", "To price your package:"));
      const list = el("ul");
      state.problems.forEach((problem) => list.append(el("li", "", problem)));
      status.append(list);
    } else if (state.failure) {
      status.append(el("p", "", state.failure));
    }
    status.hidden = !state.problems.length && !state.failure;
  }

  function renderEmpty() {
    const empty = el("div", "pb-empty");
    empty.append(
      el("p", "pb-empty-title", "Nothing here yet"),
      el(
        "p",
        "",
        families.length > 1
          ? "Choose a tier from any service to start. You can mix tiers across services and add extras."
          : "Choose a tier to start, then add any extras.",
      ),
    );
    return empty;
  }

  function render() {
    const chosen = included();
    const quoted = new Map((state.quote?.agreements || []).map((agreement) => [agreement.slug, agreement]));
    summary.classList.toggle("is-pending", state.pending);
    summary.setAttribute("aria-busy", String(state.pending));
    const focused = body.contains(document.activeElement) ? document.activeElement.dataset.focusKey : null;
    body.replaceChildren(...(chosen.length ? chosen.map((family) => renderFamily(family, quoted.get(family.slug))) : [renderEmpty()]));
    if (focused) body.querySelector(`[data-focus-key="${focused}"]`)?.focus();
    const spoken = renderTotals(chosen);
    renderStatus();
    const grand = totals.querySelector(".pb-total-grand dd");
    barTotal.textContent = grand && !state.pending ? grand.textContent : "";
    updateBar();
    if (spoken && !state.pending && spoken !== state.announced) {
      state.announced = spoken;
      announce(spoken);
    }
  }

  // ---------- Small-screen package bar ----------

  const wide = window.matchMedia("(min-width: 60em)");
  const visible = new Set();
  function updateBar() {
    bar.hidden = wide.matches || !included().length || visible.size > 0;
  }
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => (entry.isIntersecting ? visible.add(entry.target) : visible.delete(entry.target)));
      updateBar();
    });
    [summary, document.getElementById("review")].forEach((target) => target && observer.observe(target));
  }
  wide.addEventListener?.("change", updateBar);

  // ---------- Events ----------

  form.addEventListener("change", (event) => {
    const target = event.target;
    const family = familyOf(target);
    if (family && target.closest(".pb-staff")) return;
    if (family) {
      if (target === family.include) {
        setIncluded(family, target.checked);
        announce(
          target.checked
            ? `${family.name} added at the ${tierColumn(tierOf(family)).dataset.tierName} tier.`
            : `${family.name} removed. Your choices are kept if you add it again.`,
        );
      } else if (target.classList.contains("pb-tier-input") && !family.include.checked) {
        family.include.checked = true;
        announce(`${family.name} added at the ${tierColumn(target).dataset.tierName} tier.`);
      }
    } else if (target.name !== "discount") {
      return;
    }
    syncAll();
    refresh();
  });

  form.addEventListener("input", (event) => {
    if (!event.target.closest(".pb-params")) return;
    syncAll();
    refresh(350);
  });

  summary.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove]");
    if (!button) return;
    const family = families.find((candidate) => candidate.slug === button.dataset.remove);
    if (!family) return;
    setIncluded(family, false);
    syncAll();
    refresh(0);
    announce(`${family.name} removed. Your choices are kept if you add it again.`);
    summaryTitle.focus();
  });

  families.forEach((family) => {
    if (!family.include.checked) setIncluded(family, false);
  });
  syncAll();
  const revealContact = setupContacts();
  setupSteps(revealContact);
  refresh(0);
})();
