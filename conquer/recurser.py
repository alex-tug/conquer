#from sets import Set
import random

from vec_2d import Vec2d

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

class TRecurser:
    def __init__(self,board):
        self.board = board
        self.recursed_land = []
        self.recursed_own_land_count = 0
  
    def count_towns_in_province(self, start_cell):
     # Initialize set to be used in crawling
        land_area_rec = []
        town_list = []
        
        # Crawl from (x,y), save crawling to land_area_rec and
        # crawl for player_id of start_cell
        self.crawl(start_cell, land_area_rec, [start_cell.province.side])
        # Lets iterate through crawled places
        for cell in land_area_rec:
            # Check if current coordinate has a town
            if cell.town:
                town_list.append(cell.town)
        return [town_list, land_area_rec]
  
    def get_free_cell_in_province(self, start_cell):
        land_area_rec = []
        self.crawl(start_cell, land_area_rec, [start_cell.province.side])
        # Check if province has area to afford town
        if len(land_area_rec) > 1:
            # It has enough area
            return [random.choice(list(land_area_rec)), list(land_area_rec)]
        else:
            # Not enough area, be careful with handling the None
            return [None, None]
   
    def is_the_whole_earth_connected(self):
        # Figure out if every land is connected to other
        # 1) Count land area 2) Recurse through one random land
        # 3) If recurse count == land area -> one big continent
        land_area = self.board.count_land_area()
        if _DEBUG > 1:
            print "World area: %d" % land_area
            
        land_area_rec = []
        
        # find a cell which is not water:
        start_cell = None
        for cur_cell in self.board.cells.values():
            if cur_cell.province.side > 0:
                start_cell = cur_cell

        # old:
        # for x in xrange(self.board.MAPSIZE_X):
        #     for y in xrange(self.board.MAPSIZE_Y):
        #         if self.board.cells[Vec2d(x,y)].side > 0:
        #             start_cell = self.board.cells[coord((x,y))]
        #             break

        if start_cell:
            self.crawl(start_cell, land_area_rec, [1,2,3,4,5,6])
        
        if len(land_area_rec) == land_area:
            return True
        else:
            return False
   
    def count_own_provinces(self):
        # Count how many provinces player controls
        counter = 0
        recursed_provinces = []
        for x in xrange(self.board.MAPSIZE_X):
            for y in xrange(self.board.MAPSIZE_Y):
                cur_coord = Vec2d(x, y)
                cur_cell = self.board.cells[cur_coord]
                if cur_cell.province.side == self.board.turn:
                    if cur_cell not in recursed_provinces:
                        self.recursed_own_land_count = 0
                        self.crawl(cur_cell,recursed_provinces,[self.board.turn])
                        counter += 1
        return counter
  
    def get_province_border_lands(self, start_cell):
        land_area_set = []
        province_owner = start_cell.province.side
        self.crawl(start_cell, land_area_set, [province_owner])
        border_area_set = []
        for cur_cell in land_area_set:
            edm = self.board.get_right_edm(cur_cell.pos.y)
            for i in xrange(6):
                new_coord = cur_cell.pos + edm[i]
                if self.board.valid_xy(new_coord):
                    new_cell = self.board.cells[new_coord]
                    if (new_cell.province.side != province_owner) and (new_cell.province.side != 0):
                            # This worked with sets because sets can't have duplicates
                            # now we use a list, so we have to check first
                            if new_cell not in border_area_set:
                                border_area_set.append(new_cell)
        return border_area_set
         
    def recurse_own_province(self, start_cell, player_id_list=None):
        # Count and recurse through own province' lands
        # clear recursed_land (a list of cells)
        assert start_cell is not None

        if player_id_list is None:
            player_id_list = [start_cell.province.side]
        del self.recursed_land[:]        
        self.recursed_own_land_count = 0
        
        self.crawl(start_cell,self.recursed_land,[player_id_list])
        
        return self.recursed_own_land_count

    def crawl(self, start_cell, recursion_list, find_list):
        """
        start_cell -> cell to start "crawling"
        recursion_list -> list to hold already "crawled" cells
        find_list -> list of players whose lands are to be searched
        """
        
        # Is the current land in find_list?
        if start_cell.province.side in find_list:
            # Check whether the location has been crawled already
            if start_cell not in recursion_list:
                self.recursed_own_land_count += 1
                recursion_list.append(start_cell)
                for edm_cell in start_cell.edm_list:
                    # Crawl neighbours
                    self.crawl(edm_cell, recursion_list, find_list)