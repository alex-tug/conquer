import pygame
from vec_2d import Vec2d
import time
from types import *

from graphics_helper import Plotter

#------------------------------------------------------------------------
#
#    This file is part of Conquer.
#
#    Conquer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Conquer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Conquer.  If not, see <http://www.gnu.org/licenses/>.
#
#    Copyright Conquer Development Team (http://code.google.com/p/pyconquer/)
#
#------------------------------------------------------------------------

class TGameMenu:
    def __init__(self, screen, bg_image, logo1, menu_items, start_vec, spacing=50):
        # Currently selected menuitem's index
        self.pos = 0
        # List of menuitems
        self.menu_items = menu_items
        # Pointer to pygame screen
        self.screen = screen
        # Coordinates where to render the menu
        self.start_vec = start_vec
        # Space between menuitems
        self.spacing = spacing
        # Background picture is oddly here as well the top logo
        self.bg = bg_image
        self.logo = logo1

        self.plotter = Plotter(self.screen)
        # Font to be used with the menu
        self.used_font = pygame.font.Font("yanone_regular.otf", 24)
        self.plotter.cur_font = self.used_font

    def draw_items(self, text=None):
        # If images and/or text are supplied, draw them
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        if self.logo:
            self.screen.blit(self.logo, (263, 0))
        if text:
            self.plotter.text_at(text[0], Vec2d(text[1], text[2]),
                    font=self.used_font, wipe_background=True, color=(255, 255, 255))

        # Iterate through menu items
        for i, item_i in enumerate(self.menu_items):
            # FIXME: skinnable colors

            # Menu item color is white
            cur_color = (0, 0, 0)
            shadow = True
            if i == self.pos:
                # Selected menu item is red
                shadow = False
                cur_color = (255, 0, 0)
            # Text to be rendered
            text = item_i[0]
            # Check if menu items are value editors
            if len(item_i[2]) >= 2:
                if item_i[2][0] == "value_int_editor":
                    text = "%s (%d)" % (text, item_i[2][1])
                if item_i[2][0] == "value_bool_editor":
                    if item_i[2][1]:
                        text = "%s (%s)" % (text, "on")
                    else:
                        text = "%s (%s)" % (text, "off")

            # Draw the menu item text
            self.plotter.text_at(text,
                    self.start_vec + Vec2d(0, self.spacing) * i,
                    color=cur_color,
                    wipe_background=False,
                    drop_shadow=shadow
            )

        # Caption Text
        if self.menu_items[self.pos][3]:
            # It has caption text, draw it
            self.plotter.text_at(self.menu_items[self.pos][3],
                                 Vec2d(400, 75))

        # Some info :)
        tmp_color = (50, 185, 10)
        self.plotter.text_at("Contact:", Vec2d(400, 520),
                             color=tmp_color,
                             wipe_background=False)
        self.plotter.text_at("Conquer Dev Team http://pyconquer.googlecode.com/",
                             Vec2d(400, 545),
                             color=tmp_color,
                             wipe_background=False)

    def scroll(self, dy):
        # Change the selected menu item
        self.pos += dy
        if self.pos < 0:
            self.pos = len(self.menu_items) - 1
        if self.pos == len(self.menu_items):
            self.pos = 0

    def edit_value(self, dv):
        # This is totally unreadable :D
        # Well it edits values in their border values
        if len(self.menu_items[self.pos][2]) >= 2:
            if self.menu_items[self.pos][2][0] == "value_int_editor":
                self.menu_items[self.pos][2][1] += dv
                if len(self.menu_items[self.pos][2]) >= 3:
                    if self.menu_items[self.pos][2][1] < self.menu_items[self.pos][2][2][0]:
                        self.menu_items[self.pos][2][1] = self.menu_items[self.pos][2][2][0]
                    if self.menu_items[self.pos][2][1] > self.menu_items[self.pos][2][2][1]:
                        self.menu_items[self.pos][2][1] = self.menu_items[self.pos][2][2][1]
            if self.menu_items[self.pos][2][0] == "value_bool_editor":
                self.menu_items[self.pos][2][1] = not self.menu_items[self.pos][2][1]

    def get_selection(self, text=None):
        """
        Render the menu as long as user selects a menuitem
        text -> optional text to be rendered
        """

        # Draw the items
        self.draw_items(text)

        # Create instance of pygame Clock
        clock = pygame.time.Clock()

        # Endless loop
        while True:
            # Limit fps to 30
            clock.tick(30)

            # Iterate through events
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_DOWN:
                        self.scroll(1)
                        self.draw_items(text)
                    if e.key == pygame.K_UP:
                        self.scroll(-1)
                        self.draw_items(text)
                    if e.key == pygame.K_RETURN:
                        choice = self.select()
                        return choice
                    if e.key == pygame.K_LEFT:
                        self.edit_value(-1)
                        self.draw_items(text)
                    if e.key == pygame.K_RIGHT:
                        self.edit_value(1)
                        self.draw_items(text)
            pygame.display.flip()

    def select(self):
        # User selects a menu item
        return self.menu_items[self.pos][1]

