import pygame


class HealthBar:
    def __init__(self, max_hits=5, pos=(4, 4), size=(60, 10), bg_color=(40, 40, 40), fg_color=(200, 30, 30), border_color=(255,255,255)):
        self.max_hits = max_hits
        self.pos = pos
        self.size = size
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_color = border_color

    def render(self, surf, hits):
        # hits = number of times player was hit; health remaining = max_hits - hits
        remaining = max(0, self.max_hits - hits)
        w, h = self.size
        x, y = self.pos

        # background
        pygame.draw.rect(surf, self.bg_color, (x, y, w, h))

        # foreground fill based on remaining health
        ratio = remaining / max(1, self.max_hits)
        fill_w = int(w * ratio)
        if fill_w > 0:
            pygame.draw.rect(surf, self.fg_color, (x, y, fill_w, h))

        # border
        pygame.draw.rect(surf, self.border_color, (x, y, w, h), 1)

        # optional: draw numbers
        try:
            font = pygame.font.Font(None, 12)
            txt = font.render(f"{remaining}/{self.max_hits}", True, (255, 255, 255))
            surf.blit(txt, (x + 2, y + (h - txt.get_height()) // 2))
        except Exception:
            # if fonts not initialized yet, ignore
            pass

    def render_with_items(self, surf, hits, items: dict = None):
        """Render the healthbar and (optionally) item counts below it.

        items: dict like {'shuriken': 10, 'sword': 3}
        """
        self.render(surf, hits)
        if not items:
            return

        x, y = self.pos
        w, h = self.size
        # draw small labels under the healthbar
        try:
            font = pygame.font.Font(None, 14)
            off_y = y + h + 4
            spacing = 6
            cur_x = x
            for key, val in items.items():
                # val may be int (count) or tuple (count, cooldown_ratio, image_surf)
                count = 0
                cooldown = 0
                img = None
                if isinstance(val, (list, tuple)):
                    if len(val) > 0:
                        count = val[0]
                    if len(val) > 1:
                        cooldown = val[1]
                    if len(val) > 2:
                        img = val[2]
                else:
                    count = val

                # draw icon (image if available)
                icon_size = h
                if img:
                    try:
                        icon_surf = pygame.transform.scale(img, (icon_size, icon_size))
                        surf.blit(icon_surf, (cur_x, off_y))
                        # cooldown overlay: draw from top proportionally to cooldown (0..1)
                        if cooldown and cooldown > 0:
                            overlay = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                            cover_h = int(icon_size * cooldown)
                            overlay.fill((0, 0, 0, 160), rect=(0, 0, icon_size, cover_h))
                            surf.blit(overlay, (cur_x, off_y))
                        # draw count to the right of icon
                        surf_txt = font.render(f"x{count}", True, (255, 255, 255))
                        surf.blit(surf_txt, (cur_x + icon_size + 4, off_y + (icon_size - surf_txt.get_height()) // 2))
                        cur_x += icon_size + surf_txt.get_width() + spacing + 4
                        continue
                    except Exception:
                        # if image drawing fails, fall back to glyph
                        pass

                # fallback glyph icon
                icon = ''
                if key.lower().startswith('sh'):
                    icon = '◦'  # placeholder for shuriken
                elif key.lower().startswith('ku') or key.lower().startswith('kn'):
                    icon = '⚔'  # placeholder for kunai
                else:
                    icon = key[0].upper()

                text = f"{icon} x{count}"
                surf_txt = font.render(text, True, (255, 255, 255))
                surf.blit(surf_txt, (cur_x, off_y))
                cur_x += surf_txt.get_width() + spacing
        except Exception:
            pass
