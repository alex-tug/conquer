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

import random,pygame,time,classcollection
from sys import path
from os import sep

_DEBUG = 0

# Initialize pygame
pygame.init()

# Path for game's graphics
graphics_path = path[0] + sep + "images" + sep

# Set the icon for the game window
pygame.display.set_icon(pygame.image.load(graphics_path+"soldier.png"))

# Import TheGameBoard and gamemenu
import gameboard
from gameboard import TGB
import gamemenu

# Generate new random seed
random.seed(round(time.time()))

# Instance of ImageHandler to contain used images in one place
IH = classcollection.TIH()

# Setting Release Version...
conquer_version = "0.1"

# Initialize the screen and set resolution
screeni = pygame.display.set_mode((800,600))

# Set windows caption
pygame.display.set_caption("Conquer " + conquer_version)

# Resources are greatly saved with this
pygame.event.set_blocked(pygame.MOUSEMOTION)

# Fill the screen with black color
screeni.fill((0,0,0))

# Load images into image container, IH. (but not the interface images yet)
gameboard.load_image_files_but_not_interface_image_files(IH,graphics_path)

# Create the Game Board
# Parameters: pygame screen, image container and game path
gb = TGB(screeni,IH,path[0])

# Load the interface images... at the moment they need
# to be loaded after the Game Board has an instance
IH.add_image(pygame.image.load(graphics_path+gb.sc.get("interface_filename","leiska.png")).convert(),"interface")
IH.add_image(pygame.image.load(graphics_path+gb.sc.get("menu_interface_filename","menu.png")).convert(),"menu_interface")


# We have nothing to lose if we try to use psyco.
try:
	import psyco
except ImportError:
	pass
	# If Psyco is not installed it is not a problem
else:
	psyco.full()


# Generate main menu
mainmenu = gamemenu.TGameMenu(screeni, IH.gi("menu_interface"),IH.gi("logo"),
[("Play Scenario",0,[],"Play a premade map (scenarios-folder)"),
("Play Random Island",1,[],"Generate and play a random map"),
("Options",2,[],None),
("Map Editor",3,[],"Edit your own scenario"),
("Quit",4,[],None)],
(800/2-10,200), spacing = 60)

# Generate Options menu
optionsmenu = gamemenu.TGameMenu(screeni, IH.gi("menu_interface"),IH.gi("logo"),
[("Show CPU moves with lines",0,["value_bool_editor",gb.show_cpu_moves_with_lines],"(Use left and right arrow key) Show CPU soldiers moves with lines."),
("CPU AI Recursion Depth",1,["value_int_editor",gb.ai_recursion_depth,[1,20]],"(Use left and right arrow key) Increase AI Recursion Depth: computer may play better but uses more CPU."),
("Return",2,[],None)],
(800/2-10,200), spacing = 60)

# The true main loop behing the whole application
main_loop_running = True
while main_loop_running:
	# Get selection from main menu
	tulos = mainmenu.get_selection()
	if tulos == 0:
		
		# Dynamically generate menu items from scenario - files
		
		# Read scenarios
		scenarios = gb.read_scenarios()
		
		generated_menu_items = []
		
		# Add option to step back to main menu 
		generated_menu_items.append(("Back to Menu",0,[],None))
		
		# Add scenarios as menuitems
		for i,scenario in enumerate(scenarios):
			generated_menu_items.append((scenario,i+1,[],None))
			
		# Build the menu
		newgamemenu = gamemenu.TGameMenu(screeni, IH.gi("menu_interface"),IH.gi("logo"),
		generated_menu_items, (800/2-10,200), spacing = 30)
		
		# Get selection from the newly build menu
		selection = newgamemenu.get_selection()
		if selection > 0:
			# User selected a scenario
			gb.map_edit_mode = False
			gb.new_game(randommap = False, scenariofile = newgamemenu.menuitems[selection][0])
			gb.start_game()

	# User selected to generate a random map
	if tulos == 1:
		# Ask player counts
		m1,m2 = gb.get_human_and_cpu_count()
		gb.map_edit_mode = False
		
		# Initialize a new game
		gb.new_game(randommap = True, humanplayers = m1, randomplayers_cpu = m2)
		
		# Start the game
		gb.start_game()

	# User selected to see options
	if tulos == 2:
		while 1:
			# Get selections from the options menu and break the loop
			# if user wants to get back to the main menu
			tulos2 = optionsmenu.get_selection()
			if tulos2 == 2:
				break

	# User selected to edit a scenario
	if tulos == 3:
		# FIXME: little better looking
		# Ask player counts
		m1,m2 = gb.get_human_and_cpu_count()
		
		# Fill map with empty space
		gb.fillmap(0)
		
		# Turn the editing mode on
		gb.playerlist = []
		gb.map_edit_mode = True
		gb.map_edit_info = [m1,m2,1]
		gb.actors.clear()
		
		# Start Editing
		gb.start_game()
		# Editing Finished
		
		gb.map_edit_mode = False
		gb.map_edit_info = []
		
	# User selected to quit the game
	if tulos == 4:
		main_loop_running = False
