/**
 * 游戏状态与逻辑，与 garden/models.py 保持一致
 */

(function (global) {
  const { CONFIG, FLOWER_TYPES } = global;

  function createPlot() {
    return {
      state: "empty",
      crop: null,
      unlocked: false,
      unlock_cost: 0,
    };
  }

  function createPlots() {
    const plots = [];
    for (let r = 0; r < 3; r++) {
      const row = [];
      for (let c = 0; c < 3; c++) {
        row.push(createPlot());
      }
      plots.push(row);
    }
    return plots;
  }

  function applyPlotUnlocks(state) {
    const costs = state.plot_unlock_costs;
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const plot = state.plots[r][c];
        plot.unlock_cost = costs[r][c];
        plot.unlocked = r === 0 && c === 0;
      }
    }
  }

  function GameState() {
    this.inventory = {};
    this.plots = createPlots();
    this.message = "Ready";
    this.water = 20;
    this.level = 1;
    this.xp = 0;
    this.level_xp = { ...CONFIG.level_xp };
    this.flower_unlocks = { ...CONFIG.flower_unlocks };
    this.flower_values = { ...CONFIG.flower_values };
    this.coins = 0;
    this.orders = [];
    this.order_timer = 10;
    this.max_orders = 3;
    this.order_interval = 10;
    this.plot_unlock_costs = CONFIG.plot_unlock_costs.map((row) => [...row]);

    applyPlotUnlocks(this);
    this.generateOrder();
  }

  GameState.prototype.setMessage = function (text) {
    this.message = text;
  };

  GameState.prototype.unlockedFlowers = function () {
    const level = this.level;
    return Object.keys(this.flower_unlocks).filter(
      (key) => this.flower_unlocks[key] <= level
    );
  };

  GameState.prototype.unlockedPlotCount = function () {
    let count = 0;
    this.plots.forEach((row) => {
      row.forEach((plot) => {
        if (plot.unlocked) count++;
      });
    });
    return count;
  };

  GameState.prototype.isAdjacentToUnlocked = function (row, col) {
    const neighbors = [
      [row - 1, col],
      [row + 1, col],
      [row, col - 1],
      [row, col + 1],
    ];
    for (const [r, c] of neighbors) {
      if (r >= 0 && r < 3 && c >= 0 && c < 3 && this.plots[r][c].unlocked) {
        return true;
      }
    }
    return false;
  };

  GameState.prototype.tryUnlockPlot = function (row, col) {
    if (row < 0 || row >= 3 || col < 0 || col >= 3) return;
    const plot = this.plots[row][col];
    if (plot.unlocked) return;
    if (!this.isAdjacentToUnlocked(row, col)) {
      this.setMessage("请先解锁相邻地块～");
      return;
    }
    if (this.coins < plot.unlock_cost) {
      this.setMessage(`需要 ${plot.unlock_cost} 金币`);
      return;
    }
    this.coins -= plot.unlock_cost;
    plot.unlocked = true;
    this.setMessage(`解锁 (${row + 1},${col + 1})，-${plot.unlock_cost} 金币`);
  };

  GameState.prototype.buyWater = function () {
    if (this.coins < 3) {
      this.setMessage("金币不够哦");
      return;
    }
    this.coins -= 3;
    this.water += 1;
    this.setMessage("购买 1 滴水 -3 金币");
  };

  GameState.prototype.addWater = function (amount) {
    if (amount <= 0) return;
    this.water += amount;
    this.setMessage("防卡死：获得 " + amount + " 滴水");
  };

  GameState.prototype.batchPlant = function (flowerKey) {
    const name = FLOWER_TYPES[flowerKey] || "Red Rose";
    let count = 0;
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const plot = this.plots[r][c];
        if (plot.unlocked && plot.state === "empty") {
          plot.state = "planted";
          plot.crop = { key: flowerKey, name };
          count++;
        }
      }
    }
    this.setMessage(`种下 ${name} x${count}`);
    return count;
  };

  GameState.prototype.batchWater = function () {
    if (this.water <= 0) {
      this.setMessage("没有水啦");
      return 0;
    }
    const planted = [];
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const plot = this.plots[r][c];
        if (plot.unlocked && plot.state === "planted") planted.push(plot);
      }
    }
    const total = planted.length;
    if (total === 0) {
      this.setMessage("没有可浇的地块");
      return 0;
    }
    const canWater = Math.min(this.water, total);
    for (let i = 0; i < canWater; i++) {
      planted[i].state = "ready";
      this.water -= 1;
    }
    this.setMessage(
      canWater < total
        ? `浇了 ${canWater}/${total}，剩余水 ${this.water}`
        : `浇了 ${canWater}，剩余水 ${this.water}`
    );
    return canWater;
  };

  GameState.prototype.batchHarvest = function () {
    const harvested = {};
    let total = 0;
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const plot = this.plots[r][c];
        if (plot.unlocked && plot.state === "ready" && plot.crop) {
          const key = plot.crop.key;
          harvested[key] = (harvested[key] || 0) + 1;
          total += 1;
          plot.state = "empty";
          plot.crop = null;
        }
      }
    }
    Object.keys(harvested).forEach((key) => {
      this.inventory[key] = (this.inventory[key] || 0) + harvested[key];
    });
    if (total > 0) this.gainXp(total);
    if (total === 0) {
      this.setMessage("没有可收获的");
      return 0;
    }
    const parts = Object.entries(harvested).map(
      ([k, v]) => `${FLOWER_TYPES[k] || k} x${v}`
    );
    this.setMessage(`收获 ${total}: ${parts.join(", ")}`);
    return total;
  };

  GameState.prototype.updateOrders = function (dt) {
    if (dt <= 0 || this.orders.length >= this.max_orders) return false;
    this.order_timer -= dt;
    if (this.order_timer > 0) return false;
    this.generateOrder();
    this.order_timer = this.order_interval;
    return true; // 新订单生成，调用方需要刷新订单列表
  };

  GameState.prototype.generateOrder = function () {
    const available = this.unlockedFlowers();
    if (!available.length) return;
    // 订单总朵数：1 级 3~5，2 级 4~7，3 级 6~10
    const levelRanges = { 1: [3, 5], 2: [4, 7], 3: [6, 10] };
    const range = levelRanges[this.level] || levelRanges[3];
    const totalMin = range[0];
    const totalMax = range[1];
    const total = totalMin + Math.floor(Math.random() * (totalMax - totalMin + 1));
    const maxTypes = Math.min(available.length, total);
    // 允许单一种花或混搭：1 ~ maxTypes 随机
    const numTypes = 1 + Math.floor(Math.random() * maxTypes);
    const chosen = shuffle([...available]).slice(0, numTypes);
    let remaining = total;
    const requirements = {};
    chosen.forEach((key, idx) => {
      const isLast = idx === numTypes - 1;
      const maxQty = Math.max(1, remaining - (numTypes - idx - 1));
      const qty = isLast ? remaining : 1 + Math.floor(Math.random() * maxQty);
      requirements[key] = qty;
      remaining -= qty;
    });
    let reward = 0;
    Object.entries(requirements).forEach(([key, qty]) => {
      reward += (this.flower_values[key] || 0) * qty;
    });
    this.orders.push({ requirements, reward });
    this.order_timer = this.order_interval;
  };

  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  GameState.prototype.deliverOrder = function (index) {
    if (index < 0 || index >= this.orders.length) return 0;
    const order = this.orders[index];
    if (!this.canFulfill(order)) {
      const missing = this.missingFor(order);
      this.setMessage(missing.length ? `缺少: ${missing.join(", ")}` : "花不够哦");
      return 0;
    }
    Object.entries(order.requirements).forEach(([key, qty]) => {
      this.inventory[key] = (this.inventory[key] || 0) - qty;
    });
    const reward = order.reward;
    this.coins += reward;
    this.orders.splice(index, 1);
    // 交付订单不重置“下一单”倒计时，新订单仍按原计时生成
    this.setMessage(`送达 +${reward} 金币`);
    return reward;
  };

  GameState.prototype.canFulfill = function (order) {
    return Object.entries(order.requirements).every(
      ([key, qty]) => (this.inventory[key] || 0) >= qty
    );
  };

  GameState.prototype.missingFor = function (order) {
    const missing = [];
    Object.entries(order.requirements).forEach(([key, qty]) => {
      const have = this.inventory[key] || 0;
      if (have < qty) {
        missing.push(`${FLOWER_TYPES[key] || key} x${qty - have}`);
      }
    });
    return missing;
  };

  GameState.prototype.xpRequired = function () {
    return this.level_xp[this.level] ?? null;
  };

  GameState.prototype.gainXp = function (amount) {
    if (amount <= 0) return;
    this.xp += amount;
    for (;;) {
      const required = this.xpRequired();
      if (required == null || this.xp < required) break;
      this.xp -= required;
      this.level += 1;
    }
  };

  GameState.prototype.plantFlower = function (row, col, flowerKey) {
    if (row < 0 || row >= 3 || col < 0 || col >= 3) return;
    const plot = this.plots[row][col];
    if (plot.state !== "empty") return;
    const name = FLOWER_TYPES[flowerKey] || "Red Rose";
    plot.state = "planted";
    plot.crop = { key: flowerKey, name };
    this.setMessage(`种下 ${name}`);
  };

  GameState.prototype.clickPlot = function (row, col) {
    if (row < 0 || row >= 3 || col < 0 || col >= 3) return;
    const plot = this.plots[row][col];
    if (!plot.unlocked) return;
    if (plot.state === "empty") return;
    if (plot.state === "planted") {
      if (this.water <= 0) {
        this.setMessage("没有水啦");
        return;
      }
      this.water -= 1;
      plot.state = "ready";
      this.setMessage(plot.crop ? `${plot.crop.name} 可以收获啦` : "可以收获啦");
      return;
    }
    if (plot.state === "ready") {
      if (plot.crop) {
        this.inventory[plot.crop.key] = (this.inventory[plot.crop.key] || 0) + 1;
        this.gainXp(1);
      }
      plot.state = "empty";
      plot.crop = null;
      this.setMessage("收获成功");
    }
  };

  global.GameState = GameState;
})(typeof window !== "undefined" ? window : globalThis);
