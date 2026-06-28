// ─── State ────────────────────────────────────────────────────────────────────

let selectedAction = null;
let actionSheetQty = 1;
let partialQty = 1;
let pickModalQty = 1;
let pressTimer = null;
let activeCategory = "All";
let activeTab = "catalog";
let _activePickCategory = null;
let _pickScanCooldown = false;

// picksMap: Map<pickId, {id, product_id, sku, name, brand, image_url, quantity}>
const picksMap = new Map();

// Module-level context refs for modals (avoids storing DOM refs in datasets)
let _pickModalContext = null; // { productId, sku, triggerBtn }
let _partialContext = null; // { pickId, sku, productId }

// ─── Init ─────────────────────────────────────────────────────────────────────

function init() {
  PICKS_DATA.forEach((p) => {
    const info = PRODUCTS_MAP[p.sku] || {};
    picksMap.set(p.id, {
      ...p,
      upc: info.upc || "",
      category: info.category || "Other",
    });
  });

  updatePickBadge();
  setupNavTabs();
  setupSearch();
  setupFilterTabs();
  setupPickButtons();
  setupLongPress();
  setupPickModal();
  setupActionSheet();
  setupPartialSheet();
  setupFloorSheet();
}

document.addEventListener("DOMContentLoaded", init);

// ─── Tab switching ────────────────────────────────────────────────────────────

function setupNavTabs() {
  document.querySelectorAll(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
}

function switchTab(tab) {
  activeTab = tab;

  document
    .getElementById("view-catalog")
    .classList.toggle("hidden", tab !== "catalog");
  document
    .getElementById("view-picks")
    .classList.toggle("hidden", tab !== "picks");
  document.getElementById("view-log").classList.toggle("hidden", tab !== "log");

  document
    .getElementById("header-catalog")
    .classList.toggle("hidden", tab !== "catalog");
  document
    .getElementById("header-picks")
    .classList.toggle("hidden", tab !== "picks");
  document
    .getElementById("header-log")
    .classList.toggle("hidden", tab !== "log");

  document.querySelectorAll(".nav-tab").forEach((t) => {
    const isActive = t.dataset.tab === tab;
    t.classList.toggle("active", isActive);
    const icon = t.querySelector(".nav-icon");
    const label = t.querySelector(".nav-label");
    if (icon) {
      icon.classList.toggle("text-accent", isActive);
      icon.classList.toggle("text-muted", !isActive);
    }
    if (label) {
      label.classList.toggle("text-accent", isActive);
      label.classList.toggle("text-muted", !isActive);
    }
  });

  if (tab === "picks") renderPicksView();
  if (tab === "log") renderLogView();
}

// ─── Search ───────────────────────────────────────────────────────────────────

function setupSearch() {
  const input = document.getElementById("search-input");
  const clearBtn = document.getElementById("search-clear");
  input.addEventListener("input", () => {
    clearBtn.classList.toggle("hidden", !input.value);
    applyFilters();
  });
  clearBtn.addEventListener("click", () => {
    input.value = "";
    clearBtn.classList.add("hidden");
    applyFilters();
    input.focus();
  });
}

// ─── Filter tabs ──────────────────────────────────────────────────────────────

function setupFilterTabs() {
  document.querySelectorAll(".filter-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document
        .querySelectorAll(".filter-tab")
        .forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      activeCategory = tab.dataset.category;
      applyFilters();
    });
  });
}

function applyFilters() {
  const query = document
    .getElementById("search-input")
    .value.trim()
    .toLowerCase();
  const cards = document.querySelectorAll(".product-card");
  let visible = 0;
  cards.forEach((card) => {
    const matchCategory =
      activeCategory === "All" ||
      activeCategory.split("|").includes(card.dataset.category);
    const matchSearch =
      !query ||
      card.dataset.name.toLowerCase().includes(query) ||
      card.dataset.upc.toLowerCase().includes(query) ||
      card.dataset.brand.toLowerCase().includes(query);
    const show = matchCategory && matchSearch;
    card.style.display = show ? "" : "none";
    if (show) visible++;
  });
  document.getElementById("no-results").classList.toggle("hidden", visible > 0);
}

