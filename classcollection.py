from os import sep, path
import random

#import operator
from vec_2d import Vec2d
#import pygame
from types import *
import pygame

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

#==============================================================================
#
# general classes:

# None

#==============================================================================
#
# classes used for the map:
#
# strucure of class-inheritance:
#
#     Town
#     |
#     \-- City
#
#     Building
#     |
#     \-- Factory
#         
#     Unit
#     |
#     \--Soldier
#


class Cell(object):
    """
    The map consists of a 2-dimensional array (dict) of cells
    there is no smaller step on the map than a cell
    """

    def __init__(self, pos, cell_type, edm_cells, province, town_flag=False):
        self.pos = pos
        # edm_cells ... the six neighbouring cells
        if not len(edm_cells) == 6:
            # the list of neighbours must always have 6 elements
            # use 'None' for empty cells or on the edge of the map
            return
        self.edm_cells = edm_cells

        if not province:
            return
        self.province = province

        # define if cell is water(=0) or any other type
        self.cell_type = cell_type

        self.town_flag = town_flag    # says if there is a town on this cell

        self.soldier = None
        self.factory = None

    def __hash__(self):
        return hash((self.pos.x, self.pos.y))

    def __eq__(self, other):
        return self.pos == other.pos

    def build_soldier(self):
        """ create a new soldier and calls append """

        # Soldier drafting function used by human player
        if not self.province:
            return

        # Get the actor instance
        soldier_to_update = self.soldier

        # Check if actor was found
        if soldier_to_update:
            # We do not update level 6 soldiers
            if soldier_to_update.level == 6:
                return

        # check if this province has supplies
        if self.province.supplies > 0:
            if self.soldier:
                if self.soldier.level == self.soldier.max_level:
                    return
                else:
                    # there's already a soldier which we will upgrade
                    self.soldier.upgrade()
                    self.province.supplies -= 1
            else:
                # no soldier => build new one
                new_soldier = Soldier(owner=self.province.owner)
                self.append_soldier(new_soldier)
                self.province.supplies -= 1

            # Update province income/expends
            self.province.update()

    def append_soldier(self, soldier):
        # bind passed soldier and this cell together
        if not self.soldier:
            self.soldier = soldier
            soldier.cur_cell = self

    def destroy_town(self):
        assert isinstance(self.province.town, Town)
        #del self.town
        if self.town_flag:
            self.province.town.destroy()  # = None

    def build_factory(self):
        # a factory won't change it's cell, so there's no seperate append_factory method
        if not self.factory:
            self.factory = Factory(cell=self)

    def destroy_factory(self):
        assert isinstance(self.factory, Factory)
        #del self.factory
        self.factory.destroy()  # = None

    def destroy_buildings(self):
        if self.factory:
            self.destroy_factory()

    def change_to_province(self, new_province):
        assert self.province
        # remove cell from old province
        self.province.remove_cell(self)
        # ... and append to new one
        new_province.append_cell(self)
        assert new_province.province_cells
        assert new_province.size() > 0

    def get_image_key(self):
        if self.province:
            if self.province.is_land is False:
                return None
            assert self.province.owner
            return 'cell_' + str(self.province.owner.id)
        else:
            if self.cell_type:
                if self.cell_type > 0:
                    return 'cell_' + str(self.cell_type)
                else:
                    return None
            else:
                return None


# Instance of town (=some kind of camp, center of each province)
class Town(object):
    def __init__(self, cell):
        self.cell = cell
        self.province = cell.province

    def destroy(self):
        if self.cell:
            self.cell.town_flag = False
        if self.province:
            self.province.town = None
            #del self    # looks strange, maybe i should rewrite destroy() as __del__


class City(Town):
    def __init__(self, cell):
        super(City, self).__init__(cell)

        # ToDo


# Base class for each building -> town, factory, etc.
class Building(object):
    def __init__(self, cell=None):
        self.dead = False
        self.cell = cell
        #self.owner = owner # might add builder or similar

    def destroy(self):
        self.dead = True

    def get_owner(self):
        if self.cell:
            if self.cell.province:
                return self.cell.province.owner
            else:
                return None
        else:
            return None


# Instance of factory (generates extra income)
class Factory(Building):
    def __init__(self, cell):
        super(Factory, self).__init__(cell)
        #self.income += 1

    def destroy(self):
        super(Factory, self).destroy()
        if self.cell:
            self.cell.factory = None
            #del self    # looks strange, maybe i should rewrite destroy() as __del__


# Base class for each unit -> Soldier, etc.
class Unit(object):
    def __init__(self, owner=0):
        self.dead = False
        self.cur_cell = None
        self.owner = owner

    def destroy(self):
        self.dead = True

    def move_to(self, target_cell):
        assert isinstance(target_cell, Cell)
        # fighting and so on should not be handled here,
        # so we can only move to a cell without soldier
        assert isinstance(target_cell.soldier, NoneType)
        target_cell.soldier = self      # append on new cell
        self.cur_cell.soldier = None    # remove from old cell
        self.cur_cell = target_cell     # set link to new cell

    def get_cur_cell(self):
        # if self.cur_cell is not used, it should be None which can be catched
        return self.cur_cell

    def set_owner(self, new_owner):
        self.owner = new_owner

    def get_owner(self):
        return self.owner


