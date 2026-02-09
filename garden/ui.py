# -*- coding: utf-8 -*-
from typing import Optional, Tuple

import pygame

from garden.models import FLOWER_TYPES, GameState, Order


STATE_LABELS = {
    "empty": "EMPTY",
    "planted": "PLANTED",
    "ready": "READY",
}

MENU_LABELS = {
    "red_rose": "红玫瑰 (Red Rose)",
    "white_lily": "白百合 (White Lily)",
    "eucalyptus": "尤加利叶 (Eucalyptus)",
}


class GardenUI:
    def __init__(self, state: GameState) -> None:
        self.state = state
        pygame.init()
        pygame.display.set_caption("Garden MVP")

        self.width = 720
        self.height = 680
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.bg_color = (244, 241, 236)
        self.panel_color = (228, 222, 214)
        self.tile_color = (247, 245, 241)
        self.tile_border = (140, 129, 116)
        self.text_color = (25, 23, 20)
        self.accent_color = (96, 82, 69)

        self.font = self._load_font(20, bold=False)
        self.font_small = self._load_font(16, bold=False)
        self.font_bold = self._load_font(20, bold=True)

        self.grid_size = 3
        self.PADDING = 24
        self.GAP = 14
        self.TOP_H = 80
        self.BOTTOM_H = 44
        self.XP_BAR_W = 320
        self.XP_BAR_H = 16
        self.SIDE_W = 200

        self.tile_size = 120
        self.grid_gap = self.GAP
        self.grid_top = 0
        self.grid_left = 0

        self.inventory_rect = pygame.Rect(0, 0, 110, 32)
        self.message_rect = pygame.Rect(0, 0, 0, 0)
        self.xp_bar_rect = pygame.Rect(0, 0, self.XP_BAR_W, self.XP_BAR_H)
        self.content_rect = pygame.Rect(0, 0, 0, 0)
        self.side_rect = pygame.Rect(0, 0, 0, 0)
        self.grid_rect = pygame.Rect(0, 0, 0, 0)
        self.active_modal: Optional[str] = None
        self.menu_rect = pygame.Rect(0, 0, 260, 220)
        self.menu_entries: list[tuple[str, bool, str]] = []
        self.menu_buttons: dict[str, pygame.Rect] = {}
        self.pending_plot: Optional[Tuple[int, int]] = None
        self.inventory_rect_modal = pygame.Rect(0, 0, 260, 200)
        self.inventory_close_rect = pygame.Rect(0, 0, 0, 0)
        self.order_buttons: list[pygame.Rect] = []

        self.layout()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            self.state.update_orders(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.draw()
            pygame.display.flip()

        pygame.quit()

    def _load_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        candidates = [
            "PingFang SC",
            "Heiti SC",
            "Hiragino Sans GB",
            "Microsoft YaHei",
            "SimHei",
            "Arial Unicode MS",
            "Noto Sans CJK SC",
        ]
        font = pygame.font.SysFont(candidates, size, bold=bold)
        return font

    def handle_click(self, pos: Tuple[int, int]) -> None:
        if self.active_modal == "plant_menu":
            if self.handle_menu_click(pos):
                return
            self.active_modal = None
            self.pending_plot = None
            self.state.message = "Cancelled"
            return
        if self.active_modal == "inventory":
            if self.handle_inventory_click(pos):
                return
            self.active_modal = None
            return
        if self.inventory_rect.collidepoint(pos):
            self.pending_plot = None
            self.active_modal = "inventory"
            return
        if self.side_rect.collidepoint(pos):
            if self.handle_order_click(pos):
                return

        row_col = self.get_plot_at_pos(pos)
        if row_col is None:
            return
        row, col = row_col
        plot = self.state.plots[row][col]
        if plot.state == "empty":
            self.active_modal = "plant_menu"
            self.pending_plot = (row, col)
            return
        self.state.click_plot(row, col)

    def get_plot_at_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        x, y = pos
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                rect = self.get_plot_rect(row, col)
                if rect.collidepoint(x, y):
                    return row, col
        return None

    def get_plot_rect(self, row: int, col: int) -> pygame.Rect:
        x = self.grid_left + col * (self.tile_size + self.grid_gap)
        y = self.grid_top + row * (self.tile_size + self.grid_gap)
        return pygame.Rect(x, y, self.tile_size, self.tile_size)

    def show_inventory(self) -> None:
        self.active_modal = "inventory"

    def draw(self) -> None:
        self.screen.fill(self.bg_color)

        self.layout()

        water_text = self.font_bold.render(f"water: {self.state.water}", True, self.text_color)
        self.screen.blit(water_text, (self.PADDING, self.PADDING + 10))
        coins_text = self.font.render(f"coins: {self.state.coins}", True, self.text_color)
        self.screen.blit(coins_text, (self.PADDING + 140, self.PADDING + 12))

        pygame.draw.rect(self.screen, self.panel_color, self.inventory_rect, border_radius=6)
        inv_text = self.font.render("Inventory", True, self.text_color)
        inv_text_rect = inv_text.get_rect(center=self.inventory_rect.center)
        self.screen.blit(inv_text, inv_text_rect)

        level_text = self.font.render(f"Level: {self.state.level}", True, self.text_color)
        level_rect = level_text.get_rect(center=(self.width // 2, self.PADDING + 14))
        self.screen.blit(level_text, level_rect)
        self.draw_xp_bar()

        self.draw_orders_panel()

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                rect = self.get_plot_rect(row, col)
                pygame.draw.rect(self.screen, self.tile_color, rect, border_radius=8)
                pygame.draw.rect(self.screen, self.tile_border, rect, width=2, border_radius=8)
                plot = self.state.plots[row][col]
                label = self.get_plot_label(plot)
                label_text = self.font.render(label, True, self.accent_color)
                label_rect = label_text.get_rect(center=rect.center)
                self.screen.blit(label_text, label_rect)

        pygame.draw.rect(self.screen, self.panel_color, self.message_rect, border_radius=6)
        self.draw_message_lines(self.state.message)

        if self.active_modal == "plant_menu":
            self.draw_menu()
        if self.active_modal == "inventory":
            self.draw_inventory_modal()

    def _build_menu_buttons(
        self, entries: list[tuple[str, bool, str]]
    ) -> dict[str, pygame.Rect]:
        buttons: dict[str, pygame.Rect] = {}
        start_x = self.menu_rect.x + 20
        start_y = self.menu_rect.y + 50
        width = self.menu_rect.width - 40
        height = 32
        gap = 12
        for idx, (key, _enabled, _label) in enumerate(entries):
            y = start_y + idx * (height + gap)
            buttons[key] = pygame.Rect(start_x, y, width, height)
        return buttons

    def handle_menu_click(self, pos: Tuple[int, int]) -> bool:
        if not self.menu_rect.collidepoint(pos):
            return False
        for key, rect in self.menu_buttons.items():
            if rect.collidepoint(pos):
                if key == "cancel":
                    self.active_modal = None
                    self.pending_plot = None
                    self.state.message = "Cancelled"
                    return True
                entry = next((e for e in self.menu_entries if e[0] == key), None)
                if entry and not entry[1]:
                    self.state.message = "未解锁"
                    return True
                if self.pending_plot:
                    row, col = self.pending_plot
                    self.state.plant_flower(row, col, key)
                self.active_modal = None
                self.pending_plot = None
                return True
        return True

    def draw_menu(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, self.panel_color, self.menu_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.tile_border, self.menu_rect, width=2, border_radius=8)

        title = self.font_bold.render("Choose a flower", True, self.text_color)
        title_rect = title.get_rect(center=(self.menu_rect.centerx, self.menu_rect.y + 24))
        self.screen.blit(title, title_rect)

        for key, rect in self.menu_buttons.items():
            pygame.draw.rect(self.screen, self.tile_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, self.tile_border, rect, width=2, border_radius=6)
            if key == "cancel":
                label = "Cancel"
                color = self.text_color
            else:
                entry = next((e for e in self.menu_entries if e[0] == key), None)
                label = entry[2] if entry else MENU_LABELS.get(key, key)
                color = self.text_color if entry is None or entry[1] else (120, 110, 100)
            text = self.font_small.render(label, True, color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def handle_inventory_click(self, pos: Tuple[int, int]) -> bool:
        if not self.inventory_rect_modal.collidepoint(pos):
            return False
        if self.inventory_close_rect.collidepoint(pos):
            self.active_modal = None
            return True
        return True

    def draw_inventory_modal(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            self.screen, self.panel_color, self.inventory_rect_modal, border_radius=8
        )
        pygame.draw.rect(
            self.screen, self.tile_border, self.inventory_rect_modal, width=2, border_radius=8
        )

        title = self.font_bold.render("Inventory", True, self.text_color)
        title_rect = title.get_rect(
            center=(self.inventory_rect_modal.centerx, self.inventory_rect_modal.y + 24)
        )
        self.screen.blit(title, title_rect)

        red = self.state.inventory.get("red_rose", 0)
        lily = self.state.inventory.get("white_lily", 0)
        eucalyptus = self.state.inventory.get("eucalyptus", 0)

        lines = [
            f"Red Rose: {red}",
            f"White Lily: {lily}",
            f"Eucalyptus: {eucalyptus}",
        ]
        start_y = self.inventory_rect_modal.y + 60
        for idx, line in enumerate(lines):
            text = self.font_small.render(line, True, self.text_color)
            self.screen.blit(
                text, (self.inventory_rect_modal.x + 20, start_y + idx * 20)
            )

        pygame.draw.rect(
            self.screen, self.tile_color, self.inventory_close_rect, border_radius=6
        )
        pygame.draw.rect(
            self.screen, self.tile_border, self.inventory_close_rect, width=2, border_radius=6
        )
        close_text = self.font_small.render("Close", True, self.text_color)
        close_rect = close_text.get_rect(center=self.inventory_close_rect.center)
        self.screen.blit(close_text, close_rect)

    def draw_message_lines(self, message: str) -> None:
        lines = message.splitlines() if message else [""]
        start_y = self.message_rect.y + 6
        for idx, line in enumerate(lines[:3]):
            text = self.font_small.render(line, True, self.text_color)
            self.screen.blit(text, (self.message_rect.x + 10, start_y + idx * 14))

    def get_plot_label(self, plot) -> str:
        if plot.state == "empty":
            return "EMPTY"
        if plot.state == "planted":
            name = plot.crop.name if plot.crop else "-"
            return f"PLANTED - {name}"
        if plot.state == "ready":
            return plot.crop.name if plot.crop else "READY"
        return plot.state

    def draw_xp_bar(self) -> None:
        pygame.draw.rect(self.screen, self.panel_color, self.xp_bar_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.tile_border, self.xp_bar_rect, width=2, border_radius=6)

        required = self.state.xp_required()
        if required is None:
            fill_width = self.xp_bar_rect.width
            label = "MAX"
        else:
            ratio = 0 if required <= 0 else min(self.state.xp / required, 1.0)
            fill_width = int(self.xp_bar_rect.width * ratio)
            label = f"{self.state.xp}/{required}"

        fill_rect = pygame.Rect(
            self.xp_bar_rect.x,
            self.xp_bar_rect.y,
            fill_width,
            self.xp_bar_rect.height,
        )
        pygame.draw.rect(self.screen, (196, 176, 154), fill_rect, border_radius=6)
        label_text = self.font_small.render(label, True, self.text_color)
        label_rect = label_text.get_rect(center=self.xp_bar_rect.center)
        self.screen.blit(label_text, label_rect)

    def build_menu_entries(self) -> list[tuple[str, bool, str]]:
        unlocks = self.state.flower_unlocks or {}
        items = sorted(unlocks.items(), key=lambda kv: kv[1])
        current = self.state.level
        next_level = None
        for _key, level in items:
            if level > current:
                next_level = level
                break
        entries: list[tuple[str, bool, str]] = []
        for key, level in items:
            if level <= current:
                entries.append((key, True, MENU_LABELS.get(key, key)))
            elif next_level is not None and level == next_level:
                label = MENU_LABELS.get(key, key)
                entries.append((key, False, f"{label} - Lv {level}"))
        entries.append(("cancel", True, "Cancel"))
        return entries

    def draw_orders_panel(self) -> None:
        pygame.draw.rect(self.screen, self.panel_color, self.side_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.tile_border, self.side_rect, width=2, border_radius=8)

        title = self.font_bold.render("Orders", True, self.text_color)
        self.screen.blit(title, (self.side_rect.x + 12, self.side_rect.y + 10))

        if len(self.state.orders) >= self.state.max_orders:
            timer_text = "Next order: Full"
        else:
            timer_text = f"Next order in: {max(0, int(self.state.order_timer))}s"
        timer = self.font_small.render(timer_text, True, self.text_color)
        self.screen.blit(timer, (self.side_rect.x + 12, self.side_rect.y + 34))

        self.order_buttons = []
        y = self.side_rect.y + 60
        for idx, order in enumerate(self.state.orders[: self.state.max_orders]):
            card_rect = pygame.Rect(
                self.side_rect.x + 10, y, self.side_rect.width - 20, 102
            )
            pygame.draw.rect(self.screen, self.tile_color, card_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.tile_border, card_rect, width=1, border_radius=6)

            title = self.font_small.render(f"Order {idx + 1}", True, self.text_color)
            self.screen.blit(title, (card_rect.x + 8, card_rect.y + 6))

            lines = self.format_order_lines(order)
            for li, (line, ok) in enumerate(lines):
                color = self.text_color if ok else (150, 80, 80)
                text = self.font_small.render(line, True, color)
                self.screen.blit(text, (card_rect.x + 8, card_rect.y + 24 + li * 16))

            reward_text = self.font_small.render(
                f"Reward: {order.reward} coins", True, self.text_color
            )
            self.screen.blit(reward_text, (card_rect.x + 8, card_rect.y + 72))

            deliver_rect = pygame.Rect(
                card_rect.right - 86,
                card_rect.bottom - 26,
                76,
                22,
            )
            can_deliver = self.state.can_fulfill(order)
            fill = self.panel_color if can_deliver else (205, 198, 190)
            pygame.draw.rect(self.screen, fill, deliver_rect, border_radius=4)
            pygame.draw.rect(self.screen, self.tile_border, deliver_rect, width=1, border_radius=4)
            label = self.font_small.render("Deliver", True, self.text_color)
            self.screen.blit(label, (deliver_rect.x + 10, deliver_rect.y + 3))
            self.order_buttons.append(deliver_rect)

            y += 110

    def format_order_lines(self, order: Order) -> list[tuple[str, bool]]:
        parts: list[tuple[str, bool]] = []
        for key, qty in order.requirements.items():
            name = FLOWER_TYPES.get(key, key)
            owned = self.state.inventory.get(key, 0)
            ok = owned >= qty
            parts.append((f"{name} x{qty} (owned {owned})", ok))
        return parts

    def handle_order_click(self, pos: Tuple[int, int]) -> bool:
        if not self.order_buttons:
            return False
        for idx, rect in enumerate(self.order_buttons):
            if rect.collidepoint(pos):
                if idx < len(self.state.orders) and self.state.can_fulfill(
                    self.state.orders[idx]
                ):
                    self.state.deliver_order(idx)
                else:
                    self.state.message = "Not enough flowers"
                return True
        return False

    def layout(self) -> None:
        self.content_rect = pygame.Rect(
            0, self.TOP_H, self.width, self.height - self.TOP_H - self.BOTTOM_H
        )

        self.side_rect = pygame.Rect(
            self.PADDING,
            self.content_rect.y + self.PADDING,
            self.SIDE_W,
            self.content_rect.height - self.PADDING * 2,
        )
        self.grid_rect = pygame.Rect(
            self.side_rect.right + self.GAP,
            self.content_rect.y + self.PADDING,
            self.width - self.PADDING - (self.side_rect.right + self.GAP),
            self.content_rect.height - self.PADDING * 2,
        )

        self.message_rect = pygame.Rect(
            self.PADDING,
            self.height - self.BOTTOM_H + 6,
            self.width - self.PADDING * 2,
            self.BOTTOM_H - 12,
        )

        self.inventory_rect = pygame.Rect(
            self.width - self.PADDING - 110,
            self.PADDING + 6,
            110,
            32,
        )

        self.xp_bar_rect = pygame.Rect(
            self.width // 2 - self.XP_BAR_W // 2,
            self.PADDING + 38,
            self.XP_BAR_W,
            self.XP_BAR_H,
        )

        avail_w = self.content_rect.width - self.PADDING * 2
        avail_h = self.content_rect.height - self.PADDING * 2
        total_gap = self.grid_gap * (self.grid_size - 1)
        size_by_w = (self.grid_rect.width - total_gap) // self.grid_size
        size_by_h = (self.grid_rect.height - total_gap) // self.grid_size
        self.tile_size = max(60, min(size_by_w, size_by_h))

        grid_w = self.tile_size * self.grid_size + total_gap
        grid_h = self.tile_size * self.grid_size + total_gap
        self.grid_left = self.grid_rect.x + (self.grid_rect.width - grid_w) // 2
        self.grid_top = self.grid_rect.y + (self.grid_rect.height - grid_h) // 2

        self.menu_rect = pygame.Rect(
            self.width // 2 - 130,
            self.content_rect.y + (self.content_rect.height - 220) // 2,
            260,
            220,
        )
        self.menu_entries = self.build_menu_entries()
        self.menu_buttons = self._build_menu_buttons(self.menu_entries)

        self.inventory_rect_modal = pygame.Rect(
            self.width // 2 - 130,
            self.content_rect.y + (self.content_rect.height - 200) // 2,
            260,
            200,
        )
        self.inventory_close_rect = pygame.Rect(
            self.inventory_rect_modal.x + 60,
            self.inventory_rect_modal.y + 140,
            self.inventory_rect_modal.width - 120,
            32,
        )


def run_app(state: GameState) -> None:
    ui = GardenUI(state)
    ui.run()