// ─── Pick buttons (bookmark tap → modal) ─────────────────────────────────────

function setupPickButtons() {
  document.querySelectorAll(".pick-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const sku = btn.dataset.sku;
      if (PICKED_SKUS.has(sku)) {
        const pick = [...picksMap.values()].find((p) => p.sku === sku);
        if (pick) removePick(pick.id, sku);
      } else {
        openPickModal(
          parseInt(btn.dataset.productId, 10),
          btn.dataset.displayName,
          sku,
          btn,
        );
      }
    });
  });
}

// ─── Pick modal ───────────────────────────────────────────────────────────────

function openPickModal(productId, name, sku, triggerBtn) {
  pickModalQty = 1;
  document.getElementById("pick-modal-qty").textContent = "1";
  document.getElementById("pick-modal-product-name").textContent = name;
  _pickModalContext = { productId, sku, triggerBtn };
  showOverlay("pick-modal");
}

function closePickModal() {
  hideOverlay("pick-modal");
  _pickModalContext = null;
}

function setupPickModal() {
  document
    .getElementById("pick-modal-backdrop")
    .addEventListener("click", closePickModal);
  document
    .getElementById("pick-modal-cancel")
    .addEventListener("click", closePickModal);

  document.getElementById("pick-modal-dec").addEventListener("click", () => {
    if (pickModalQty > 1) {
      pickModalQty--;
      document.getElementById("pick-modal-qty").textContent = pickModalQty;
    }
  });

  document.getElementById("pick-modal-inc").addEventListener("click", () => {
    if (pickModalQty < 10) {
      pickModalQty++;
      document.getElementById("pick-modal-qty").textContent = pickModalQty;
    }
  });

  document
    .getElementById("pick-modal-add")
    .addEventListener("click", async () => {
      if (!_pickModalContext) return;
      const { productId, sku, triggerBtn } = _pickModalContext;
      closePickModal();
      await addPick(productId, sku, pickModalQty, triggerBtn);
    });
}

// ─── Core pick add / remove ───────────────────────────────────────────────────