# Instance of soldier
class Soldier(Unit):
    def __init__(self, owner, level=1):
        super(Soldier, self).__init__(owner)

        self.level = level
        self.moved = False

        self.max_level = 6

    def destroy(self):
        super(Soldier, self).destroy()
        if self.cur_cell:
            self.cur_cell.soldier = None
            #del self    # looks strange, maybe i should rewrite destroy() as __del__        

    def upgrade(self, d_level=1):
        self.level += d_level


class Province(object):
    """
    A Province consists of several cell and has a Town or similar
    """

    def __init__(self, owner, board=None, town=None, province_cells=None, is_land=False):
        self.supplies = 0
        self.income = 0
        self.expends = 0

        # a link to the board is needed to append new provinces to board.provinces
        self.board = board

        # append a list of province cells only if passed
        self.province_cells = province_cells
        self.town = town
        # self.owner: player instance of the owner of this cell (None = neutral)
        self.owner = owner

        self.is_land = is_land

    def append_cell(self, new_cell):
        if self.province_cells:
            if not new_cell in self.province_cells:
                self.province_cells.append(new_cell)
        else:
            self.province_cells = [new_cell]

        # vice versa:
        new_cell.province = self

    def remove_cell(self, cell):
        """
        simply removing that cell from this province
        attention: this cell won't have a province right after this function
        """
        if cell in self.province_cells:
            #print "removing cell: ", cell.pos
            self.province_cells.remove(cell)

        if len(self.province_cells) == 0:
            # a province without cells will be destroyed!
            #print "destroying province!"
            self.destroy()

    def split_off_cell(self, cell):
        """
        remove that cell from this province and
        establish a new province which holds jsut this cell
        """
        assert cell.province == self
        self.remove_cell(cell)
        new_province = Province(self.owner, board=self.board, province_cells=[cell], is_land=self.is_land)
        new_province.build_town(cell)

        cell.province = new_province
        self.board.provinces.append(cell.province)
        assert cell.province.province_cells

    def get_supplies(self):
        return self.supplies

    def update_income(self):
        self.income = len(self.province_cells)

    def update_expends(self):
        new_expends = 0
        for cur_cell in self.province_cells:
            if cur_cell.soldier:
                # each soldier costs (level+1) per turn
                new_expends += cur_cell.soldier.level + 1
        self.expends = new_expends

    def update(self):
        self.update_income()
        self.update_expends()

    def apply_income_and_costs(self):
        self.update_income()
        self.update_expends()

        self.supplies += self.income
        self.supplies -= self.expends

    def size(self):
        assert self.province_cells
        return len(self.province_cells)

    def merge_with(self, other_province):
        # merge this province with the other one
        # sum all supplies etc. and add it to the new province
        assert isinstance(other_province, Province)

        if self.owner != other_province.owner:
            return

        size_1a = self.size()
        size_1b = other_province.size()

        # We'll add the other province' supplies to the own one
        self.supplies += other_province.supplies
        # ... and it's cells too
        # NOTE: fucking NEVER use for when changing a list!!!
        while other_province.province_cells:
            other_cell = other_province.province_cells[0]
            assert isinstance(other_cell, Cell)
            #print "--- changing cell:", other_cell.pos
            other_cell.change_to_province(self)

        # Both towns will be destroyed and new one will be build at a random place in the merged province area
        if self.town:
            self.town.destroy()
        if other_province.town:
            other_province.town.destroy()

        assert self.province_cells
        self.build_town(random.choice(self.province_cells))
        assert self.town

        # just to make sure no cell was lost!
        assert size_1a + size_1b == self.size()

    def destroy(self):
        # this is quite useless...
        if self.province_cells:
            return False
        else:
            del self

    def build_town(self, town_cell=None):
        # each province has excatly one town
        if town_cell is None:
            town_cell = random.choice(self.province_cells)

        assert isinstance(town_cell, Cell)
        if self.town:
            self.town.destroy()

        self.town = Town(cell=town_cell)
        town_cell.town_flag = True

    def get_province_border_lands(self):
        # loop over all cells in this province and for each overa ll it's neighbours
        # if one edm's owner isn't same as cur_cell's: cur cell is a 'border-cell'
        border_area_set = []
        for cur_cell in self.province_cells:
            for edm in cur_cell.edm_cells:
                if edm.province.owner != self.owner:
                    border_area_set.append(cur_cell)
                    break
        return border_area_set


#==============================================================================
#
# 'old' classes      
#


