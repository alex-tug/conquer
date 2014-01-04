import pygame
import time
#from types import *
import os
from operator import itemgetter
#import random

#from vec_2d import Vec2d
from classcollection import *
import ai
from gameboard import TGB
from graphics_helper import Plotter
import hex_sys



_DEBUG = 0

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

class GameView(object):
    def __init__(self, screen, ih, game_path):

        # Create GameBoard
        self.board = board = TGB(self)

        # Current path
        self.game_path = game_path + os.sep

        # Instance of cursor
        self.cursor = Cursor(self)
        self.cursor.x = 10
        self.cursor.y = 10

        # How many 'extra'-recursions cpu will make (max.) trying to figure out a good move
        self.ai_recursion_depth = 10

        # Pretty self-explanatory
        self.show_cpu_moves_with_lines = True

        # Pygame screen surface passed as 'pointer' for drawing methods
        self.screen = screen
        self.plotter = Plotter(self.screen)
        self.plotter.pos_0 = Vec2d(40, 0)
        self.fonts = self.plotter.fonts     # shortcut

        # Pointer to Picture Handler container class which has used pictures
        self.pics = ih

        # the actual game board (without score, etc.)
        assert isinstance(board, TGB)
        self.board = board

        # List of current players in a game
        self.player_list = []

        # Skin configuration dictionary
        self.sc = {}

        # Load the skin configuration file
        self.load_skin_file('skin')

        # Tuple that is used at sorting scorelist
        self.score_s = ()

        self.turn = self.board.turn

        # If the game (actual map view) is running, game_running is True
        self.game_running = False

        self.map_edit_mode = False

        # List for cpu player names and load the names
        self.cpu_names = []
        self.load_cpu_names()

    def start(self, map_edit_mode=False, scenario_file='unfair', random_map=False, human_players=3, players_cpu=3):

        self.map_edit_mode = map_edit_mode

        # Initialize a new game
        self.new_game(scenario_file=scenario_file, random_map=random_map,
                      human_players=human_players, random_players_cpu=players_cpu)

        # Start the game
        self.run_game()

    def new_game(self, scenario_file='unfair', random_map=False, human_players=3, random_players_cpu=3):
        """
        Makes everything ready for a new game. Call new_game before calling start_game.

        scenario_file -> Filename for scenario if random_map is set to False
        random_players_cpu -> CPU Player count in random generated map
        human_players -> Human Player count in random generated map
        """

        self.cursor.scroll_x = 0

        # Status Quo Ante (bellum), Settings before war ;)
        self.board.random_map = random_map
        self.board.turn = 1
        self.player_list = []
        self.board.score_s = ()

        self.generate_players(human_players, random_players_cpu)

        # Clear data and actors from possible previous maps
        self.board.cells.clear()

        if self.board.random_map:
            # Generate random map
            self.board.generate_map()
        else:
            # Read a scenario
            self.load_map(os.path.join(self.game_path, 'scenarios') + os.sep + scenario_file)

        # Calculate income and expends, and do changes for first players supplies
        self.board.pay_salary_to_towns([1])

        # JUST ONLY calculate everyones supply income and expends
        self.board.pay_salary_to_towns(self.board.get_player_id_list())

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

    # noinspection PyArgumentList
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
                self.sc['unit_status_text_color'] = pygame.Color(int(line[1]), int(line[2]), int(line[3]))
            if line[0] == 'scoreboard_text_color':
                self.sc['scoreboard_text_color'] = pygame.Color(int(line[1]), int(line[2]), int(line[3]))
            if line[0] == 'button_endturn':
                self.sc['button_endturn'] = (Vec2d(int(line[1]), int(line[2])), Vec2d(int(line[3]), int(line[4])))
            if line[0] == 'button_quit':
                self.sc['button_quit'] = (Vec2d(int(line[1]), int(line[2])), Vec2d(int(line[3]), int(line[4])))
            if line[0] == 'making_moves_text_topleft_corner':
                self.sc['making_moves_text_topleft_corner'] = Vec2d(int(line[1]), int(line[2]))
            if line[0] == 'menu_interface_filename':
                self.sc['menu_interface_filename'] = line[1]
            if line[0] == 'making_moves_text_color':
                self.sc['making_moves_text_color'] = pygame.Color(int(line[1]), int(line[2]), int(line[3]))

    def get_player_id_list(self):
        # Make a player-id - list and return it
        return [iteration.id for iteration in self.player_list]

    def get_player_by_name(self, player_name):
        for player in self.player_list:
            if player.name == player_name:
                return player
        return None

    def run_game(self):
        self.game_running = True
        # Instance of pygame's Clock
        clock = pygame.time.Clock()

        # The Main Loop to run a game
        while self.game_running:

            # Limit fps to 30, smaller resource usage
            clock.tick(30)

            player = self.board.get_player_by_id(self.turn)
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
                        if self.cursor.x < self.board.MAPSIZE_X and self.cursor.y < (self.board.MAPSIZE_Y - 1):
                            if event.button == 3:
                                if self.board.valid_xy(self.cursor.pos):
                                    target_cell = self.board.cells[self.cursor.pos]
                                    if target_cell.province.owner.id == self.turn:
                                        target_cell.build_soldier()

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
                            self.board.show_own_units_that_can_move()
                        if event.key == pygame.K_e:
                            self.end_turn()
                    else:
                        # In map editor mode, UP and DOWN keys change
                        # selected land
                        if event.key == pygame.K_UP:
                            self.board.map_edit_info[2] += 1
                            if self.board.map_edit_info[2] > 6:
                                self.board.map_edit_info[2] = 6
                        if event.key == pygame.K_DOWN:
                            self.board.map_edit_info[2] -= 1
                            if self.board.map_edit_info[2] < 0:
                                self.board.map_edit_info[2] = 0
                                # Draw the scoreboard without calculating and sorting scores
                self.draw_scoreboard(False)
                # Draw the map
                self.draw_map()
                # Show the drawed content
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
            self.board.create_cells(self.board.MAPSIZE_X, self.board.MAPSIZE_Y, cell_type=0)
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
            for cell in self.board.cells.values():
                if cell.soldier:
                    cell.soldier.moved = False

        # Update salaries and kill own unsupplied soldiers
        # old: self.salary_time_to_towns_by_turn([self.turn], False)
        # Update everyones salaries
        self.board.pay_salary_to_towns(self.player_list)

        # Check for errors
        if len(self.player_list) < self.turn:
            return

        if not self.player_list:
            return

        if not self.board.get_player_by_id(self.turn):
            return

        cur_player = self.board.get_player_by_id(self.turn)

        # Is the current player holding an instance of
        # artificial intelligence? If so, act too.
        if cur_player.ai_controller and not cur_player.lost:
            # Act here
            tmp_color = (
                self.sc['making_moves_text_color'][0],
                self.sc['making_moves_text_color'][1],
                self.sc['making_moves_text_color'][2]
            )
            self.plotter.text_at('Player %s is making moves...' % cur_player.name,
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

    def check_and_mark_if_someone_won(self):
        # If only one player has lost==False, he is winner
        no_losers = [z for z in self.player_list if not z.lost]
        if len(no_losers) == 1:
            no_losers[0].won = True
            return True
        return False

    def has_anyone_lost_the_game(self):
        # Check if anyone has recently lost the game:
        #    - not marked as lost and has 0 towns
        for possible_new_loser in self.player_list:
            if self.board.count_towns_on_world(possible_new_loser.id) == 0 and not possible_new_loser.lost:
                possible_new_loser.lost = True

    def seen_xy(self, pos):
        # Return boolean value if the coordinate is seen by player
        # (not scrolled out of borders)
        return self.cursor.scroll_x <= pos.x <= (self.cursor.scroll_x + 14)

    def draw_scoreboard(self, update=False):
        """
        Draw Scoreboard
        update -> If true, scores are calculated and sorted
        """
        if update or not self.score_s:
            # Update scores
            scores = {}
            for cur_player in self.player_list:
                if not cur_player.lost:
                    # Count existing players land count
                    scores[cur_player] = self.board.whole_map_situation_score(cur_player.id)
                    # Sort points
            self.score_s = sorted(scores.iteritems(), key=itemgetter(1))

        # Iterate every player
        for player in self.player_list:
            # Check if a player has won
            if player.won:
                # a Player has won, show the information
                self.cursor.clicked_obj = None

                self.plotter.cur_color = pygame.Color((255, 255, 255))
                self.plotter.cur_font = self.fonts.font_4
                if player.ai_controller:
                    self.plotter.text_at('Player %s won the game!' % player.name, Vec2d(200, 200))
                else:
                    self.plotter.text_at('You (%s) won the game!' % player.name, Vec2d(200, 200))
                pygame.display.flip()

        counter = 0
        # Draw the scores, counter puts text in right row.
        # Skin configuration file is used here
        for cur_player in reversed(self.score_s):
            pos_base = self.sc['scoreboard_text_topleft_corner']
            pos_shift = Vec2d(0, 35)

            self.screen.blit(self.pics.gi('cell_%d' % cur_player[0].id),
                             pos_base + pos_shift * counter + Vec2d(0, -13))

            self.plotter.text_at('%d     %s' % (cur_player[1], cur_player[0].name),
                                 pos_base + pos_shift * counter + Vec2d(15, 0),
                                 color=self.sc['scoreboard_text_color'],
                                 font=self.fonts.font_4,
                                 wipe_background=False)

            counter += 1

        # Lost players are discarded from player_list, so next line
        # may make an error. Thats why the try - expression.
        cur_player = self.get_player_by_id(self.turn)
        # Human player
        if not cur_player.ai_controller:
            text_pos = Vec2d(630, 300)
            self.plotter.cur_color = pygame.Color('black')
            self.plotter.cur_font = self.plotter.fonts.font_3
            if not cur_player.lost:
                # Human player's turn, tell it
                self.plotter.text_at('Your (%s) turn' % cur_player.name,
                                     text_pos,
                                     wipe_background=False)
            else:
                # The human player has lost, tell it
                self.plotter.text_at('You (%s) lost...' % cur_player.name,
                                     text_pos,
                                     wipe_background=False)

    def draw_map_edit_utilities(self):
        # Extra drawing routines for scenario editing mode

        # Text for selected map tile
        if self.board.map_edit_info[2] == 0:
            str_text = 'Eraser'
        else:
            if self.board.map_edit_info[2] <= (self.board.map_edit_info[0] + self.board.map_edit_info[1]):
                str_text = 'Player #%d land' % self.board.map_edit_info[2]
            else:
                # Land without player in the map, good for connecting player
                # provinces in own maps.
                str_text = 'Land #%d without player' % self.board.map_edit_info[2]

        # Show the selected map tile text
        self.plotter.cur_color = pygame.Color((0, 0, 0))
        self.plotter.cur_font = self.plotter.fonts.font_4
        self.plotter.text_at('Selected:', Vec2d(620, 80), wipe_background=False)
        self.plotter.text_at(str_text, Vec2d(620, 100), wipe_background=False)

        # Draw players captions in the scenario
        counter = 0
        cur_pos_base = Vec2d(620, 130)
        cur_pos_shift = Vec2d(0, 20)
        self.plotter.cur_font = self.plotter.fonts.font_4
        self.plotter.cur_color = pygame.Color((0, 0, 0))
        for i in xrange(0, self.board.map_edit_info[0]):
            counter += 1
            self.plotter.text_at('Player #%d = Human' % counter,
                                 cur_pos_base + counter * cur_pos_shift,
                                 wipe_background=False)

        for i in xrange(0, self.board.map_edit_info[1]):
            counter += 1
            self.plotter.text_at('Player #%d = CPU' % counter,
                                 cur_pos_base + counter * cur_pos_shift,
                                 wipe_background=False)

        if (6 - counter) > 0:
            for i in range(0, (6 - counter)):
                counter += 1
                self.plotter.text_at('Player #%d = No player' % counter,
                                     cur_pos_base + counter * cur_pos_shift,
                                     wipe_background=False)

    def get_visible_cells(self):
        visible_cells = []
        # 14/15 ... is the number of cells visible in the standard screen size
        for x in xrange(self.cursor.scroll_x, self.cursor.scroll_x + 15):
            for y in xrange(14):
                pos = Vec2d(x, y)
                if self.board.valid_xy(pos):
                    visible_cells.append(self.board.cells[pos])
        return visible_cells

    def draw_border(self, cell_1, cell_2):
        """
            this will draw the border, but only on the side of cell_1!
        """
        # determine where to draw the border
        pos_offset = Vec2d(19, 22-1)
        # first convert the lattice positions to absolute screen positions
        screen_pos_cell_1 = hex_sys.hex_map_to_pixel(cell_1.pos)
        screen_pos_cell_2 = hex_sys.hex_map_to_pixel(cell_2.pos)
        len_edge = 19
        vec_connect = (screen_pos_cell_2 - screen_pos_cell_1)
        # draw the border on 'our' side
        pos_mid = screen_pos_cell_1 + vec_connect * 0.48 + pos_offset
        assert isinstance(vec_connect, Vec2d)
        vec_edge = vec_connect.perpendicular()
        vec_edge_norm = vec_edge.normalized()
        color = cell_1.province.owner.color
        start_pos = pos_mid - vec_edge_norm*len_edge*0.5
        end_pos = pos_mid + vec_edge_norm*len_edge*0.5
        width = 2
        pygame.draw.line(self.screen, color, start_pos, end_pos, width)

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
            pass
            # Map editing interface
            #self.screen.blit(self.pics.gi('mapedit'), (0, 0))
            #self.draw_map_edit_utilities()

        # Loop pieces to be drawn (horizontally there is scrolling too)
        visible_cells = self.get_visible_cells()
        if visible_cells:
            for cur_cell in visible_cells:
                assert isinstance(cur_cell, Cell)
                # There is land to draw
                cell_image_key = cur_cell.get_image_key()
                if cell_image_key:  # otherwise cell is water which is already shown as background
                    # Get pixel coordinates
                    pixel_coord = hex_sys.hex_map_to_pixel(cur_cell.pos - self.cursor.scroll_vec)
                    # Draw the piece
                    self.screen.blit(self.pics.gi(cell_image_key), pixel_coord)

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
                        self.plotter.text_at(str_text, pixel_coord + Vec2d(20, 20), font=self.plotter.fonts.font_1)

                    if cur_cell.town_flag:
                        # a Resource Town was found
                        self.screen.blit(self.pics.gi('town'), pixel_coord + Vec2d(3, 8))

                        # If the town is on our 's and we are not AI controlled, then we'll
                        # draw the supply count on the town.
                        if cur_cell.province.owner == self.board.turn:
                            if not self.board.get_player_by_id(cur_cell.province.owner).ai_controller:
                                self.plotter.text_at('%d' % cur_cell.province.supplies,
                                                     pixel_coord + Vec2d(15, 13),
                                                     font=self.fonts.font_2,
                                                     wipe_background=False)

                    for cur_edm in cur_cell.edm_cells:
                        if cur_edm:     # -> not on the edge of the map
                            if cur_edm.province != cur_cell.province:
                                # it's a province border
                                self.draw_border(cur_cell, cur_edm)

                    # print coordinates (for debugging)
                    #str_text = str(int(cur_cell.pos.x)) + ':' + str(int(cur_cell.pos.y))
                    #self.plotter.text_at(str_text, pixel_coord + Vec2d(10, 20), font=self.plotter.fonts.font_1)


        # If an actor is selected, then we'll draw red box around the actor
        if self.cursor.clicked_obj:
            pixel_pos = hex_sys.hex_map_to_pixel(self.cursor.pos - self.cursor.scroll_vec)
            pygame.draw.rect(self.screen, self.cursor.get_color(), (pixel_pos.x, pixel_pos.y, 40, 40), 2)

        # if a cell is selected, we will print some infos about it
        if isinstance(self.cursor.clicked_cell, Cell):
            cur_cell = self.cursor.clicked_cell
            coord_topleft = self.sc['unit_status_text_topleft_corner']
            vec_offset = Vec2d(240, 10)     # second column
            vec_shift = Vec2d(0, 20)
            self.plotter.text_at('cell pos: %d:%d' % (cur_cell.pos.x, cur_cell.pos.y),
                                 coord_topleft + vec_offset + 1 * vec_shift,
                                 wipe_background=False)
            self.plotter.text_at('screen pos: %f:%f' % (cur_cell.pos.x, cur_cell.pos.y),
                                 coord_topleft + vec_offset + 2 * vec_shift,
                                 wipe_background=False)
            self.plotter.text_at('is town? ' + str(cur_cell.town_flag),
                                 coord_topleft + vec_offset + 3 * vec_shift,
                                 wipe_background=False)
            if cur_cell.province.owner:
                self.plotter.text_at('owner: ' + str(cur_cell.province.owner.name),
                                     coord_topleft + vec_offset + 4 * vec_shift,
                                     wipe_background=False)

        # If a town is chosen, we'll draw information about it:
        #   Income, Expends, Supplies
        if isinstance(self.cursor.clicked_obj, Town):
            cur_town = self.cursor.clicked_obj
            self.plotter.cur_color = (
                self.sc['unit_status_text_color'][0],
                self.sc['unit_status_text_color'][1],
                self.sc['unit_status_text_color'][2])
            self.plotter.cur_font = self.fonts.font_4
            coord_topleft = self.sc['unit_status_text_topleft_corner']
            vec_offset = Vec2d(0, 10)
            vec_shift = Vec2d(0, 20)

            self.plotter.text_at('Resource town',
                                 coord_topleft + vec_offset + 1 * vec_shift,
                                 wipe_background=False)
            self.plotter.text_at('Income: %d' % cur_town.province.income,
                                 coord_topleft + vec_offset + 2 * vec_shift,
                                 wipe_background=False)
            self.plotter.text_at('Expends: %d' % cur_town.province.expends,
                                 coord_topleft + vec_offset + 3 * vec_shift,
                                 wipe_background=False)
            self.plotter.text_at('Supplies: %d' % cur_town.province.supplies,
                                 coord_topleft + vec_offset + 4 * vec_shift,
                                 wipe_background=False)
            self.screen.blit(self.pics.gi('town'), coord_topleft)

    def load_cpu_names(self):
        # Read names from file to cpu name list
        file_handle = open(self.game_path + 'cpu_player_names', 'r')
        for line in file_handle.readlines():
            if line.endswith('\n'):
                self.cpu_names.append(line[:-1])
            else:
                self.cpu_names.append(line)
        file_handle.close()

    @staticmethod
    def get_random_color_list():
        color_names_list = ['red', 'green', 'blue', 'black', 'grey', 'yellow']
        random.shuffle(color_names_list)
        return color_names_list

    def generate_players(self, human_players, random_players_cpu):
        # each player will have a random color
        color_names_list = self.get_random_color_list()
        # If map is randomly generated, add players
        if self.board.random_map:
            for i in xrange(human_players):
                color = pygame.Color(color_names_list.pop())
                self.player_list.append(Player('Player %d' % (i + 1),
                                               i + 1,
                                               color))
            for i in xrange(random_players_cpu):
                color = pygame.Color(color_names_list.pop())
                self.player_list.append(
                    Player('%s (cpu)' % (random.choice(self.cpu_names)),
                           i + (human_players + 1),
                           color,
                           ai.TAi(self)))

    def load_map(self, map_file_name):
        """
        Load a map from file
        """
        # ToDo: read/write color of each player
        color_names_list = self.get_random_color_list()
        try:
            if self.board.map_edit_mode:
                self.board.map_edit_info = [0, 0, 1]
            map_file = open(map_file_name, 'r')
            for line_nr, data in enumerate(map_file.xreadlines()):
                if line_nr < 6:   # these lines describe human/ai player
                    data_2 = data[:-1]   # remove line ending
                    color = color_names_list.pop()
                    if data_2 == 'player':
                        if not self.map_edit_mode:
                            self.player_list.append(Player('Player %d' % (y + 1), y + 1, color))
                        else:
                            self.board.map_edit_info[0] += 1
                    if data_2 == 'ai':
                        if not self.map_edit_mode:
                            self.player_list.append(
                                Player('%s (cpu)' % (random.choice(self.cpu_names)), y + 1, color, ai.TAi(self)))
                        else:
                            self.board.map_edit_info[1] += 1
                else:
                    # these lines define the map
                    if len(data) > 0:
                        data_2 = data[:-1]
                        x_y, owner = data_2.split('|')
                        x, y = x_y.split(' ')
                        pos = Vec2d(int(x), int(y))
                        self.board.cells[pos].province.owner = int(owner)
            map_file.close()
        except:
            pass

    def get_player_by_id(self, player_id):
        for player in self.player_list:
            if player.id == player_id:
                return player
        return None

    def get_random_existing_player(self):
        return random.choice(self.player_list)