async function addPick(productId, sku, qty, triggerBtn) {
  // Optimistically mark as picked to prevent double-taps
  PICKED_SKUS.add(sku);
  if (triggerBtn) setBookmarkFilled(triggerBtn);

  try {
    const res = await fetch("/picks_list/mark-for-pick", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: productId,
        quantity: qty,
        user_id: 1,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const productInfo = PRODUCTS_MAP[sku] || {};
    picksMap.set(data.id, {
      id: data.id,
      product_id: productId,
      sku,
      name: productInfo.name || sku,
      brand: productInfo.brand || "",
      image_url: productInfo.image_url || "",
      upc: productInfo.upc || "",
      category: productInfo.category || "Other",
      quantity: data.quantity,
    });

    updatePickBadge();
    showToast("Added to picks");
  } catch (err) {
    // Revert optimistic update
    PICKED_SKUS.delete(sku);
    if (triggerBtn) setBookmarkOutline(triggerBtn);
    console.error("Failed to add pick:", err);
    showToast("Failed to add pick");
  }
}

async function removePick(pickId, sku) {
  if (!picksMap.has(pickId)) return;
  picksMap.delete(pickId);
  PICKED_SKUS.delete(sku);
  const cardBtn = document.querySelector(`.pick-btn[data-sku="${sku}"]`);
  if (cardBtn) setBookmarkOutline(cardBtn);
  updatePickBadge();
  if (activeTab === "picks") renderPicksView();

  try {
    const res = await fetch(`/picks_list/unmark_for_pick/${pickId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    console.error("Failed to remove pick:", err);
    showToast("Failed to remove pick");
  }
}

// ─── Pick List view ───────────────────────────────────────────────────────────

// Category display order
const CATEGORY_ORDER = [
  "Raw Beef",
  "Raw Pork",
  "Raw Chicken",
  "Raw Poultry",
  "Raw Fish",
  "Ready to eat",
  "Other",
];

const CATEGORY_LABELS = {
  "Raw Beef": "Beef",
  "Raw Pork": "Pork",
  "Raw Chicken": "Poultry",
  "Raw Poultry": "Poultry",
  "Raw Fish": "Fish",
  "Ready to eat": "Ready to Eat",
  Other: "Other",
};

function renderPicksView() {
  const container = document.getElementById("view-picks");
  container.innerHTML = "";

  if (picksMap.size === 0) {
    container.innerHTML = `<p class="text-center text-muted text-sm py-12">No items on the pick list.</p>`;
    return;
  }

  // Group picks by category
  const groups = new Map();
  picksMap.forEach((pick) => {
    const cat = pick.category || "Other";
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat).push(pick);
  });

  // Render in defined order, then any remaining
  const ordered = CATEGORY_ORDER.filter((c) => groups.has(c));
  groups.forEach((_, c) => {
    if (!ordered.includes(c)) ordered.push(c);
  });

  ordered.forEach((cat) => {
    const picks = groups.get(cat);
    const label = CATEGORY_LABELS[cat] || cat;
    const count = picks.length;

    const section = document.createElement("div");
    section.className = "mb-2";

    // Header row
    const header = document.createElement("button");
    header.className = "w-full flex items-center justify-between px-1 py-2";
    header.innerHTML = `
      <div class="flex-1 flex items-center justify-center gap-2">
        <span class="text-white font-bold text-base">${escHtml(label)}</span>
        <span class="bg-accent text-surface text-sm font-bold rounded-full px-2.5 py-0.5">${count}</span>
      </div>
      <svg class="chevron w-4 h-4 text-muted transition-transform flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path d="M19 9l-7 7-7-7"/>
      </svg>
    `;

    const body = document.createElement("div");
    body.className = "pick-section-body space-y-2";

    picks.forEach((pick) => {
      const div = document.createElement("div");
      div.className = "bg-card rounded-xl border border-border p-3";
      div.innerHTML = `
        <div class="flex items-center gap-3 mb-3">
          ${
            pick.image_url
              ? `<img src="${escHtml(pick.image_url)}" class="w-12 h-12 rounded-lg object-cover flex-shrink-0" loading="lazy">`
              : `<div class="w-12 h-12 rounded-lg bg-border flex-shrink-0"></div>`
          }
          <div class="flex-1 min-w-0">
            <p class="text-white text-sm font-semibold leading-snug line-clamp-2">${escHtml(pick.name)}</p>
            <p class="text-muted text-xs">Target: ${pick.quantity} case${pick.quantity !== 1 ? "s" : ""}</p>
            ${pick.upc ? `<p class="text-muted text-xs">UPC: ${escHtml(pick.upc)}</p>` : ""}
          </div>
        </div>
        <div class="grid grid-cols-3 gap-1.5">
          <button class="picked-btn rounded-lg py-2 text-xs font-semibold bg-border text-white"
            data-pick-id="${pick.id}" data-sku="${escHtml(pick.sku)}" data-product-id="${pick.product_id}" data-name="${escHtml(pick.name)}">
            Picked ✓
          </button>
          <button class="failed-btn rounded-lg py-2 text-xs font-semibold bg-border text-white"
            data-pick-id="${pick.id}" data-sku="${escHtml(pick.sku)}" data-product-id="${pick.product_id}">
            Failed ✗
          </button>
          <button class="remove-btn rounded-lg py-2 text-xs font-semibold bg-border text-white"
            data-pick-id="${pick.id}" data-sku="${escHtml(pick.sku)}">
            Remove
          </button>
        </div>
      `;

      div.querySelector(".picked-btn").addEventListener("click", async () => {
        try {
          const res = await fetch("/activity_log/log-activity", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              product_id: pick.product_id,
              action: "restock",
              units_qty: 1,
              user_id: 1,
            }),
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          await removePick(pick.id, pick.sku);
          showToast("Picked & logged ✓");
        } catch (err) {
          console.error(err);
          showToast("Error logging pick");
        }
      });
      div
        .querySelector(".failed-btn")
        .addEventListener("click", () =>
          handleFailedPick(pick.id, pick.sku, pick.product_id),
        );
      div
        .querySelector(".remove-btn")
        .addEventListener("click", () => removePick(pick.id, pick.sku));

      body.appendChild(div);
    });

    // Start collapsed
    body.classList.add("hidden");
    header.querySelector(".chevron").style.transform = "rotate(-90deg)";

    header.addEventListener("click", () => {
      const isCollapsed = body.classList.contains("hidden");
      container
        .querySelectorAll(".pick-section-body")
        .forEach((b) => b.classList.add("hidden"));
      container.querySelectorAll(".chevron").forEach((c) => {
        c.style.transform = "rotate(-90deg)";
      });
      if (isCollapsed) {
        body.classList.remove("hidden");
        header.querySelector(".chevron").style.transform = "";
        _activePickCategory = cat;
      } else {
        _activePickCategory = null;
      }
    });

    section.appendChild(header);
    section.appendChild(body);
    container.appendChild(section);
  });
  if (_activePickCategory) {
    const sections = [...container.querySelectorAll(".pick-section-body")];
    const headers = [...container.querySelectorAll("button")];
    ordered.forEach((c, i) => {
      if (c === _activePickCategory) {
        sections[i].classList.remove("hidden");
        headers[i].querySelector(".chevron").style.transform = "";
      }
    });
  }
}

async function handleFailedPick(pickId, sku, productId) {
  try {
    const res = await fetch("/activity_log/log-activity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: productId,
        action: "restock",
        notes: "Failed pick. Item OOS.",
        user_id: 1,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await removePick(pickId, sku);
    showToast("Failed pick logged");
  } catch (err) {
    console.error(err);
    showToast("Error logging failed pick");
  }
}

// ─── Partial pick sheet ───────────────────────────────────────────────────────

function openPickedSheet(pickId, sku, productId, name) {
  partialQty = 1;
  document.getElementById("partial-qty-display").textContent = "1";
  document.getElementById("partial-product-name").textContent = name;
  document.getElementById("partial-pick-id").value = pickId;
  document.getElementById("partial-product-id").value = productId;
  _partialContext = { pickId, sku, productId };
  showOverlay("partial-sheet");
}

function closePartialSheet() {
  hideOverlay("partial-sheet");
  _partialContext = null;
}

function setupPartialSheet() {
  document
    .getElementById("partial-backdrop")
    .addEventListener("click", closePartialSheet);
  document
    .getElementById("partial-cancel")
    .addEventListener("click", closePartialSheet);

  document.getElementById("partial-dec").addEventListener("click", () => {
    if (partialQty > 1) {
      partialQty--;
      document.getElementById("partial-qty-display").textContent = partialQty;
    }
  });

  document.getElementById("partial-inc").addEventListener("click", () => {
    partialQty++;
    document.getElementById("partial-qty-display").textContent = partialQty;
  });

  document
    .getElementById("partial-confirm")
    .addEventListener("click", async () => {
      if (!_partialContext) return;
      const { pickId, sku, productId } = _partialContext;
      const qty = partialQty;
      closePartialSheet();

      try {
        const res = await fetch("/activity_log/log-activity", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_id: productId,
            action: "restock",
            units_qty: qty,
            user_id: 1,
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await removePick(pickId, sku);
        showToast(`Picked & logged ×${qty}`);
      } catch (err) {
        console.error(err);
        showToast("Error logging partial pick");
      }
    });
}

// ─── Long-press → action sheet ────────────────────────────────────────────────

function setupLongPress() {
  document.querySelectorAll(".product-card").forEach((card) => {
    card.addEventListener(
      "touchstart",
      () => {
        pressTimer = setTimeout(
          () =>
            openActionSheet(
              card.dataset.productId,
              card.dataset.displayName,
              PRODUCTS_MAP[card.dataset.sku]?.image_url || "",
            ),
          500,
        );
      },
      { passive: true },
    );
    card.addEventListener("touchend", () => clearTimeout(pressTimer));
    card.addEventListener("touchmove", () => clearTimeout(pressTimer));
    card.addEventListener("touchcancel", () => clearTimeout(pressTimer));

    card.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      pressTimer = setTimeout(
        () =>
          openActionSheet(
            card.dataset.productId,
            card.dataset.displayName,
            PRODUCTS_MAP[card.dataset.sku]?.image_url || "",
          ),
        600,
      );
    });
    card.addEventListener("mouseup", () => clearTimeout(pressTimer));
    card.addEventListener("mouseleave", () => clearTimeout(pressTimer));
  });
}

function openActionSheet(productId, name, imageUrl = "") {
  selectedAction = null;
  actionSheetQty = 1;
  document.getElementById("qty-display").textContent = "1";
  const unitLabel = document.getElementById("qty-unit-label");
  if (unitLabel) unitLabel.textContent = "Unit(s)";
  document.getElementById("qty-row").classList.remove("hidden");
  const noteInput = document.getElementById("action-note-input");
  noteInput.classList.add("hidden");
  noteInput.value = "";
  document.getElementById("action-product-id").value = productId;
  document.getElementById("action-product-name").textContent = name;

  const wrap = document.getElementById("action-product-image-wrap");
  const img = document.getElementById("action-product-image");
  if (imageUrl) {
    img.src = imageUrl;
    img.alt = name;
    wrap.classList.remove("hidden");
  } else {
    img.removeAttribute("src");
    wrap.classList.add("hidden");
  }

  document
    .querySelectorAll(".action-btn")
    .forEach((b) => b.classList.remove("selected"));
  showOverlay("action-sheet");
}

function closeActionSheet() {
  hideOverlay("action-sheet");
  selectedAction = null;
}

function setupActionSheet() {
  document
    .getElementById("sheet-backdrop")
    .addEventListener("click", closeActionSheet);
  document
    .getElementById("sheet-cancel-btn")
    .addEventListener("click", closeActionSheet);

  document.querySelectorAll(".action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".action-btn")
        .forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedAction = btn.dataset.action;
      const label = document.getElementById("qty-unit-label");
      if (label)
        label.textContent = selectedAction === "vizpik" ? "Case(s)" : "Unit(s)";
      const isNote = selectedAction === "product_note";
      document.getElementById("qty-row").classList.toggle("hidden", isNote);
      const noteInput = document.getElementById("action-note-input");
      noteInput.classList.toggle("hidden", !isNote);
      if (isNote) noteInput.focus();
    });
  });

  document.getElementById("qty-dec").addEventListener("click", () => {
    if (actionSheetQty > 1) {
      actionSheetQty--;
      document.getElementById("qty-display").textContent = actionSheetQty;
    }
  });

  document.getElementById("qty-inc").addEventListener("click", () => {
    actionSheetQty++;
    document.getElementById("qty-display").textContent = actionSheetQty;
  });

  document
    .getElementById("sheet-log-btn")
    .addEventListener("click", async () => {
      if (!selectedAction) {
        showToast("Select an action first");
        return;
      }

      const productId = parseInt(
        document.getElementById("action-product-id").value,
        10,
      );
      const caseActions = ["vizpik"];
      const unitActions = ["throw", "cvp", "donate"];
      const payload = {
        product_id: productId,
        action: selectedAction,
        user_id: 1,
      };
      if (selectedAction === "product_note") {
        const note = document.getElementById("action-note-input").value.trim();
        if (!note) {
          showToast("Enter a note first");
          return;
        }
        payload.notes = note;
      } else if (caseActions.includes(selectedAction))
        payload.cases_qty = actionSheetQty;
      else if (unitActions.includes(selectedAction))
        payload.units_qty = actionSheetQty;

      try {
        const res = await fetch("/activity_log/log-activity", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const label = ACTION_LABELS[selectedAction] || selectedAction;
        const qty = actionSheetQty;
        closeActionSheet();
        showToast(`${label} logged ×${qty}`);
      } catch (err) {
        console.error(err);
        showToast("Failed to log action");
      }
    });
}

// ─── Activity Log view ────────────────────────────────────────────────────────

const ACTION_LABELS = {
  throw: "Throw",
  cvp: "CVP",
  vizpik: "Vizpik",
  restock: "Restock",
  clean_daily: "Daily Clean",
  clean_pm: "PM Clean",
  temp_check: "Temp Check",
  general_note: "General Note",
  product_note: "Product Note",
  donate: "Donate",
  floor_sweep: "Floor Sweep",
  recovery: "Recovery",
};

// Badge bg / text colors per action
const ACTION_COLORS = {
  throw: { bg: "#fde8e8", text: "#b91c1c" }, // red
  cvp: { bg: "#e0f2fe", text: "#0369a1" }, // blue
  vizpik: { bg: "#ede9fe", text: "#6d28d9" }, // purple
  restock: { bg: "#dcfce7", text: "#15803d" }, // green
  donate: { bg: "#fef9c3", text: "#a16207" }, // yellow
  product_note: { bg: "#ffedd5", text: "#c2410c" }, // orange
  general_note: { bg: "#f3f4f6", text: "#374151" }, // gray
  clean_daily: { bg: "#cffafe", text: "#0e7490" }, // cyan
  clean_pm: { bg: "#e0e7ff", text: "#3730a3" }, // indigo
  temp_check: { bg: "#fce7f3", text: "#9d174d" }, // pink
  floor_sweep: { bg: "#d1fae5", text: "#065f46" }, // emerald
  recovery: { bg: "#fef3c7", text: "#92400e" }, // amber
};

async function renderLogView() {
  const container = document.getElementById("log-feed");
  container.innerHTML = `<p class="text-center text-muted text-sm py-8">Loading…</p>`;

  try {
    const res = await fetch("/activity_log/feed");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const logs = await res.json();

    if (logs.length === 0) {
      container.innerHTML = `<p class="text-center text-muted text-sm py-8">No activity logged yet.</p>`;
      return;
    }

    container.innerHTML = "";
    _lastLogId = logs[logs.length - 1].id;
    logs.forEach((log) => {
      const div = document.createElement("div");
      div.className = "bg-card rounded-xl border border-border p-3";

      const label = ACTION_LABELS[log.action] || log.action;
      const color = ACTION_COLORS[log.action] || {
        bg: "#e5e7eb",
        text: "#374151",
      };

      const qtyParts = [];
      if (log.cases_qty)
        qtyParts.push(`${log.cases_qty} case${log.cases_qty !== 1 ? "s" : ""}`);
      if (log.units_qty)
        qtyParts.push(`${log.units_qty} unit${log.units_qty !== 1 ? "s" : ""}`);
      const qtyStr = qtyParts.join(", ");

      const timeStr = log.logged_at
        ? new Date(log.logged_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })
        : "";

      div.innerHTML = `
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <span class="inline-block text-xs font-semibold px-2 py-0.5 rounded-full mb-1" style="background:${color.bg};color:${color.text}">${escHtml(label)}</span>
            ${log.product_name ? `<p class="text-white text-sm font-medium leading-snug line-clamp-2">${escHtml(log.product_name)}</p>` : ""}
            ${qtyStr && log.action !== "restock" ? `<p class="text-muted text-xs mt-0.5">${escHtml(qtyStr)}</p>` : ""}
            ${log.notes ? `<p class="text-muted text-xs mt-0.5 italic">${escHtml(log.notes)}</p>` : ""}
          </div>
          <p class="text-muted text-xs flex-shrink-0 mt-0.5">${escHtml(timeStr)}</p>
        </div>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    console.error(err);
    container.innerHTML = `<p class="text-center text-muted text-sm py-12">Failed to load activity log.</p>`;
  }
}

// ─── Floor activity sheet ─────────────────────────────────────────────────────

// ─── Delete last log ──────────────────────────────────────────────────────────

let _lastLogId = null;

document
  .getElementById("delete-last-log-btn")
  .addEventListener("click", async () => {
    if (!_lastLogId) {
      showToast("Nothing to undo");
      return;
    }
    try {
      const res = await fetch(`/activity_log/delete-activity/${_lastLogId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      _lastLogId = null;
      showToast("Last entry deleted");
      renderLogView();
    } catch (err) {
      console.error(err);
      showToast("Failed to delete");
    }
  });

// ─── Floor sheet ──────────────────────────────────────────────────────────────

let _selectedFloorAction = null;

function openFloorSheet() {
  _selectedFloorAction = null;
  document.getElementById("floor-notes").value = "";
  document
    .querySelectorAll(".floor-btn")
    .forEach((b) => b.classList.remove("selected"));
  showOverlay("floor-sheet");
}

function closeFloorSheet() {
  hideOverlay("floor-sheet");
  _selectedFloorAction = null;
}

function setupFloorSheet() {
  document
    .getElementById("log-activity-btn")
    .addEventListener("click", openFloorSheet);
  document
    .getElementById("floor-backdrop")
    .addEventListener("click", closeFloorSheet);
  document
    .getElementById("floor-cancel")
    .addEventListener("click", closeFloorSheet);

  document.querySelectorAll(".floor-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".floor-btn")
        .forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      _selectedFloorAction = btn.dataset.action;
    });
  });

  document.getElementById("floor-log").addEventListener("click", async () => {
    if (!_selectedFloorAction) {
      showToast("Select an activity first");
      return;
    }

    const action = _selectedFloorAction;
    const notes = document.getElementById("floor-notes").value.trim() || null;
    closeFloorSheet();

    try {
      const res = await fetch("/activity_log/log-activity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, notes, user_id: 1 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      showToast(`${ACTION_LABELS[action]} logged`);
      renderLogView();
    } catch (err) {
      console.error(err);
      showToast("Failed to log activity");
    }
  });
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function updatePickBadge() {
  const count = picksMap.size;
  const badge = document.getElementById("pick-count-badge");
  badge.textContent = count;
  badge.classList.toggle("hidden", count === 0);
}

function setBookmarkFilled(btn) {
  btn.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="currentColor">
      <path d="M6 2a2 2 0 00-2 2v18l8-4 8 4V4a2 2 0 00-2-2H6z"/>
    </svg>`;
}

function setBookmarkOutline(btn) {
  btn.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M19 21l-7-4-7 4V5a2 2 0 012-2h10a2 2 0 012 2v16z"/>
    </svg>`;
}

function escHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showOverlay(id) {
  const el = document.getElementById(id);
  el.style.display = "flex";
}

function hideOverlay(id) {
  const el = document.getElementById(id);
  el.style.display = "none";
}

// ─── Barcode scanner ──────────────────────────────────────────────────────────

const _detectionCounts = {};

function openScanner() {
  document.getElementById("scanner-overlay").style.display = "flex";
  document.getElementById("scanner-status").textContent =
    "Point camera at a barcode…";

  Quagga.init(
    {
      inputStream: {
        type: "LiveStream",
        target: document.getElementById("scanner-video"),
        constraints: { facingMode: "environment" },
      },
      decoder: {
        readers: ["upc_reader", "code_128_reader"],
      },
    },
    (err) => {
      if (err) {
        document.getElementById("scanner-status").textContent =
          "Camera error: " + err.message;
        console.error(err);
        return;
      }
      Quagga.start();
    },
  );

  Quagga.onDetected((data) => {
    if (data.codeResult.startInfo.error > 0.1) return;
    const upc = data.codeResult.code.replace(/^0/, "");
    _detectionCounts[upc] = (_detectionCounts[upc] || 0) + 1;
    if (_detectionCounts[upc] >= 3) {
      closeScanner();
      const input = document.getElementById("search-input");
      input.value = upc;
      document.getElementById("search-clear").classList.remove("hidden");
      applyFilters();
      const visibleCards = [
        ...document.querySelectorAll(".product-card"),
      ].filter((card) => card.style.display !== "none");
      showToast(`Scanned: ${upc}`);
      if (visibleCards.length === 1) {
        const card = visibleCards[0];
        openActionSheet(
          card.dataset.productId,
          card.dataset.displayName,
          PRODUCTS_MAP[card.dataset.sku]?.image_url || "",
        );
      }
    }
  });
}

function closeScanner() {
  Quagga.stop();
  Object.keys(_detectionCounts).forEach((k) => delete _detectionCounts[k]);
  document.getElementById("scanner-overlay").style.display = "none";
}

document.getElementById("scan-btn").addEventListener("click", openScanner);
document
  .getElementById("scanner-close")
  .addEventListener("click", closeScanner);

// ─── Pick list scanner ────────────────────────────────────────────────────────

const _pickDetectionCounts = {};
let _pickScannerRunning = false;

function openPickScanner() {
  document.getElementById("pick-scanner-overlay").style.display = "flex";
  document.getElementById("pick-scanner-overlay").style.flexDirection =
    "column";
  document.getElementById("pick-scanner-status").textContent =
    "Point camera at item barcode…";
  _pickScannerRunning = true;

  Quagga.init(
    {
      inputStream: {
        type: "LiveStream",
        target: document.getElementById("pick-scanner-video"),
        constraints: { facingMode: "environment" },
      },
      decoder: { readers: ["upc_reader", "code_128_reader"] },
    },
    (err) => {
      if (err) {
        document.getElementById("pick-scanner-status").textContent =
          "Camera error: " + err.message;
        return;
      }
      Quagga.start();
    },
  );

  Quagga.onDetected((data) => {
    if (!_pickScannerRunning || _pickScanCooldown) return;
    const raw = data.codeResult.code.replace(/^0/, "");
    _pickDetectionCounts[raw] = (_pickDetectionCounts[raw] || 0) + 1;
    if (_pickDetectionCounts[raw] >= 3) {
      _pickScanCooldown = true;
      Object.keys(_pickDetectionCounts).forEach(
        (k) => delete _pickDetectionCounts[k],
      );
      showPickScanResult(raw);
      setTimeout(() => {
        _pickScanCooldown = false;
      }, 5000); // match your toast duration
    }
  });
}

function closePickScanner() {
  Quagga.stop();
  _pickScanCooldown = false;
  Object.keys(_pickDetectionCounts).forEach(
    (k) => delete _pickDetectionCounts[k],
  );
  document.getElementById("pick-scanner-overlay").style.display = "none";
}

function showPickScanResult(upc) {
  const match = [...picksMap.values()].find(
    (p) => p.upc && p.upc.replace(/^0/, "") === upc,
  );
  const toast = document.getElementById("pick-scan-toast");
  document.getElementById("pick-scan-verdict").textContent = match
    ? "✓ Pick this item"
    : "✗ Do not pick";
  document.getElementById("pick-scan-product-name").textContent = match
    ? match.name
    : "Not on pick list";
  document.getElementById("pick-scan-upc").textContent = "UPC: " + upc;
  toast.style.backgroundColor = match ? "#16a34a" : "#dc2626";
  toast.style.display = "block";
  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => {
      toast.style.display = "none";
    }, 300);
  }, 3000);
}

document
  .getElementById("pick-scan-btn")
  .addEventListener("click", openPickScanner);
document
  .getElementById("pick-scanner-close")
  .addEventListener("click", closePickScanner);

// ─── Toast ────────────────────────────────────────────────────────────────────

function showToast(message) {
  const toast = document.createElement("div");
  toast.className =
    "fixed bottom-20 left-1/2 -translate-x-1/2 bg-accent text-white text-sm font-semibold px-5 py-2.5 rounded-full shadow-lg z-[100] transition-opacity duration-300";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 2000);
}
