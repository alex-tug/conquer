__author__ = 'Ace'
import pygame
from vec_2d import Vec2d
#from classcollection import FontContainer


# Simple Font Container (could be done in a better way ...)
class FontContainer(object):
    def __init__(self):
        # Load four different fonts.
        self.font_1 = pygame.font.Font(None, 12)
        self.font_2 = pygame.font.Font(None, 16)
        self.font_3 = pygame.font.Font(None, 24)
        self.font_4 = pygame.font.Font("yanone_regular.otf", 20)


# a class with some functions to plot text, etc. on screen
class Plotter(object):  # ... kind of stupid name
    def __init__(self, screen, pos_0=Vec2d(0, 0)):

        self.screen = screen
        self.cur_color = pygame.Color('black')

        self.fonts = FontContainer()
        self.cur_font = self.fonts.font_1

        # offset to shift all plots
        self.pos_0 = pos_0

    def text_at(self,
                text,
                pos,
                wipe_background=True,
                drop_shadow=False,
                font=None,
                color=None,
                flip_now_flag=False):
        """
        Render text
        text -> text to be drawn
        pos -> coordinates as Vec2d(x,y)
        wipe_background = True -> draw a box behing the text
        cur_font = self.fonts.font_2 -> font to be used
        color = (255,255,255) -> font color
        flip_now_flag = False -> immediately flip the screen
        """
        assert isinstance(pos, Vec2d)
        if color is None:
            color = self.cur_color
        if font is None:
            font = self.cur_font

        # Render text
        text_rendered = font.render(text, 1, color)

        # Wipe_Background
        corner_2 = font.size(text)
        if wipe_background:
            pygame.draw.rect(self.screen, (0, 0, 0), (self.pos_0.x + pos.x - corner_2[0]/2, self.pos_0.y + pos.y,
                                                      self.pos_0.x + corner_2[0], self.pos_0.y + corner_2[1]))

        # Shadow
        if drop_shadow:
            shadow_text_ = font.render(text, 1, (255 - color[0], 255 - color[1], 255 - color[2]))
            self.screen.blit(shadow_text_, self.pos_0 + pos - Vec2d(corner_2[0]/2, 0) + Vec2d(1, 1))

        # Draw the text on a screen
        self.screen.blit(text_rendered, self.pos_0 + pos - Vec2d(corner_2[0]/2, 0))
        if flip_now_flag:
            pygame.display.flip()
