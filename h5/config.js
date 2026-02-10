/**
 * 与 config/*.json 一致的配置，供 H5 静态使用
 */
const CONFIG = {
  level_xp: { 1: 10, 2: 50 },
  flower_unlocks: { red_rose: 1, white_lily: 2, eucalyptus: 3 },
  flower_values: { red_rose: 3, white_lily: 5, eucalyptus: 7 },
  plot_unlock_costs: [
    [0, 20, 100],
    [20, 50, 300],
    [100, 300, 1000],
  ],
};

const FLOWER_TYPES = {
  red_rose: "Red Rose",
  white_lily: "White Lily",
  eucalyptus: "Eucalyptus",
};

const FLOWER_LABELS = {
  red_rose: "红玫瑰",
  white_lily: "白百合",
  eucalyptus: "尤加利叶",
};

if (typeof window !== "undefined") {
  window.CONFIG = CONFIG;
  window.FLOWER_TYPES = FLOWER_TYPES;
  window.FLOWER_LABELS = FLOWER_LABELS;
}
