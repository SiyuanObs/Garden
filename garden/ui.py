# -*- coding: utf-8 -*-
from typing import Optional, Tuple

import pygame

from garden.models import GameState


STATE_LABELS = {
    "empty": "EMPTY",
    "planted": "PLANTED",
    "ready": "READY",
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
        self.grid_top = 90
        self.grid_left = (self.width - (self.tile_size * self.grid_size + self.grid_gap * 2)) // 2

        self.inventory_rect = pygame.Rect(self.width - 140, 22, 110, 32)
        self.message_rect = pygame.Rect(24, self.height - 60, self.width - 48, 36)

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
        if self.inventory_rect.collidepoint(pos):
            self.show_inventory()
            return

        row_col = self.get_plot_at_pos(pos)
        if row_col is None:
            return
        row, col = row_col
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
        roses = self.state.inventory.get("红玫瑰", 0)
        self.state.message = f"Red Rose: {roses} / 红玫瑰：{roses}"

    def draw(self) -> None:
        self.screen.fill(self.bg_color)

        water_text = self.font_bold.render(f"water: {self.state.water}", True, self.text_color)
        self.screen.blit(water_text, (24, 26))

        pygame.draw.rect(self.screen, self.panel_color, self.inventory_rect, border_radius=6)
        inv_text = self.font.render("Inventory", True, self.text_color)
        inv_text_rect = inv_text.get_rect(center=self.inventory_rect.center)
        self.screen.blit(inv_text, inv_text_rect)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                rect = self.get_plot_rect(row, col)
                pygame.draw.rect(self.screen, self.tile_color, rect, border_radius=8)
                pygame.draw.rect(self.screen, self.tile_border, rect, width=2, border_radius=8)
                plot = self.state.plots[row][col]
                label = STATE_LABELS.get(plot.state, plot.state)
                label_text = self.font.render(label, True, self.accent_color)
                label_rect = label_text.get_rect(center=rect.center)
                self.screen.blit(label_text, label_rect)

        pygame.draw.rect(self.screen, self.panel_color, self.message_rect, border_radius=6)
        message_text = self.font_small.render(self.state.message, True, self.text_color)
        self.screen.blit(message_text, (self.message_rect.x + 10, self.message_rect.y + 9))


def run_app(state: GameState) -> None:
    ui = GardenUI(state)
    ui.run()