# end of class TGameMenu
###################################################################


def text_input(plotter, caption, corner_1, span_vec, fonts, only_numbers=False):
    # Make an input-box and prompt it for input
    assert isinstance(corner_1, Vec2d)
    x1 = corner_1.x
    y1 = corner_1.y
    assert isinstance(span_vec, Vec2d)
    w1 = span_vec.x
    h1 = span_vec.y

    cur_str = []
    pygame.draw.rect(plotter.screen, (30, 30, 30), (x1, y1, w1, h1))
    plotter.text_at(caption, Vec2d(x1 + w1 / 4, y1), font=fonts.font_2, wipe_background=False)
    pygame.display.flip()

    done = False
    while not done:
        for e in pygame.event.get():
            key = None
            #e = pygame.event.poll()
            if e.type == pygame.NOEVENT:
                # event queue is empty
                time.sleep(0.1)
                continue

            if e.type == pygame.KEYDOWN:
                key = e.key
            else:
                continue

            if key == pygame.K_BACKSPACE:
                if cur_str:
                    del cur_str[len(cur_str) - 1]
                    done = True

            elif key == pygame.K_RETURN:
                done = True

            if (key <= 127) and (key != pygame.K_BACKSPACE):
                if only_numbers:
                    if chr(key) in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                        cur_str.append(chr(key))
                else:
                    cur_str.append(chr(key))

            cur_text_pos = Vec2d(x1 + (w1 / 2) - (len(cur_str) * 4), y1 + 15)
            cur_font = fonts.font_4

            plotter.text_at("".join(cur_str),
                                cur_text_pos,
                                wipe_background=False,
                                font=cur_font)
            pygame.display.flip()
    return "".join(cur_str)


def load_image_files_but_not_interface_image_files(image_handler, graphics_path):
    tmp = pygame.image.load(graphics_path + "skull7.png").convert_alpha()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "skull")

    tmp = pygame.image.load(graphics_path + "soldier.png").convert_alpha()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "soldier")

    tmp = pygame.image.load(graphics_path + "armytent.png").convert_alpha()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "town")

    tmp = pygame.image.load(graphics_path + "hextile2_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_1")

    tmp = pygame.image.load(graphics_path + "hextile_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_2")

    tmp = pygame.image.load(graphics_path + "hextile3_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_3")

    tmp = pygame.image.load(graphics_path + "hextile4_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_4")

    tmp = pygame.image.load(graphics_path + "hextile5_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_5")

    tmp = pygame.image.load(graphics_path + "hextile6_.png").convert()
    tmp.set_colorkey(tmp.get_at((0, 0)))
    image_handler.add_image(tmp, "cell_6")

    image_handler.add_image(pygame.image.load(graphics_path + "teksti.png").convert(), "logo")
    image_handler.add_image(pygame.image.load(graphics_path + "mapedit.png").convert(), "mapedit")


def get_human_and_cpu_count(screen, fonts):
    # This is very ugly piece of code.
    # It ask for scenario editing and random generated map,
    # how many human and cpu players will participate.

    max_player = 6

    text_pos = Vec2d(800 / 2 - 110, 300)
    span_vec = Vec2d(240, 45)

    # get number of human players
    nr_of_h = 0
    while True:
        #input_raw = text_input(screen, 'How many human players (1-6)?',
        #                       text_pos, span_vec, fonts, only_numbers=True)
        # DEBUG:
        input_raw = '2'

        try:
            nr_of_h = int(input_raw)
        except:
            continue
        if 1 <= nr_of_h <= max_player:
            break

    # get number of ai players
    nr_of_c = 0
    min_nr_of_ai = 0
    if nr_of_h < max_player:
        if nr_of_h == 1:
            min_nr_of_ai = 1
        while True:
            #input_raw = text_input(screen,
            #                       'How many cpu players (%d-%d)?' % (min_nr_of_ai, max_player - nr_of_h),
            #                       text_pos, span_vec, fonts, only_numbers=True)
            # DEBUG:
            input_raw = '2'

            try:
                nr_of_c = int(input_raw)
            except:
                continue

            if min_nr_of_ai <= nr_of_c <= (max_player - nr_of_h):
                break

    return nr_of_h, nr_of_c