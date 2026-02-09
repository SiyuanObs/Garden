# -*- coding: utf-8 -*-
from typing import Optional, Tuple

import pygame

from garden.models import FLOWER_LABELS, FLOWER_TYPES, GameState


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

        self.width = 520
        self.height = 560
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
        self.tile_size = 120
        self.grid_gap = 16
        self.grid_top = 130
        self.grid_left = (self.width - (self.tile_size * self.grid_size + self.grid_gap * 2)) // 2

        self.inventory_rect = pygame.Rect(self.width - 140, 22, 110, 32)
        self.message_rect = pygame.Rect(24, self.height - 60, self.width - 48, 36)
        self.xp_bar_rect = pygame.Rect(24, 56, self.width - 48, 18)
        self.active_modal: Optional[str] = None
        self.menu_rect = pygame.Rect(140, 160, 240, 220)
        self.menu_buttons = self._build_menu_buttons()
        self.pending_plot: Optional[Tuple[int, int]] = None
        self.inventory_rect_modal = pygame.Rect(140, 160, 240, 200)
        self.inventory_close_rect = pygame.Rect(
            self.inventory_rect_modal.x + 60,
            self.inventory_rect_modal.y + 140,
            self.inventory_rect_modal.width - 120,
            32,
        )

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

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

        water_text = self.font_bold.render(f"water: {self.state.water}", True, self.text_color)
        self.screen.blit(water_text, (24, 26))

        pygame.draw.rect(self.screen, self.panel_color, self.inventory_rect, border_radius=6)
        inv_text = self.font.render("Inventory", True, self.text_color)
        inv_text_rect = inv_text.get_rect(center=self.inventory_rect.center)
        self.screen.blit(inv_text, inv_text_rect)

        level_text = self.font.render(f"Level: {self.state.level}", True, self.text_color)
        self.screen.blit(level_text, (24, 84))
        self.draw_xp_bar()

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

    def _build_menu_buttons(self) -> dict[str, pygame.Rect]:
        buttons: dict[str, pygame.Rect] = {}
        start_x = self.menu_rect.x + 20
        start_y = self.menu_rect.y + 50
        width = self.menu_rect.width - 40
        height = 32
        gap = 12
        order = ["red_rose", "white_lily", "eucalyptus", "cancel"]
        for idx, key in enumerate(order):
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
            else:
                label = MENU_LABELS.get(key, key)
            text = self.font_small.render(label, True, self.text_color)
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


def run_app(state: GameState) -> None:
    ui = GardenUI(state)
    ui.run()
