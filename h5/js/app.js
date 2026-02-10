/**
 * H5 界面与游戏逻辑绑定
 */
(function () {
  const state = new GameState();
  let pendingPlot = null; // { row, col } 或 null
  let pendingBatch = false;
  let batchMode = false;
  let lastTime = performance.now();

  const FLOWER_EMOJI = {
    red_rose: { seed: "🌱", ready: "🌹", inv: "🌹" },
    white_lily: { seed: "🌱", ready: "🤍", inv: "💐" },
    eucalyptus: { seed: "🌱", ready: "🌿", inv: "🌿" },
  };

  function getPlotEmoji(plot) {
    if (!plot.crop) return "";
    const key = plot.crop.key;
    const set = FLOWER_EMOJI[key] || { seed: "🌱", ready: "🌸", inv: "🌸" };
    return plot.state === "ready" ? set.ready : set.seed;
  }

  function getPlotLabel(plot, row, col) {
    if (!plot.unlocked) {
      if (!state.isAdjacentToUnlocked(row, col)) return "🔒";
      return "🔒";
    }
    if (plot.state === "empty") return "空地";
    if (plot.state === "planted") return plot.crop ? plot.crop.name : "生长中";
    if (plot.state === "ready") return plot.crop ? plot.crop.name + " ✓" : "收获";
    return plot.state;
  }

  function getPlotClasses(plot, row, col) {
    const c = ["plot"];
    if (!plot.unlocked) {
      c.push(state.isAdjacentToUnlocked(row, col) ? "locked-adj" : "locked-far");
    } else {
      c.push("unlocked", plot.state);
    }
    return c.join(" ");
  }

  function renderPlots() {
    const container = document.getElementById("plots");
    container.innerHTML = "";
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const plot = state.plots[r][c];
        const cell = document.createElement("div");
        cell.className = getPlotClasses(plot, r, c);
        cell.dataset.row = r;
        cell.dataset.col = c;

        if (!plot.unlocked && state.isAdjacentToUnlocked(r, c)) {
          const badge = document.createElement("span");
          badge.className = "lock-badge";
          badge.innerHTML = `<span class="lock-ico">🔒</span>${plot.unlock_cost}`;
          cell.appendChild(badge);
        }

        const emoji = getPlotEmoji(plot);
        if (emoji) {
          const span = document.createElement("span");
          span.className = "plot-emoji";
          span.textContent = emoji;
          cell.appendChild(span);
        }

        const label = document.createElement("div");
        label.className = "plot-label";
        label.textContent = getPlotLabel(plot, r, c);
        cell.appendChild(label);

        cell.addEventListener("click", () => onPlotClick(r, c));
        container.appendChild(cell);
      }
    }
  }

  function onPlotClick(row, col) {
    const plot = state.plots[row][col];
    if (!plot.unlocked) {
      state.tryUnlockPlot(row, col);
      refreshAll();
      return;
    }
    if (plot.state === "empty") {
      pendingPlot = { row, col };
      pendingBatch = batchMode;
      openPlantModal();
      return;
    }
    if (batchMode) {
      if (plot.state === "planted") state.batchWater();
      else if (plot.state === "ready") state.batchHarvest();
      else state.clickPlot(row, col);
    } else {
      state.clickPlot(row, col);
    }
    refreshAll();
  }

  function refreshStats() {
    document.getElementById("water-num").textContent = state.water;
    document.getElementById("coins-num").textContent = state.coins;
    document.getElementById("level-num").textContent = "Lv." + state.level;

    const required = state.xpRequired();
    if (required == null) {
      document.getElementById("xp-fill").style.width = "100%";
      document.getElementById("xp-text").textContent = "MAX";
    } else {
      const pct = Math.min(100, (state.xp / required) * 100);
      document.getElementById("xp-fill").style.width = pct + "%";
      document.getElementById("xp-text").textContent = state.xp + "/" + required;
    }
  }

  function updateOrderTimerOnly() {
    const timerEl = document.getElementById("order-timer");
    if (state.orders.length >= state.max_orders) {
      timerEl.textContent = "订单已满";
    } else {
      timerEl.textContent = "下一单: " + Math.max(0, Math.ceil(state.order_timer)) + "s";
    }
  }

  function refreshOrders() {
    updateOrderTimerOnly();

    const container = document.getElementById("order-cards");
    container.innerHTML = "";
    state.orders.forEach((order, idx) => {
      const card = document.createElement("div");
      card.className = "order-card";
      const reqLines = Object.entries(order.requirements).map(
        ([key, qty]) => {
          const name = FLOWER_TYPES[key] || key;
          const have = state.inventory[key] || 0;
          const ok = have >= qty;
          return `${name} x${qty} ${ok ? "✓" : "(缺" + (qty - have) + ")"}`;
        }
      );
      card.innerHTML = `
        <div class="order-title">订单 ${idx + 1}</div>
        <div class="order-reqs">${reqLines.join("<br>")}</div>
        <div class="order-reward">奖励 ${order.reward} 🪙</div>
        <button type="button" class="btn-deliver ${state.canFulfill(order) ? "" : "disabled"}" data-idx="${idx}">送达</button>
      `;
      const btn = card.querySelector(".btn-deliver");
      btn.addEventListener("click", () => {
        const reward = state.deliverOrder(idx);
        if (reward > 0) refreshAll();
        else refreshOrders();
      });
      container.appendChild(card);
    });
  }

  function refreshMessage() {
    document.getElementById("message-bar").textContent = state.message;
  }

  function refreshBatchUI() {
    const wrap = document.getElementById("batch-wrap");
    const toggle = document.getElementById("batch-toggle");
    const label = document.getElementById("batch-label");
    if (state.unlockedPlotCount() >= 2) {
      wrap.style.display = "flex";
      toggle.classList.toggle("on", batchMode);
      label.textContent = batchMode ? "批量模式 开" : "批量模式";
    } else {
      wrap.style.display = "none";
    }
  }

  function refreshAll() {
    renderPlots();
    refreshStats();
    refreshOrders();
    refreshMessage();
    refreshBatchUI();
  }

  function openPlantModal() {
    const list = document.getElementById("plant-menu");
    list.innerHTML = "";

    const unlocks = state.flower_unlocks || {};
    const currentLevel = state.level;
    const entries = Object.entries(unlocks)
      .sort((a, b) => a[1] - b[1])
      .map(([key, level]) => ({
        key,
        level,
        enabled: level <= currentLevel,
        label: FLOWER_LABELS[key] || FLOWER_TYPES[key] || key,
      }));

    entries.forEach(({ key, enabled, label }) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "menu-btn" + (enabled ? "" : " disabled");
      btn.textContent = enabled ? label : label + " (Lv." + (unlocks[key] || "?") + " 解锁)";
      btn.addEventListener("click", () => {
        if (!enabled) return;
        if (pendingBatch) {
          state.batchPlant(key);
        } else if (pendingPlot) {
          state.plantFlower(pendingPlot.row, pendingPlot.col, key);
        }
        pendingPlot = null;
        pendingBatch = false;
        closePlantModal();
        refreshAll();
      });
      li.appendChild(btn);
      list.appendChild(li);
    });

    const cancelLi = document.createElement("li");
    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "menu-btn cancel";
    cancelBtn.textContent = "取消";
    cancelBtn.addEventListener("click", () => {
      pendingPlot = null;
      pendingBatch = false;
      state.setMessage("取消");
      closePlantModal();
      refreshAll();
    });
    cancelLi.appendChild(cancelBtn);
    list.appendChild(cancelLi);

    document.getElementById("modal-plant").classList.add("show");
  }

  function closePlantModal() {
    document.getElementById("modal-plant").classList.remove("show");
  }

  function openInventory() {
    const list = document.getElementById("inv-list");
    list.innerHTML = "";
    const unlocks = state.flower_unlocks || {};
    const keys = Object.keys(unlocks).sort((a, b) => (unlocks[a] || 0) - (unlocks[b] || 0));
    if (!keys.length) keys.push(...Object.keys(FLOWER_TYPES));

    keys.forEach((key) => {
      const qty = state.inventory[key] || 0;
      const name = FLOWER_TYPES[key] || key;
      const emoji = (FLOWER_EMOJI[key] && FLOWER_EMOJI[key].inv) || "🌸";
      const li = document.createElement("li");
      li.innerHTML = `<span class="inv-emoji">${emoji}</span><span class="inv-name">${name}</span><span class="inv-qty">x${qty}</span>`;
      list.appendChild(li);
    });

    document.getElementById("modal-inventory").classList.add("show");
  }

  document.getElementById("btn-buy-water").addEventListener("click", () => {
    state.buyWater();
    refreshAll();
  });

  document.getElementById("btn-rescue").addEventListener("click", () => {
    state.addWater(20);
    refreshAll();
  });

  document.getElementById("btn-inventory").addEventListener("click", openInventory);

  document.getElementById("btn-close-inv").addEventListener("click", () => {
    document.getElementById("modal-inventory").classList.remove("show");
  });

  document.getElementById("batch-toggle").addEventListener("click", () => {
    if (state.unlockedPlotCount() < 2) return;
    batchMode = !batchMode;
    state.setMessage(batchMode ? "批量模式 开" : "批量模式 关");
    refreshBatchUI();
    refreshMessage();
  });

  document.getElementById("modal-plant").addEventListener("click", (e) => {
    if (e.target.id === "modal-plant") {
      closePlantModal();
      pendingPlot = null;
      pendingBatch = false;
    }
  });

  function gameLoop(now) {
    const dt = (now - lastTime) / 1000;
    lastTime = now;
    const newOrderAdded = state.updateOrders(dt);
    if (newOrderAdded) {
      refreshOrders();
    } else {
      updateOrderTimerOnly();
    }
    requestAnimationFrame(gameLoop);
  }

  refreshAll();
  requestAnimationFrame(gameLoop);
})();
