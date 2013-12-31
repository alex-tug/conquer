#from sets import Set
import time

import hex_sys
#from sys import exit
from operator import itemgetter
from classcollection import *
from recurser import *
import ai
import os
import gamemenu

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
    MAPSIZE_X = 30  # number of cells in x-direction
    MAPSIZE_Y = 14  # number of cells in y-direction


    def __init__(self, screen, ih, gp):
        # side_id: 0 = Empty Space, 1-6 are player id:s

        # How many 'extra'-recursions cpu will make (max.) trying to figure out a good move
        self.ai_recursion_depth = 10

        # Pretty self-explanatory
        self.show_cpu_moves_with_lines = True

        # Pygame screen surface passed as 'pointer' for drawing methods
        self.screen = screen

        # create self.cells as dictionary and add a MAPSIZE_X * MAPSIZE_Y cell instances for 'player 0'
        self.cells = {}
        self.create_cells(self.MAPSIZE_X, self.MAPSIZE_Y, piece=0)

        # Pointer to Picture Handler container class which has used pictures
        self.pics = ih
        self.fonts = FontContainer()

        # Current path
        self.game_path = gp + os.sep

        # Instance of recurser engine
        self.rek = TRecurser(self)

        # Instance of cursor
        self.cursor = TCursor(self)
        self.cursor.x = 10
        self.cursor.y = 10

        # map_edit_info[0] = human player count in editable map
        # map_edit_info[1] = cpu player count in editable map
        # map_edit_info[2] = selected land in map editor
        self.map_edit_info = []
        self.map_edit_mode = False

        # Current turn
        self.turn = 1

        # List for cpu player names and load the names
        self.cpu_names = []
        self.load_cpu_names()

        # Tuple that is used at sorting scorelist
        self.score_s = ()

        # If the game (actual map view) is running, game_running is True
        self.game_running = False

        # Skin configuration dictionary
        self.sc = {}

        # Load the skin configuration file
        self.load_skin_file('skin')

        # List of current players in a game
        self.player_list = []

    def load_cpu_names(self):
        # Read names from file to cpu name list
        file_handle = open(self.game_path + 'cpu_player_names', 'r')
        for line in file_handle.readlines():
            if line.endswith('\n'):
                self.cpu_names.append(line[:-1])
            else:
                self.cpu_names.append(line)
        file_handle.close()

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
            file_handle.write('%s|%d\n' % (pos, cell.province.side))
        file_handle.close()

    def read_scenarios(self):
        # Get list of the scenario - folder's files and remove '.svn' - folder
        scenario_list = os.listdir(os.path.join(self.game_path, 'scenarios'))
        if '.svn' in scenario_list:
            scenario_list.remove('.svn')
        return scenario_list

    def load_skin_file(self, filename1):
        # Load configuration file and read it into sc - dictionary
        file_handle = open(filename1, 'r')
        for line in file_handle.xreadlines():
            if not line:
                # Empty line, go to next
                continue
            else:
                if line[0] == '#':
                    # Line is comment, go to next line
                    continue
                if line.isspace():
                    # Line is empty, go to next line
                    continue

            # Cut newlines
            if line.endswith('\r\n'):
                line = line[:-1]
            if line.endswith('\n'):
                line = line[:-1]

            # Make lowercase and split
            line = line.lower().split(' ')

            # Configuration options into sc, read the skin file for more info
            if line[0] == 'interface_filename':
                self.sc['interface_filename'] = line[1]
            if line[0] == 'unit_status_text_topleft_corner':
                self.sc['unit_status_text_topleft_corner'] = Vec2d(int(line[1]), int(line[2]))
            if line[0] == 'scoreboard_text_topleft_corner':
                self.sc['scoreboard_text_topleft_corner'] = Vec2d(int(line[1]), int(line[2]))
            if line[0] == 'unit_status_text_color':
                self.sc['unit_status_text_color'] = (int(line[1]), int(line[2]), int(line[3]))
            if line[0] == 'scoreboard_text_color':
                self.sc['scoreboard_text_color'] = (int(line[1]), int(line[2]), int(line[3]))
            if line[0] == 'button_endturn':
                self.sc['button_endturn'] = (Vec2d(int(line[1]), int(line[2])), Vec2d(int(line[3]), int(line[4])))
            if line[0] == 'button_quit':
                self.sc['button_quit'] = (Vec2d(int(line[1]), int(line[2])), Vec2d(int(line[3]), int(line[4])))
            if line[0] == 'making_moves_text_topleft_corner':
                self.sc['making_moves_text_topleft_corner'] = Vec2d(int(line[1]), int(line[2]))
            if line[0] == 'menu_interface_filename':
                self.sc['menu_interface_filename'] = line[1]
            if line[0] == 'making_moves_text_color':
                self.sc['making_moves_text_color'] = (int(line[1]), int(line[2]), int(line[3]))

    def start_game(self):
        self.game_running = True

        # Instance of pygame's Clock
        clock = pygame.time.Clock()

        # The Main Loop to run a game
        while self.game_running:

            # Limit fps to 30, smaller resource usage
            clock.tick(30)

            player = self.get_player_by_side(self.turn)
            if player:
                if player.ai_controller or player.lost:
                    self.end_turn()
                if player.won:
                    self.draw_scoreboard(False)
                    pygame.display.flip()

            # Iterate through events
            for event in pygame.event.get():
                # Mouse click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Scrolling included in calculations
                    click_pos = hex_sys.pixel_to_hex_map(Vec2d(event.pos)) + self.cursor.scroll_vec
                    # Coordinates into cursor's memory
                    self.cursor.set_pos(click_pos)
                    self.cursor.mouse_pos = Vec2d(event.pos)

                    # Left mouse button = cursor's click
                    if event.button == 1:
                        self.cursor.click()

                    # Right mouse button = draft and update soldiers if
                    # NOT in map editing mode
                    if not self.map_edit_mode:
                        if self.cursor.x < self.MAPSIZE_X and self.cursor.y < (self.MAPSIZE_Y - 1):
                            #if event.button == 3:
                            #    if self.valid_xy(self.cursor.pos):
                            #        self.cells[self.cursor.pos].build_soldier()
                            if event.button == 2:
                                if self.valid_xy(self.cursor.pos):
                                    target_cell = self.cells[self.cursor.pos]
                                    if target_cell.province.side == self.turn:
                                        self.cells[self.cursor.pos].build_soldier()

                # Key press
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        # Scroll screen left
                        self.cursor.scroll(-1)
                    if event.key == pygame.K_RIGHT:
                        # Scroll screen right
                        self.cursor.scroll(1)

                    if not self.map_edit_mode:
                        if event.key == pygame.K_m:
                            self.show_own_units_that_can_move()
                        if event.key == pygame.K_e:
                            self.end_turn()
                    else:
                        # In map editor mode, UP and DOWN keys change
                        # selected land
                        if event.key == pygame.K_UP:
                            self.map_edit_info[2] += 1
                            if self.map_edit_info[2] > 6:
                                self.map_edit_info[2] = 6
                        if event.key == pygame.K_DOWN:
                            self.map_edit_info[2] -= 1
                            if self.map_edit_info[2] < 0:
                                self.map_edit_info[2] = 0
                                # Draw the scoreboard without calculating and sorting scores
                self.draw_scoreboard(False)
                # Draw the map
                self.draw_map()
                # Show the drawed content
                pygame.display.flip()

    def new_game(self, scenario_file='unfair', random_map=False, random_players_cpu=3, human_players=3):
        """
        Makes everything ready for a new game. Call new_game before calling start_game.
        
        scenario_file -> Filename for scenario if random_map is set to False
        random_players_cpu -> CPU Player count in random generated map
        human_players -> Human Player count in random generated map
        """

        # Status Quo Ante (bellum), Settings before war ;)
        self.turn = 1
        self.score_s = ()
        self.player_list = []
        self.map_edit_mode = False
        self.cursor.scroll_x = 0

        # If map is randomly generated, add players        
        if random_map:
            for i in xrange(human_players):
                self.player_list.append(TPlayer('Player %d' % (i + 1), i + 1, self.screen, None))
            for i in xrange(random_players_cpu):
                self.player_list.append(
                    TPlayer('%s (cpu)' % (random.choice(self.cpu_names)), i + (human_players + 1), self.screen,
                            ai.TAi(self)))

        # Clear data and actors from possible previous maps
        self.cells.clear()

        if random_map:
            # Generate random map
            self.generate_map()
        else:
            # Read a scenario
            self.load_map(os.path.join(self.game_path, 'scenarios') + os.sep + scenario_file)

        # Add resource towns
        #self.fill_towns()

        # Calculate income and expends, and do changes for first players supplies
        self.salary_time_to_towns_by_turn([1])

        # JUST ONLY calculate everyones supply income and expends
        self.salary_time_to_towns_by_turn(self.get_player_id_list())

        self.draw_map()
        # Calculate and sort scores and draw scores
        self.draw_scoreboard(True)

        pygame.display.flip()

        # If the first player is computer, make it act
        if self.player_list[0].ai_controller:
            # The AI routines for CPU Player are called from it's AI-Controller
            self.player_list[0].ai_controller.act(self.ai_recursion_depth)
            # FIXME, cpu intensive? Well anyway, make sure that towns are on their places
            #self.fill_towns()
            # Next player's turn
            self.end_turn()

    def get_player_id_list(self):
        # Make a player-id - list and return it
        return [iteration.id for iteration in self.player_list]

    def get_player_by_name(self, player_name):
        for player in self.player_list:
            if player.name == player_name:
                return player
        return None

    def count_world_specific(self, id_list):
        counter = 0
        for pos, cell in self.cells.iteritems():
            if cell.province.side in id_list:
                counter += 1
        return counter


    def count_land_area(self):
        # Count whole world's land count
        counter = 0
        for cell in self.cells.values():
            if cell.tmp_side > 0:
                counter += 1
        return counter

    def seen_xy(self, pos):
        # Return boolean value if the coordinate is seen by player
        # (not scrolled out of borders)
        return (0 + self.cursor.scroll_x) <= pos.x <= (self.cursor.scroll_x + 14)

    def valid_xy(self, pos):
        # Valid coordinate is a coordinate which is found in cells
        return (pos in self.cells)

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
            if (target_cell.soldier) and (not only_simulation):
                # Target is hostile and not a town
                if (target_cell.town) and (target_cell.province.side != attacker.get_owner()):
                    # Attacker and defender are level 6 soldiers
                    if (attacker.level == 6) and (target_cell.soldier.level == 6):
                        # 50% chance to win or lose
                        if random.randint(1, 2) == 1:
                            # Attacker lost
                            attacker.destroy()
                            return

            # Both simulation and real attack makes changes to
            # land owner policy
            target_cell.province.side = attacker.get_owner()

            # If simulating for AI, we don't want to make
            # changes directly to actors.
            if not only_simulation:
                # Not simulating, not blocked, attacker conquered
                # target land.
                attacker.move_to(target_cell)
                attacker.moved = True
                target_cell.destroy_buildings()

                # Fix this to check one province (x2,y2) if town creating needed
                #self.fill_towns()
        else:
            # Target is blocked, show the reason for blocking
            # but only if attacker is human player and seen on the screen
            if self.seen_xy(blocking_cell.pos) and not self.get_player_by_side(attacker.get_owner()).ai_controller:
                # Clear selected actor
                self.cursor.clicked_obj = None
                # Convert (scrolled) hex map coordinates into screen pixels
                # and draw circle there
                anchor_pos = hex_sys.hex_map_to_pixel(blocking_cell.pos - self.cursor.scroll_vec)
                pygame.draw.circle(self.screen, (0, 255, 0), anchor_pos + Vec2d(20, 20), 30, 2)
                gamemenu.text_at(self.screen, get_block_desc(block_reason),
                                 anchor_pos + Vec2d(0, 15), font=self.fonts.font_2)
                pygame.display.flip()
                # Little time to actually see it
                time.sleep(0.35)
                self.draw_map()
                pygame.display.flip()


    def get_player_by_side(self, side):
        # Self - explanatory
        for player in self.player_list:
            if player.id == side:
                return player
        return None

    @staticmethod
    def merge_provinces(province_list):
        """
        Merge towns if provinces has more than one town
        town_coords -> list of town coordinates
        province_area -> list of provinces' lands coordinates
        """
        # If we have more than one town in a province and the province_area has items
        if len(province_list) > 1:

            # Summed supplies from provinces' towns
            summed_supplies = 0
            summed_cells = []

            # Iterate through town coordinates
            for cur_province in province_list:
                # We'll add the towns supplies in the sum counter
                summed_supplies += cur_province.supplies
                summed_cells += cur_province.province_cells

                # The towns will be destroyed
                cur_province.town.destroy()

            # create new province
            new_province = Province(province_list[0].side, province_cells=summed_cells)
            new_province.supplies = summed_supplies
            for cur_cell in new_province.province_cells:
                cur_cell.change_to_province(new_province)

            # Select a random location in the merged province for the new and only town
            new_town_cell = random.choice(summed_cells)
            new_town = new_town_cell.build_town()
            if new_town:
                new_province.town = new_town

    def fill_towns(self):
        # Fill towns should be called when lands are conquered
        # CPU INTENSIVE?

        # Keep count of already searched lands
        searched = set()

        # Get list of current non-lost players
        players = self.get_player_id_list()

        # Iterate map
        for cur_pos, cur_cell in self.cells.iteritems():

            # Is the coordinate already crawled
            if cur_cell in searched:
                continue

            # Fill Towns only for existing and not lost players
            if cur_cell.province.side not in players:
                continue

            # Not empty space
            if cur_cell.province.side > 0:
                # Check if the province has a town and get also crawled coordinates
                # towns_cells_list -> list of cells for province town(s)
                # land_area_list -> list of cells of this province
                towns_list, land_area_list = self.rek.count_towns_in_province(cur_cell)

                # Update crawled coordinates
                searched.update(land_area_list)

                # Check if the province has no Town yet, province has at least
                # 2 pieces of land and province is owned by existing player.
                if (not towns_list) and (len(land_area_list) > 1):

                    # Panic method to exit loop
                    tries = 0
                    while tries < 100:
                        tries += 1

                        # Find a new place for town:
                        #    - get a random legal coordinate from crawled province
                        place_cell = random.choice(list(land_area_list))

                        if place_cell:
                            if (not place_cell.town) and (not place_cell.soldier):
                                # If a place was found for town, we'll add
                                # a new town in actors.
                                place_cell.build_town()
                                # Break the loop
                                tries = 100

                # More than one town in province?
                elif len(towns_list) > 1:
                    # Then we'll merge towns in this province
                    self.merge_provinces(towns_list)

    def create_cells(self, max_x=None, max_y=None, piece=0):
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
                self.cells[pos] = Cell(pos, empty_edm_list, tmp_side=piece)
                # now we have a lot of cells, but no connection between them

        for cell in self.cells.values():
                edm_list = []
                for vec_edm_i in hex_sys.get_right_edm(cell.pos.y):
                    # iterate over all neighbour positions
                    pos_edm_i = pos + vec_edm_i

                    edm_cell_i = None
                    if self.valid_xy(pos_edm_i):
                        edm_cell_i = self.cells[pos_edm_i]

                    edm_list.append(edm_cell_i)
                assert len(edm_list) == 6
                cell.edm_cells = edm_list

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
                        if (cur_cell.province.side in player) and (cur_cell.soldier is None):
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
                    rand_cell.province.side = random.choice(for_whom)
                    #for edm_cell in rand_cell.edm_cells:
                    #    if edm_cell:    # it might be None if rand_cell is on the edge of the map
                    #        player_id = random.choice(for_whom)
                    #        edm_cell.tmp_side = player_id
                no_of_new_cells -= 1

    def whole_map_situation_score(self, player_id):
        # This function is obsolete (?)
        # cell_owner_ids ... a list consisting of the player id of each cell
        cell_owner_ids = [cell.province.side for cell in self.cells.values()]
        return cell_owner_ids.count(player_id)

    def draw_scoreboard(self, update=False):
        """
        Draw Scoreboard
        update -> If true, scores are calculated and sorted
        """
        if update:
            # Update scores
            scores = {}
            for cur_player in self.player_list:
                if not cur_player.lost:
                    # Count existing players land count
                    scores[cur_player] = self.whole_map_situation_score(cur_player.id)
                    # Sort points
            self.score_s = sorted(scores.iteritems(), key=itemgetter(1))

        # Iterate every player
        for player in self.player_list:
            # Check if a player has won
            if player.won:
                # a Player has won, show the information
                self.cursor.clicked_obj = None
                if player.ai_controller:
                    gamemenu.text_at(self.screen, 'Player %s won the game!' % player.name,
                                     Vec2d(200, 200), font=self.fonts.font_4,
                                     color=(255, 255, 255))
                else:
                    gamemenu.text_at(self.screen, 'You (%s) won the game!' % player.name,
                                     Vec2d(200, 200), font=self.fonts.font_4,
                                     color=(255, 255, 255))
                pygame.display.flip()

        counter = 0
        # Draw the scores, counter puts text in right row.
        # Skin configuration file is used here
        for jau in reversed(self.score_s):
            pos_base = self.sc['scoreboard_text_topleft_corner']
            pos_shift = Vec2d(0, 35)

            self.screen.blit(self.pics.gi('%d' % jau[0].id),
                             pos_base + pos_shift * counter + Vec2d(0, -13))

            gamemenu.text_at(self.screen, '%d     %s' % (jau[1], jau[0].name),
                             pos_base + pos_shift * counter + Vec2d(15, 0),
                             color=tuple(self.sc['scoreboard_text_color']),
                             font=self.fonts.font_4,
                             wipe_background=False)

            counter += 1
        try:
            # Lost players are discarded from player_list, so next line
            # may make an error. Thats why the try - expression.
            cur_player = self.get_player_by_side(self.turn)
            # Human player
            if not cur_player.ai_controller:
                if not cur_player.lost:
                    # Human player's turn, tell it
                    gamemenu.text_at(self.screen,
                                     'Your (%s) turn' % cur_player.name,
                                     Vec2d(630, 300),
                                     color=(0, 0, 0),
                                     font=self.fonts.font_3,
                                     wipe_background=False
                    )
                else:
                    # The human player has lost, tell it
                    gamemenu.text_at(self.screen,
                                     'You (%s) lost...' % cur_player.name,
                                     Vec2d(635, 300),
                                     color=(0, 0, 0),
                                     font=self.fonts.font_3,
                                     wipe_background=False
                    )
        except:
            # Error occurred, well do nothing about it...
            pass

    def draw_map_edit_utilities(self):
        # Extra drawing routines for scenario editing mode

        # Text for selected map tile
        if self.map_edit_info[2] == 0:
            str_text = 'Eraser'
        else:
            if self.map_edit_info[2] <= (self.map_edit_info[0] + self.map_edit_info[1]):
                str_text = 'Player #%d land' % self.map_edit_info[2]
            else:
                # Land without player in the map, good for connecting player
                # provinces in own maps.
                str_text = 'Land #%d without player' % self.map_edit_info[2]

        # Show the selected map tile text        
        gamemenu.text_at(self.screen, 'Selected:', Vec2d(620, 80),
                         font=self.fonts.font_4, wipe_background=False, color=(0, 0, 0))
        gamemenu.text_at(self.screen, str_text, Vec2d(620, 100),
                         font=self.fonts.font_4, wipe_background=False, color=(0, 0, 0))

        # Draw players captions in the scenario
        counter = 0
        cur_pos_base = Vec2d(620, 130)
        cur_pos_shift = Vec2d(0, 20)
        cur_font = self.fonts.font_4,
        for i in xrange(0, self.map_edit_info[0]):
            counter += 1
            gamemenu.text_at(self.screen, 'Player #%d = Human' % counter,
                             cur_pos_base + counter * cur_pos_shift,
                             font=cur_font,
                             wipe_background=False, color=(0, 0, 0))

        for i in xrange(0, self.map_edit_info[1]):
            counter += 1
            gamemenu.text_at(self.screen, 'Player #%d = CPU' % counter,
                             cur_pos_base + counter * cur_pos_shift,
                             font=cur_font, wipe_background=False, color=(0, 0, 0))

        if (6 - counter) > 0:
            for i in range(0, (6 - counter)):
                counter += 1
                gamemenu.text_at(self.screen, 'Player #%d = No player' % counter,
                                 cur_pos_base + counter * cur_pos_shift,
                                 font=cur_font, wipe_background=False, color=(0, 0, 0))

    def draw_map(self):
        """
        Game window's drawing routines
        """

        # Draw the correct interface
        if not self.map_edit_mode:
            # Game interface
            self.screen.blit(self.pics.gi('interface'), (0, 0))
            self.draw_scoreboard(False)
        else:
            # Map editing interface
            self.screen.blit(self.pics.gi('mapedit'), (0, 0))
            self.draw_map_edit_utilities()

        # Loop pieces to be drawn (horizontally there is scrolling too)
        for x in xrange(self.cursor.scroll_x, self.cursor.scroll_x + int(self.MAPSIZE_X / 2)):
            for y in xrange(self.MAPSIZE_Y):
                assert self.valid_xy(Vec2d(x, y))
                cur_cell = self.cells[Vec2d(x, y)]
                # There is land to draw
                if cur_cell.province.side > 0:
                    # Get pixel coordinates
                    pixel_coord = hex_sys.hex_map_to_pixel(cur_cell.pos - self.cursor.scroll_vec)

                    # Draw the piece
                    self.screen.blit(self.pics.gi(str(cur_cell.province.side)), pixel_coord)

                    # Check if actor is found at the coordinates
                    if cur_cell.soldier:
                        # a Soldier was found
                        # Make a text for soldier-> level and X if moved
                        str_text = '%d' % cur_cell.soldier.level
                        if cur_cell.soldier.moved:
                            str_text += 'X'
                            # Draw soldier
                        self.screen.blit(self.pics.gi('soldier'), pixel_coord + Vec2d(10, 10))
                        # Draw text for the soldier
                        gamemenu.text_at(self.screen, str_text, pixel_coord + Vec2d(20, 20), font=self.fonts.font_1)

                    if cur_cell.town:
                        # a Resource Town was found
                        self.screen.blit(self.pics.gi('town'), pixel_coord + Vec2d(3, 8))

                        # If the town is on our side and we are not AI controlled, then we'll
                        # draw the supply count on the town.
                        if cur_cell.province.side == self.turn:
                            if not (self.get_player_by_side(cur_cell.province.side).ai_controller):
                                gamemenu.text_at(self.screen, '%d' % cur_cell.province.supplies,
                                                 pixel_coord + Vec2d(15, 13),
                                                 font=self.fonts.font_2,
                                                 wipe_background=False)

                                #if cur_cell.factory:
                                # a factory was found
                                # ToDo
                                #    pass

        # If an actor is selected, then we'll draw red box around the actor
        if self.cursor.clicked_obj:
            pixel_pos = hex_sys.hex_map_to_pixel(self.cursor.pos - self.cursor.scroll_vec)
            pygame.draw.rect(self.screen, self.cursor.get_color(), (pixel_pos.x, pixel_pos.y, 40, 40), 2)

        # If an building is chosen, we'll draw information about it:
        #   Income, Expends, Supplies
        if isinstance(self.cursor.clicked_obj, Building):
            cur_town = self.cursor.clicked_obj
            tmp_color = (
                self.sc['unit_status_text_color'][0],
                self.sc['unit_status_text_color'][1],
                self.sc['unit_status_text_color'][2])
            coord_topleft = self.sc['unit_status_text_topleft_corner']
            vec_offset = Vec2d(0, 10)
            vec_shift = Vec2d(0, 20)
            gamemenu.text_at(self.screen, 'Resource town',
                             coord_topleft + vec_offset + 1 * vec_shift,
                             font=self.fonts.font_4,
                             wipe_background=False,
                             color=tmp_color)
            gamemenu.text_at(self.screen, 'Income: %d' % cur_town.cell.income,
                             coord_topleft + vec_offset + 2 * vec_shift,
                             font=self.fonts.font_4,
                             wipe_background=False,
                             color=tmp_color)
            gamemenu.text_at(self.screen, 'Expends: %d' % cur_town.cell.expends,
                             coord_topleft + vec_offset + 3 * vec_shift,
                             font=self.fonts.font_4,
                             wipe_background=False,
                             color=tmp_color)
            gamemenu.text_at(self.screen, 'Supplies: %d' % cur_town.cell.supplies,
                             coord_topleft + vec_offset + 4 * vec_shift,
                             font=self.fonts.font_4,
                             wipe_background=False,
                             color=tmp_color)
            self.screen.blit(self.pics.gi('town'), coord_topleft)

    def is_blocked(self, attacker, cell_target):
        # Check is cell_target blocked for soldier attacker

        defender = cell_target.soldier
        # cell_target ... attacked cell
        if defender:
            # There is a defending unit at target
            if attacker.level < 6:
                if defender.level >= attacker.level:
                    return [True, cell_target, 'tooweak']

            if (cell_target.town is not None) and attacker.level < 2:
                return [True, cell_target, 'tooweak']
            if attacker.get_owner() == defender.get_owner():
                return [True, cell_target, 'sameside']

        # Soldier can move only once a turn
        if attacker.moved:
            return [True, cell_target, 'alreadymoved']

        # Empty Space can't be conquered
        if cell_target.province.side == 0:
            return [True, cell_target, 'spaceisnotlegal']

        # One can't conquer his own soldiers            
        if cell_target.province.side == self.turn:
            if defender:
                return [True, cell_target, 'ownspacealreadyoccupied']

        found = False
        for edm_cell in cell_target.edm_list:
            # Next to target must be own land. The land must be
            # from the same province as the actor is from.
            if edm_cell is None:
                continue    # might be None
            if edm_cell.province == attacker.cell.province:
                found = True
        if not found:
            # No adjacent lands found, can't conquer places out of
            # soldier's reach
            return [True, cell_target, 'outofprovince']

        # Check for enemy unit blockers
        for edm_cell in cell_target.edm_list:
            if edm_cell is None:
                continue
            # Is the targets neighbour same side as the target
            if edm_cell.province.side == cell_target.province.side:
                # Has the neighbourds adjacent own piece a soldier defending?
                defender = edm_cell.soldier
                if defender:
                    # Yes it has
                    if defender.get_owner() != attacker.get_owner():
                        if defender.cur_cell.town is not None:
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

    def generate_map(self, minsize=None):
        # Generate simple random map
        if minsize is None:
            minsize = self.MAPSIZE_X * self.MAPSIZE_Y * 0.5

        self.create_cells(self.MAPSIZE_X, self.MAPSIZE_Y, piece=0)

        # fill random cells untill a specific percentage is land area
        while not self.count_land_area() >= minsize:
            self.fill_random_boxes(3, [1, 2, 3, 4, 5, 6])
            print self.count_land_area()

        # at the moment, there are no provinces and towns!
        for cur_cell in self.cells.values():
            assert isinstance(cur_cell, Cell)
            cur_cell.build_town()
            cur_cell.province = Province(cur_cell.tmp_side,cur_cell.town, [cur_cell])
        # now we have a map full of tiny Monacos ,)

        # first cycle:
        # for each province with only 1 cell:
        #   merge with a neighbour-province that has not more than 3 cell
        # merge it with a random neighbour
        for cur_cell in self.cells.values():
            assert isinstance(cur_cell.province, Province)
            if len(cur_cell.province.province_cells) == 1:
                # iterate over neighbours in random order
                did_merge = False
                for rand_edm in random.shuffle(cur_cell.edm_cells):
                    if rand_edm:    # it might be None
                        if did_merge:   # merge with at most one neighbour
                            break
                        if rand_edm.province != cur_cell.province:
                            assert isinstance(rand_edm, Cell)
                            if rand_edm.province.size() == 1:
                                rand_edm.change_to_province(cur_cell.province)
                                did_merge = True
                            else:
                                pass

        self.salary_time_to_towns_by_turn(self.get_player_id_list())

    def check_and_mark_if_someone_won(self):
        # If only one player has lost==False, he is winner
        no_losers = [z for z in self.player_list if not z.lost]
        if len(no_losers) == 1:
            no_losers[0].won = True
            return True
        return False

    def load_map(self, map_file_name):
        """
        Load a map from file
        """
        try:
            if self.map_edit_mode:
                self.map_edit_info = [0, 0, 1]
            map_file = open(map_file_name, 'r')
            for line_nr, data in enumerate(map_file.xreadlines()):
                if line_nr < 6:   # these lines describe human/ai player
                    data_2 = data[:-1]   # remove line ending
                    if data_2 == 'player':
                        if not self.map_edit_mode:
                            self.player_list.append(TPlayer('Player %d' % (y + 1), y + 1, self.screen, None))
                        else:
                            self.map_edit_info[0] += 1
                    if data_2 == 'ai':
                        if not self.map_edit_mode:
                            self.player_list.append(
                                TPlayer('%s (cpu)' % (random.choice(self.cpu_names)), y + 1, self.screen, ai.TAi(self)))
                        else:
                            self.map_edit_info[1] += 1
                else:
                    # these lines define the map
                    if len(data) > 0:
                        data_2 = data[:-1]
                        x_y, side = data_2.split('|')
                        x, y = x_y.split(' ')
                        pos = Vec2d(int(x), int(y))
                        self.cells[pos].side = int(side)
            map_file.close()
        except:
            pass

    def has_anyone_lost_the_game(self):
        # Check if anyone has recently lost the game:
        #    - not marked as lost and has 0 towns
        for possible_new_loser in self.player_list:
            if self.count_towns_on_world(possible_new_loser.id) == 0 and not possible_new_loser.lost:
                possible_new_loser.lost = True

    def count_towns_on_world(self, pid):
        # Self - explanatory
        result = 0
        for cell in self.cells.values():
            if cell.town:
                if (cell.town.province.side == pid):
                    result += 1
        return result

    def show_own_units_that_can_move(self):
        # Draw own units that have not moved yet
        for cell in self.cells.values():
            if cell.soldier:
                if (not cell.soldier.moved) and (cell.soldier.get_owner() == self.turn):
                    if self.seen_xy(cell.pos):
                        pixel_coord = hex_sys.hex_map_to_pixel(cell.pos - self.cursor.scroll_vec)
                        pygame.draw.circle(self.screen, (255, 255, 20), pixel_coord + Vec2d(20, 20), 20, 3)
        pygame.display.flip()
        time.sleep(0.5)
        self.draw_map()

    def salary_time_to_towns_by_turn(self, side_list):
        """
        Calculate towns income,expend and supplies. Kill soldiers without supplies.
        just_do_math -> if true, only income and expend are calculated

        ... was mostly moved to Town-class
        """

        for cell in self.cells.values():
            if cell.town and (cell.province.side in side_list):
                province = cell.province
                province.apply_income_and_costs()

                if province.supplies < 0:
                    # Not enough supplies, provinces soldiers are going
                    # to be terminated.
                    for province_cell in province.province_cells:
                        if province_cell.soldier:
                            # a Skull is drawn on the dead soldier
                            pixel_coord = hex_sys.hex_map_to_pixel(province_cell.pos - self.cursor.scroll_vec)
                            self.screen.blit(self.pics.gi('skull'), pixel_coord + Vec2d(10, 10))
                            # ... and now his/her end is coming:
                            province_cell.soldier.destroy()
        pygame.display.flip()

    def end_turn(self):
        # CPU INTENSIVE?
        self.has_anyone_lost_the_game()

        # Mark winner if found and get immediately 'True'
        # if winner was found
        if self.check_and_mark_if_someone_won():
            # Someone won, break the recursion loop
            self.turn = 0
            #self.data = {}
            # ToDo: delete cells etc.
            self.create_cells(self.MAPSIZE_X, self.MAPSIZE_Y, piece=0)
            return

        for player in self.player_list:
            if player.won:
                return

        self.turn += 1

        # Check if all players are scheduled already
        if len(self.player_list) + 1 <= self.turn:
            # Show last player's moves
            time.sleep(0.2)
            self.turn = 1
            # Every actor's 'moved' is reseted
            for cell in self.cells.values():
                if cell.soldier:
                    cell.soldier.moved = False

        # Update salaries and kill own unsupplied soldiers
        # old: self.salary_time_to_towns_by_turn([self.turn], False)
        # Update everyones salaries
        self.salary_time_to_towns_by_turn(self.get_player_id_list())

        # Check for errors
        if len(self.player_list) < self.turn:
            return

        if not self.player_list:
            return

        if not self.get_player_by_side(self.turn):
            return

        cur_player = self.get_player_by_side(self.turn)

        # Is the current player holding an instance of
        # artificial intelligence? If so, act too.
        if cur_player.ai_controller and not cur_player.lost:
            # Act here
            tmp_color = (
                self.sc['making_moves_text_color'][0],
                self.sc['making_moves_text_color'][1],
                self.sc['making_moves_text_color'][2]
            )
            gamemenu.text_at(self.screen,
                             'Player %s is making moves...' % cur_player.name,
                             Vec2d(self.sc['making_moves_text_topleft_corner']),
                             flip_now_flag=True, font=self.fonts.font_3,
                             wipe_background=False,
                             color=tmp_color
            )

            self.draw_scoreboard(True)

            # Ai buys and updates soldiers
            cur_player.ai_controller.buy_units_by_turn()

            # Here the AI makes moves
            act_dict = cur_player.ai_controller.act(self.ai_recursion_depth)

            self.draw_map()

            # Draw CPU player's moves
            if self.show_cpu_moves_with_lines:
                for from_cell, to_cell in act_dict.iteritems():
                    pos_1 = from_cell.pos
                    pos_2 = to_cell.spos
                    vec_offset = Vec2d(20, 20)
                    if self.seen_xy(pos_1):
                        if self.seen_xy(pos_2):
                            pixel_1_pos = hex_sys.hex_map_to_pixel(pos_1 - self.cursor.scroll_vec)
                            pixel_2_pos = hex_sys.hex_map_to_pixel(pos_2 - self.cursor.scroll_vec)

                            pygame.draw.line(self.screen,
                                             (255, 0, 0),
                                             pixel_1_pos + vec_offset,
                                             pixel_2_pos + vec_offset,
                                             2)
                            if _DEBUG > 1:
                                print pos_1, '', pos_2

            pygame.display.flip()

            # End of AI act
            # self.end_turn()
        else:
            self.draw_scoreboard(True)
            self.draw_map()
            pygame.display.flip()
            # If the human player has lost game, he is not going to play
            #if cur_player.lost:
            #    self.end_turn()

