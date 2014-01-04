#!/usr/bin/python
# Conquer is strategy-flavoured game written with PyGame

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

# This is one of the sloppiest looking files in the project...

import random, pygame, time, classcollection
from sys import path
from os import sep

_DEBUG = 1

# Initialize pygame
pygame.init()

# Path for game's graphics
graphics_path = path[0] + sep + "images" + sep

# Set the icon for the game window
pygame.display.set_icon(pygame.image.load(graphics_path + "soldier.png"))

# Import TheGameBoard and game_menu
from gameboard import TGB
import gamemenu
from game_view import GameView

# Generate new random seed
random.seed(round(time.time()))

# Instance of ImageHandler to contain used images in one place
IH = classcollection.TIH()

# Setting Release Version...
conquer_version = "0.2"

# Initialize the screen and set resolution
screen = pygame.display.set_mode((800, 600))

# Set windows caption
pygame.display.set_caption("Conquer " + conquer_version)

# Resources are greatly saved with this
pygame.event.set_blocked(pygame.MOUSEMOTION)

# Fill the screen with black color
screen.fill((0, 0, 0))

# Load images into image container, IH. (but not the interface images yet)
gamemenu.load_image_files_but_not_interface_image_files(IH, graphics_path)

# Create the Game View
# Parameters: pygame screen, image container, game path and game board
gv = GameView(screen, IH, path[0])


# Load the interface images... at the moment they need
# to be loaded after the Game Board has an instance
IH.add_image(pygame.image.load(graphics_path + gv.sc.get("interface_filename", "leiska.png")).convert(), "interface")
IH.add_image(pygame.image.load(graphics_path + gv.sc.get("menu_interface_filename", "menu.png")).convert(),
             "menu_interface")


# We have nothing to lose if we try to use psyco.
try:
    import psyco
except ImportError:
    pass
# If Psyco is not installed it is not a problem
else:
    psyco.full()


# Generate main menu
main_menu = gamemenu.TGameMenu(screen, IH.gi("menu_interface"), IH.gi("logo"),
                               [("Play Scenario", 0, [], "Play a premade map (scenarios-folder)"),
                                ("Play Random Island", 1, [], "Generate and play a random map"),
                                ("Options", 2, [], None),
                                ("Map Editor", 3, [], "Edit your own scenario"),
                                ("Quit", 4, [], None)],
                               (800 / 2 - 10, 200), spacing=60)

# Generate Options menu
options_menu = gamemenu.TGameMenu(screen, IH.gi("menu_interface"), IH.gi("logo"),
                                [("Show CPU moves with lines", 0, ["value_bool_editor",
                                                                   gv.show_cpu_moves_with_lines],
                                "(Use left and right arrow key) Show CPU soldiers moves with lines."),
                                ("CPU AI Recursion Depth", 1, ["value_int_editor", gv.ai_recursion_depth, [1, 20]],
                                "(Use left and right arrow key) Increase AI Recursion Depth: computer may play better but uses more CPU."),
                                ("Return", 2, [], None)],
                                (800 / 2 - 10, 200), spacing=60)

# The true main loop behing the whole application
main_loop_running = True
first_loop = True
while main_loop_running:
    # Get selection from main menu

    # DEBUG:
    if first_loop:
        # for debugging: automatically select random_map when menu is started for the first time
        selected = 1
        first_loop = False
    else:
        # also for debugging: exit directly
        selected = 4
        #selected = main_menu.get_selection()

    if selected == 0:
        # Dynamically generate menu items from scenario - files

        # Read scenarios
        scenarios = board.read_scenarios()

        generated_menu_items = []

        # Add option to step back to main menu
        generated_menu_items.append(("Back to Menu", 0, [], None))

        # Add scenarios as menuitems
        for i, scenario in enumerate(scenarios):
            generated_menu_items.append((scenario, i + 1, [], None))

        # Build the menu
        new_game_menu = gamemenu.TGameMenu(screen, IH.gi("menu_interface"), IH.gi("logo"),
                                           generated_menu_items, (800 / 2 - 10, 200), spacing=30)

        # Get selection from the newly build menu
        selection = new_game_menu.get_selection()
        if selection > 0:
            # User selecteded a scenario
            gv.start(map_edit_mode=False, random_map=False, scenario_file=new_game_menu.menu_items[selection][0])

    # User selecteded to generate a random map
    if selected == 1:
        # Ask player counts
        m1, m2 = gamemenu.get_human_and_cpu_count(gv.screen, gv.fonts)

        # hand over to game viewer
        gv.start(map_edit_mode=False, random_map=True, human_players=m1, players_cpu=m2)


    # User selecteded to see options
    if selected == 2:
        while 1:
            # Get selections from the options menu and break the loop
            # if user wants to get back to the main menu
            selected2 = options_menu.get_selection()
            if selected2 == 2:
                break

    # User selecteded to edit a scenario
    if selected == 3:
        # FIXME: little better looking
        # Ask player counts
        m1, m2 = gamemenu.get_human_and_cpu_count(gv.screen, gv.fonts)

        # Fill map with empty space
        board.create_cells(board.MAPSIZE_X, board.MAPSIZE_Y)

        # Turn the editing mode on
        board.player_list = []
        board.map_edit_mode = True
        board.map_edit_info = [m1, m2, 1]

        # Start Editing
        gv.start()
        # Editing Finished

        board.map_edit_mode = False
        board.map_edit_info = []

    # User selected to quit the game
    if selected == 4:
        main_loop_running = False