# Instance for game cursor
class Cursor(object):
    def __init__(self, game_viewer):

        self.x = 10
        self.y = 10
        # .pos is the lattice position on game board
        self.pos = Vec2d(self.x, self.y)
        self.scroll_x = 0
        self.scroll_vec = Vec2d(0, 0)
        self.clicked_cell = None
        self.clicked_obj = None
        self.last_clicked_obj = None

        self.gv = game_viewer

        # board will be the class TGB
        self.board = self.gv.board
        # .mous_pos is the 'real' position on scren
        self.mouse_pos = Vec2d(0, 0)

    def set_pos(self, pos):
        # to keep pos and x/y in sync
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]

    def scroll(self, dx):
        self.scroll_x += dx
        if self.scroll_x > 15:
            self.scroll_x = 15
        if self.scroll_x < 0:
            self.scroll_x = 0
        self.update_scroll_vec()

    def update_scroll_vec(self):
        self.scroll_vec = Vec2d(self.scroll_x, 0)

    def click(self):
        if not self.gv.map_edit_mode:
            # We are not in map editing mode, so we check from
            # skin configuration file if we clicked any gui elements.
            if self.mouse_pos.in_rect(self.gv.sc["button_endturn"]):
                self.gv.end_turn()

            elif self.mouse_pos.in_rect(self.gv.sc["button_quit"]):
                self.clicked_obj = None
                self.gv.game_running = False

            elif self.mouse_pos.in_rect(Vec2d(0, 0), Vec2d(573, 444)):    # click is in map area

                if not self.board.valid_xy(self.pos):
                    return

                self.clicked_cell = self.board.cells[self.pos]

                self.last_clicked_obj = self.clicked_obj
                # there might be more than one object in this cell
                # for the moment: always choose soldier first
                if self.clicked_cell.soldier:
                    self.clicked_obj = self.clicked_cell.soldier
                elif self.clicked_cell.town_flag:
                    self.clicked_obj = self.clicked_cell.province.town
                else:
                    self.clicked_obj = None

                # last selected object was unit => move or attack ...
                if isinstance(self.last_clicked_obj, Unit):
                    if self.board.valid_xy(self.pos):
                        self.board.try_to_conquer(self.last_clicked_obj, self.clicked_cell, False)
                        # CPU INTENSIVE?
                        self.gv.has_anyone_lost_the_game()
                        # CPU INTENSIVE?
                        if self.gv.check_and_mark_if_someone_won():
                            self.board.turn = 0
                            self.board.cells.clear()
                            self.board.create_cells()
                            return
                else:
                # last selected object was a building or NoneType
                # => it's not important => concentrate on clicked_obj
                    if isinstance(self.clicked_obj, Unit):
                        # show stats or so ... do nothing for now
                        if self.clicked_obj.get_owner() == self.board.turn:
                            # It's our own soldier
                            return
                        else:
                            # clicked a foreign soldier
                            return

                    # mind the "elif" => if there's a unit AND a building => choose soldier
                    elif isinstance(self.clicked_obj, Building):
                        # There is a builing
                        if self.clicked_cell.province.owner == self.board.turn:
                            # It's our own building
                            # hm, for now: do nothing
                            return

                    elif isinstance(self.clicked_obj, NoneType):
                        # empty land or water cell
                        pass

        else:
            # Have we clicked gui elements?
            # FIXME: change editor gui elements to be modded with skin-file
            text_pos = Vec2d(800 / 2 - 110, 300)
            span_vec = Vec2d(240, 45)

            corner_1 = Vec2d(620, 366)
            corner_2 = Vec2d(782, 416)
            if self.mouse_pos.in_rect(corner_1, corner_2):
                self.gv.write_edit_map(self.gv.gamepath + "scenarios" + sep +
                                          self.gv.text_input("[SAVE MAP] Map name?", text_pos, span_vec))

            corner_1 = Vec2d(618, 429)
            corner_2 = Vec2d(782, 472)
            if self.mouse_pos.in_rect(corner_1, corner_2):
                file_path = self.gv.gamepath + "scenarios" + sep + \
                            self.gv.text_input("[LOAD MAP] Map name?", text_pos, span_vec)
                if path.exists(file_path):
                    self.gv.load_map(file_path)

            corner_1 = Vec2d(607, 560)
            corner_2 = Vec2d(792, 591)
            if self.mouse_pos.in_rect(corner_1, corner_2):
                self.gv.game_running = False

            if self.mouse_pos.x < 573 and self.mouse_pos.y < 444:
                corner_1 = Vec2d(0, 0)
                corner_2 = Vec2d(29, 13)
                if self.pos.in_rect(corner_1, corner_2):
                    self.board.cells[self.pos].province.owner = self.gv.map_edit_info[2]

    def get_color(self):
        if self.clicked_obj:
            return (255, 0, 0)
        else:
            return (255, 255, 255)


# Player that populates playerlist    
class Player(object):
    def __init__(self, name, player_id, color=pygame.Color('white'), ai=None):
        self.name = name
        self.id = player_id
        self.lost = False
        self.won = False
        self.ai_controller = ai
        self.color = color


# Simple Image Container (The Image Handler)
class TIH(object):
    def __init__(self):
        self.images = {}

    def add_image(self, image, image_id):
        self.images[image_id] = image

    # Get Image
    def gi(self, cur_id):
        if cur_id in self.images:
            return self.images[cur_id]
        else:
            return None


