#from sets import Set
import time
#import pygame

import hex_sys
#from sys import exit
from classcollection import *
from recurser import *
import os
#from graphics_helper import Plotter
#import ai


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

_DEBUG = 0



# Describe reason for being blocked
block_desc = dict(tooweak='Your soldier is too weak!',
                  alreadymoved='Soldier has already moved!',
                  spaceisnotlegal='Target is not land!',
                  ownspacealreadyoccupied='Target is friendly!',
                  outofprovince='Out of soldiers reach!',
                  default='blocked')


def get_block_desc(block_key):
    if block_key in block_desc:
        return block_desc[block_key]
    else:
        return block_desc['default']


# The Game Board, ultimate class for game board and its logic
class TGB:
    # constants
    MAPSIZE_X = 15  # number of cells in x-direction
    MAPSIZE_Y = 14  # number of cells in y-direction

    def __init__(self, game_view=None):
        # create self.cells as dictionary and add a MAPSIZE_X * MAPSIZE_Y cell instances for 'player 0'
        self.cells = {}
        self.provinces = []

        # Instance of recurser engine
        self.rek = TRecurser(self)

        self.gv = game_view

        # map_edit_info[0] = human player count in editable map
        # map_edit_info[1] = cpu player count in editable map
        # map_edit_info[2] = selected land in map editor
        self.map_edit_info = []
        self.map_edit_mode = False

        # Current turn
        self.turn = 1


        # create a random map?
        self.random_map = True

    def write_edit_map(self, filename):
        # Write edited map to file.
        # First six lines in map file are reserved for player info.
        file_handle = open(filename, 'w')
        # Add human players
        for i in range(self.map_edit_info[0]):
            file_handle.write('player\n')
            # Add CPU players
        for i in range(self.map_edit_info[1]):
            file_handle.write('ai\n')
            # Add absent players: 6 - ((Human Players) + (Cpu Players))
        # If 0 then 'none\n' does not get written
        if (self.map_edit_info[0] + self.map_edit_info[1]) > 0:
            for i in range(6 - (self.map_edit_info[0] + self.map_edit_info[1])):
                file_handle.write('none\n')
                # Iterate keys and values in board DATA and write them (separated with |)
        for pos, cell in self.cells.iteritems():
            file_handle.write('%s|%d\n' % (pos, cell.province.owner))
        file_handle.close()

    def read_scenarios(self):
        # Get list of the scenario - folder's files and remove '.svn' - folder
        scenario_list = os.listdir(os.path.join(self.gv.game_path, 'scenarios'))
        if '.svn' in scenario_list:
            scenario_list.remove('.svn')
        return scenario_list

    def get_player_id_list(self):
        return self.gv.get_player_id_list()

    def get_player_by_name(self, player_name):
        return self.gv.get_player_by_name(player_name)

    def count_world_specific(self, id_list):
        counter = 0
        for pos, cell in self.cells.iteritems():
            if cell.province.owner in id_list:
                counter += 1
        return counter

    def count_land_area(self):
        # Count whole world's land count
        counter = 0
        for cell in self.cells.values():
            assert isinstance(cell, Cell)
            if cell.province:
                if cell.province.is_land:
                    counter += 1
        return counter

    def seen_xy(self, pos):
        return self.gv.seen_xy(pos)

    def valid_xy(self, pos):
        # Valid coordinate is a coordinate which is found in cells
        return pos in self.cells

    def try_to_conquer(self, attacker, target_cell, only_simulation):
        # This function is called everytime an actor tries to attack
        if attacker.moved:
            # The soldier has already moved
            return

        # cell_is_blocked[0] -> Boolean value whether the target land is blocked
        # cell_is_blocked[1] -> if target land is blocked, this
        # holds the cell for the reason of block.
        # cell_is_blocked[3] -> holds a string for the reason of the block
        is_blocked, blocking_cell, block_reason = self.is_blocked(attacker, target_cell)

        # The target is not blocked
        if not is_blocked:

            # Check for lvl6 - battles
            # There is a target and no simulation is used
            # (meaning that try_to_conquer is not used in ai calculations)
            if target_cell.soldier and (not only_simulation):
                # Target is hostile and not a town
                if target_cell.town_flag and (target_cell.province.owner != attacker.get_owner()):
                    # Attacker and defender are level 6 soldiers
                    if (attacker.level == 6) and (target_cell.soldier.level == 6):
                        # 50% chance to win or lose
                        if random.randint(1, 2) == 1:
                            # Attacker lost
                            attacker.destroy()
                            return

            # Both simulation and real attack makes changes to
            # land owner policy
            target_cell.province.owner = attacker.get_owner()

            # If simulating for AI, we don't want to make
            # changes directly to actors.
            if not only_simulation:
                # Not simulating, not blocked, attacker conquered
                # target land.
                attacker.move_to(target_cell)
                attacker.moved = True
                target_cell.destroy_buildings()

        else:
            # Target is blocked, show the reason for blocking
            # but only if attacker is human player and seen on the screen
            if self.seen_xy(blocking_cell.pos) and not self.get_player_by_id(attacker.get_owner()).ai_controller:
                # Clear selected actor
                self.gv.cursor.clicked_obj = None
                # Convert (scrolled) hex map coordinates into screen pixels
                # and draw circle there
                anchor_pos = hex_sys.hex_map_to_pixel(blocking_cell.pos - self.gv.cursor.scroll_vec)
                pygame.draw.circle(self.gv.screen, (0, 255, 0), anchor_pos + Vec2d(20, 20), 30, 2)
                self.gv.plotter.text_at(get_block_desc(block_reason),
                                        anchor_pos + Vec2d(0, 15), font=self.gv.fonts.font_2)
                pygame.display.flip()
                # Little time to actually see it
                time.sleep(0.35)
                self.gv.draw_map()
                pygame.display.flip()

    def get_player_by_id(self, player_id):
        return self.gv.get_player_by_id(player_id)

    def get_random_existing_player(self):
        return self.gv.get_random_existing_player()



    # def fill_towns(self):
    #     # Fill towns should be called when lands are conquered
    #     # CPU INTENSIVE?
    #
    #     # Keep count of already searched lands
    #     searched = set()
    #
    #     # Get list of current non-lost players
    #     players = self.get_player_id_list()
    #
    #     # Iterate map
    #     for cur_pos, cur_cell in self.cells.iteritems():
    #
    #         # Is the coordinate already crawled
    #         if cur_cell in searched:
    #             continue
    #
    #         # Fill Towns only for existing and not lost players
    #         if cur_cell.province.owner not in players:
    #             continue
    #
    #         # Not empty space
    #         if cur_cell.province.owner > 0:
    #             # Check if the province has a town and get also crawled coordinates
    #             # towns_cells_list -> list of cells for province town(s)
    #             # land_area_list -> list of cells of this province
    #             towns_list, land_area_list = self.rek.count_towns_in_province(cur_cell)
    #
    #             # Update crawled coordinates
    #             searched.update(land_area_list)
    #
    #             # Check if the province has no Town yet, province has at least
    #             # 2 pieces of land and province is owned by existing player.
    #             if (not towns_list) and (len(land_area_list) > 1):
    #
    #                 # Panic method to exit loop
    #                 tries = 0
    #                 while tries < 100:
    #                     tries += 1
    #
    #                     # Find a new place for town:
    #                     #    - get a random legal coordinate from crawled province
    #                     place_cell = random.choice(list(land_area_list))
    #
    #                     if place_cell:
    #                         if (not place_cell.town) and (not place_cell.soldier):
    #                             # If a place was found for town, we'll add
    #                             # a new town in actors.
    #                             place_cell.build_town()
    #                             # Break the loop
    #                             tries = 100
    #
    #             # More than one town in province?
    #             elif len(towns_list) > 1:
    #                 # Then we'll merge towns in this province
    #                 self.merge_provinces(towns_list)

    def create_cells(self, max_x=None, max_y=None, cell_type=0):
        # create cell instances and add it to a new dict

        # it might be better to remove max_x/y and always set MAPSIZE_X/Y before
        # calling create_cells()
        if max_x is None:
            max_x = self.MAPSIZE_X
        else:
            self.MAPSIZE_X = max_x

        if max_y is None:
            max_y = self.MAPSIZE_Y
        else:
            self.MAPSIZE_Y = max_y

        for x in xrange(max_x):
            for y in xrange(max_y):
                pos = Vec2d(x, y)
                empty_edm_list = [None, None, None, None, None, None]
                new_province = Province(owner=None, is_land=False, board=self)
                new_cell = Cell(pos, cell_type, empty_edm_list, new_province)
                new_province.append_cell(new_cell)
                new_province.build_town(new_cell)
                self.cells[pos] = new_cell
                self.provinces.append(new_province)
            # now we have a lot of cells, but no connection between them

        for cell in self.cells.values():
            edm_cells = []
            for vec_edm_i in hex_sys.get_right_edm(cell.pos.y):
                # iterate over all neighbour positions
                pos_edm_i = cell.pos + vec_edm_i

                edm_cell_i = None
                if self.valid_xy(pos_edm_i):
                    edm_cell_i = self.cells[pos_edm_i]

                edm_cells.append(edm_cell_i)
            assert len(edm_cells) == 6
            cell.edm_cells = edm_cells
            assert len(cell.edm_cells) == 6

    def fill_random_units(self, d):
        # Obsolete
        player = self.get_player_id_list()
        if d > 0:
            while d > 0:
                retry = 0
                done = False
                while not done:
                    retry += 1
                    if retry == 500:
                        break
                    cur_coord = Vec2d(random.randint(1, self.MAPSIZE_X - 1), random.randint(1, self.MAPSIZE_Y - 1))
                    cur_cell = self.cells[cur_coord]
                    if cur_cell:
                        if (cur_cell.province.owner in player) and (cur_cell.soldier is None):
                            cur_cell.build_soldier()
                            done = True
                d -= 1  # outside of loop to decrease counter even if no empty cell was found

    def fill_random_boxes(self, no_of_new_cells, for_whom):
        """
        Fills a random box in the map
        for_whom -> list of player_id:s (randomly selected for land owned)
        max_x -> map width
        """
        # This just basically randoms coordinates and fills map
        if no_of_new_cells > 0:
            while no_of_new_cells > 0:
                pos = Vec2d(random.randint(2, self.MAPSIZE_X - 2), random.randint(2, self.MAPSIZE_Y - 2))
                if self.valid_xy(pos):
                    rand_cell = self.cells[pos]
                    assert isinstance(rand_cell, Cell)
                    rand_cell.province.owner = random.choice(for_whom)
                    #for edm_cell in rand_cell.edm_cells:
                    #    if edm_cell:    # it might be None if rand_cell is on the edge of the map
                    #        player_id = random.choice(for_whom)
                    #        edm_cell.province.owner = player_id
                no_of_new_cells -= 1

    def whole_map_situation_score(self, player_id):
        # This function is obsolete (?)
        # cell_owner_ids ... a list consisting of the player id of each cell
        cell_owner_ids = [cell.province.owner for cell in self.cells.values()]
        return cell_owner_ids.count(player_id)

    def remove_province(self, province):
        # this might be moved to player class together with province list
        self.provinces.remove(province)

    def is_blocked(self, attacker, cell_target):
        # Check is cell_target blocked for soldier attacker
        assert isinstance(attacker, Soldier)
        assert isinstance(cell_target, Cell)

        defender = cell_target.soldier
        # cell_target ... attacked cell
        if defender:
            # There is a defending unit at target
            if attacker.level < 6:
                if defender.level >= attacker.level:
                    return [True, cell_target, 'tooweak']

            if cell_target.town_flag and attacker.level < 2:
                return [True, cell_target, 'tooweak']
            if attacker.get_owner() == defender.get_owner():
                return [True, cell_target, 'sameside']

        # Soldier can move only once a turn
        if attacker.moved:
            return [True, cell_target, 'alreadymoved']

        # Empty Space can't be conquered
        if cell_target.province.owner == 0:
            return [True, cell_target, 'spaceisnotlegal']

        # One can't conquer his own soldiers            
        if cell_target.province.owner == self.turn:
            if defender:
                return [True, cell_target, 'ownspacealreadyoccupied']

        found = False
        for edm_cell in cell_target.edm_cells:
            # Next to target must be own land. The land must be
            # from the same province as the actor is from.
            if edm_cell is None:
                continue    # might be None
            if edm_cell.province == attacker.cur_cell.province:
                found = True
        if not found:
            # No adjacent lands found, can't conquer places out of
            # soldier's reach
            return [True, cell_target, 'outofprovince']

        # Check for enemy unit blockers
        for edm_cell in cell_target.edm_cells:
            if edm_cell is None:
                continue
                # Is the targets neighbour same side as the target
            if edm_cell.province.owner == cell_target.province.owner:
                # Has the neighbourds adjacent own piece a soldier defending?
                defender = edm_cell.soldier
                if defender:
                    # Yes it has
                    if defender.get_owner() != attacker.get_owner():
                        if defender.cur_cell.town_flag:
                            # Town can defend against level 1 soldiers
                            if attacker.level == 1:
                                # Attacker is level 1, blocked = True
                                return [True, edm_cell, 'tooweak']
                        if attacker.level < 6:
                            # Attacker's level is under 6, check if
                            # defender is weaker. (level 6 can attack
                            # where-ever it wants)
                            if defender.level >= attacker.level:
                                # Attacker's soldier is weaker than defender,
                                # blocked=True
                                return [True, edm_cell, 'tooweak']
                                # Found nothing that could block attacker,
                                # blocked = False !!! The move is legal.
        return [False, None, 'legal']

    def generate_map(self, percentage_land=0.75):
        # Generate simple random map

        self.create_cells(self.MAPSIZE_X, self.MAPSIZE_Y, cell_type=0)
        # now we have a map full of tiny Monacos ,)
        # i.e. one-cell provinces with a town and each cell has it's neighbours
        # but the provinces aren't assigned to any player

        self.create_land_and_water(percentage_land)
        self.check_map()

        all_cells = self.cells.values()
        self.first_cycle_for(all_cells)
        self.check_map()

        done = False
        counter = 0
        while not done and counter < 5:
            counter += 1
            split_cell_list = self.split_big_provinces(max_allowed_size=5)
            if split_cell_list:
                #random.shuffle(split_cell_list)
                self.first_cycle_for(split_cell_list)
            else:
                done = True
        self.check_map()
        # now we should have a map full of provinces no bigger than 5 cells
        # at the moment all provinces belong to the same (first) player

        self.assign_provinces_to_players()


        #time.sleep(0.05)
        # Draw the map
        #self.gv.draw_map()
        # Show the drawed content
        #pygame.display.flip()

        self.pay_salary_to_towns(self.gv.player_list)

    def assign_provinces_to_players(self):
        """
        assign each land-province to a random existing player
        """
        for province in self.provinces:
            rand_player = self.get_random_existing_player()
            province.owner = rand_player

    def split_big_provinces(self, max_allowed_size):
        """
        split big provinces to re-organize them
        """
        province_to_split_list = [province for province in self.provinces
                                  if (province.size() > max_allowed_size) and province.is_land]
        if province_to_split_list:
            print "province_to_split_list.length:", len(province_to_split_list)
            split_cell_list = [cell for province in province_to_split_list for cell in province.province_cells]
            for province in province_to_split_list[:]:
                while province.province_cells:
                    #print "province.size: ", province.size()
                    province.split_off_cell(province.province_cells[0])
                self.provinces.remove(province)
                del province

            return split_cell_list
        else:
            # there is no province bigger than max_allowed_size
            return None

    def create_land_and_water(self, percentage_land):
        """ set about [percentage_land] of the cells as land area """
        for cur_cell in self.cells.values():
            assert isinstance(cur_cell, Cell)

            # percentage_land - chance to create a random land cell
            rand_nr = random.random()
            if rand_nr < percentage_land:
                #cur_cell.province.owner = self.get_random_existing_player()
                cur_cell.province.owner = self.get_player_by_id(1)
                cur_cell.province.is_land = True
            else:
                cur_cell.province.owner = None

            assert cur_cell.province
        print "land area: ", self.count_land_area()

    def check_map(self):
        """ do some checks (for debuging) """
        for cur_cell in self.cells.values():
            assert isinstance(cur_cell, Cell)
            assert isinstance(cur_cell.province, Province)
            assert cur_cell.province.province_cells
            assert cur_cell.province.town
            for edm in cur_cell.edm_cells:
                if edm:
                    assert isinstance(edm, Cell)
                    assert isinstance(edm.province, Province)
                    assert edm.province.province_cells
                    assert cur_cell.province.town

        for province in self.provinces:
            assert province.province_cells
            assert province.town

    def first_cycle_for(self, cells):
        """
        first cycle:
        for each land province with only 1 cell:
           merge with the smallest  neighbouring province
        merge all water provinces to a big one
        """
        i = 0
        for cur_cell in cells:
            i += 1
            #print "first cylce: doing cell ", i, " at pos: ", cur_cell.pos

            assert isinstance(cur_cell.province, Province)
            cur_province = cur_cell.province

            if cur_province.is_land:
                if cur_province.size() == 1:
                    # iterate over neighbours of cur_cell in random order
                    edms_copy = cur_cell.edm_cells[:]
                    random.shuffle(edms_copy)
                    finished_cur_cell = False
                    max_size = 0
                    while not finished_cur_cell:
                        max_size += 1
                        blocked_neighbours = 0
                        for rand_edm in edms_copy:
                            if rand_edm:
                                assert isinstance(rand_edm, Cell)
                                assert isinstance(rand_edm.province, Province)
                                edm_province = rand_edm.province
                                # don't merge land and water
                                if edm_province.is_land and (edm_province != cur_province):
                                    # at the moment there is only one player/owner
                                    #if edm_province.owner == cur_province.owner:
                                    assert isinstance(rand_edm, Cell)
                                    if edm_province.size() <= max_size:
                                        #print "merge: ", cur_cell.pos, " <-> ", rand_edm.pos
                                        cur_province.merge_with(edm_province)
                                        self.remove_province(edm_province)

                                        finished_cur_cell = True
                                        assert cur_province.province_cells
                                        assert cur_province.town
                                    else:
                                        pass
                                else:
                                    # some cells might have no neighbour to merge with (i.e. small islands)
                                    blocked_neighbours += 1
                            else:
                                blocked_neighbours += 1
                        if blocked_neighbours == 6:
                            finished_cur_cell = True

            else:
                pass
                # it's a water-province
                edms_not_none_list = [edm for edm in cur_cell.edm_cells if edm is not None]
                random.shuffle(edms_not_none_list)
                #shuffled_list = random.shuffle(edms_not_none_list)
                for rand_edm in edms_not_none_list:
                    assert isinstance(rand_edm, Cell)
                    edm_province = rand_edm.province
                    if not edm_province.is_land:    # don't merge land and water
                        if edm_province != cur_province:
                            assert isinstance(rand_edm, Cell)
                            #rand_edm.change_to_province(cur_cell.province)
                            # merge all water-provinces to a big one
                            cur_province.merge_with(edm_province)
                            self.remove_province(edm_province)
                            #print "merge water: ", cur_cell.pos, " <-> ", rand_edm.pos

    def count_towns_on_world(self, pid):
        # Self - explanatory
        result = 0
        for cell in self.cells.values():
            if cell.town_flag:
                if cell.province.owner == pid:
                    result += 1
        return result

    def show_own_units_that_can_move(self):
        # Draw own units that have not moved yet
        for cell in self.cells.values():
            if cell.soldier:
                if (not cell.soldier.moved) and (cell.soldier.get_owner() == self.turn):
                    if self.seen_xy(cell.pos):
                        pixel_coord = hex_sys.hex_map_to_pixel(cell.pos - self.gv.cursor.scroll_vec)
                        pygame.draw.circle(self.gv.screen, (255, 255, 20), pixel_coord + Vec2d(20, 20), 20, 3)
        pygame.display.flip()
        time.sleep(0.5)
        self.gv.draw_map()

    def pay_salary_to_towns(self, owner_list):
        """
        Calculate towns income,expend and supplies. Kill soldiers without supplies.
        just_do_math -> if true, only income and expend are calculated

        ... was mostly moved to Town-class
        """

        for province in self.provinces:
            if province.owner in owner_list:
                province.apply_income_and_costs()

                if province.supplies < 0:
                    # Not enough supplies, provinces soldiers are going
                    # to be terminated.
                    for province_cell in province.province_cells:
                        if province_cell.soldier:
                            # a Skull is drawn on the dead soldier
                            pixel_coord = hex_sys.hex_map_to_pixel(province_cell.pos - self.gv.cursor.scroll_vec)
                            self.gv.screen.blit(self.gv.pics.gi('skull'), pixel_coord + Vec2d(10, 10))
                            # ... and now his/her end is coming:
                            province_cell.soldier.destroy()
        pygame.display.flip()
