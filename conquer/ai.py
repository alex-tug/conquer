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

import random# , time
#from classcollection import coord

class TAi:
    def __init__(self,board):
        """board -> TGameBoard instance which is the parent"""
        self.board = board
        
    def act(self,depth):
        # List of executed moves that is returned
        # it's a dict where key and values are cells
        # (from_cell : to_cell)
        act_list = {}
        
        own_soldier_actor_set = set()
        
        for cell in self.board.cells.values():
            if cell.soldier:
                soldier = cell.soldier
                if soldier.get_owner() == self.board.turn and not soldier.moved:
                    own_soldier_actor_set.add(soldier)
        # More CPU, more depth
        for cur_recusion_depth in xrange(self.board.ai_recursion_depth):        
            # We'll iterate every actor through a copy
            for cur_soldier in own_soldier_actor_set.copy():
                if cur_soldier.dead:
                    continue
                # We'll move only own soldiers that have not moved yet
                if not cur_soldier.moved and cur_soldier.get_owner() == self.board.turn:
                    # Memory for found move (=target cell of that move)
                    mem_cell  = None
                    # Memory for found move's points (/score)
                    mem_p = 0
                    
                    # Make a copy of the original map
                    backup = self.board.cells.copy()
                    score_list = []
                    target_cell_list = []
                    loppulaskija = 0
                    found_no_brute_force_solution = False
                    
                    possible_moves = self.board.rek.get_province_border_lands(cur_soldier.cur_cell)
                    possible_moves = list(possible_moves)
                    random.shuffle(possible_moves)
                    
                    for target_cell in possible_moves:
                        if found_no_brute_force_solution:
                            continue

                        # Player ID of the possible move's land
                        target_owner = target_cell.side

                        # Target must be enemy's land
                        if ((target_owner != self.board.turn) and (target_owner != 0)):

                            # Is the move possible?
                            blocked = self.board.is_blocked(cur_soldier,target_cell)
                            if not blocked[0]:
                                
                                # The move is possible, we'll simulate it
                                self.board.try_to_conquer(cur_soldier,target_cell,True)

                                # The points of the move                                
                                score = self.board.rek.recurse_own_island(cur_soldier.cur_cell)                                
                                
                                # Land area of the target island
                                area_island = self.board.rek.get_free_cell_in_province(target_cell)

                                # We'll favour more to conquer from large islands
                                if area_island[1]:
                                    score += len(area_island[1]) / 5
                                
                                # Is there a soldier at target land? => add points
                                if target_cell.soldier:
                                        score += target_cell.soldier.level * 2
                                        
                                # Is there a town at target land? => add points
                                if target_cell.town and cur_soldier.level > 1:
                                        score += 5
                                        score += target_cell.supplies / 2
                                        score += (target_cell.income - target_cell.expends)
                                                                                
                                # Put the move and it's points in memory
                                score_list.append(score)
                                target_cell_list.append(target_cell)

                                # Restore the original map and try different moves
                                self.board.cells={}
                                self.board.cells.update(backup)

                                # Found move better than the one in memory?
                                if score > mem_p:
                                    # Yes it is, update
                                    mem_p = score
                                    mem_cell = target_cell
                                    
                                if len(score_list) > depth:
                                    # Now we have been looking for a move too long
                                    
                                    if len(score_list) > (depth*5):
                                        # Found no move...
                                        # This shouldn't be never executed
                                        mem_cell = None
                                        found_no_brute_force_solution = True
                                        own_soldier_actor_set.discard(cur_soldier)                
                                    # If the current found move is better than
                                    # anyone else, we'll choose it
                                    if score > max(score_list):
                                        mem_p = score
                                        mem_cell = target_cell
                                        act_list[cur_soldier.cell] = mem_cell
                                        self.board.try_to_conquer(cur_soldier,target_cell,False)
                                        found_no_brute_force_solution = True
                                        own_soldier_actor_set.discard(cur_soldier)
                                    # Too much used time here
                                    loppulaskija += 1
                                    if loppulaskija == depth:
                                        # We'll choose best move we have found
                                        mem_p = max(score_list)
                                        mem_cell = self.board.cells[ target_cell_list[score_list.index(mem_p)] ]
                                        act_list[cur_soldier.cur_cell] = mem_cell
                                        self.board.try_to_conquer(cur_soldier,mem_cell,False)
                                        backup = self.board.cells.copy()
                                        found_no_brute_force_solution = True
                                        own_soldier_actor_set.discard(cur_soldier)
                                        
                    if (mem_cell is None) and (found_no_brute_force_solution==False):
                        # Normally we shouldn't end up here, but if we
                        # do, we choose the best current move.
                        mem_p = max(score_list)
                        mem_cell = self.board.cells[ target_cell_list[score_list.index(mem_p)] ]
                        act_list[cur_soldier.cur_cell] = mem_cell
                        self.board.try_to_conquer(cur_soldier,mem_cell,False)
                        backup = self.board.cells.copy()
                        own_soldier_actor_set.discard(cur_soldier)
        # Return dictionary of made moves
        return act_list

    def buy_units_by_turn(self):
        """
        This function buys and updates soldiers for CPU Players.
        """

        # This is VERY MESSY function, cleaning will be done sometime

        board = self.board  # shorten code
        # Iterate through a copy as original actors is probably going to be modified
        for cur_cell in self.board.cells.copy().values():

            cur_town = cur_cell.town
            if cur_town is not None:

                if (not cur_town.dead) and (cur_cell.supplies > 0) and (cur_town.get_owner() == board.turn):
                    # Alive Town & current turn player's & has (supplies > 0)

                    # Has the island space for a new soldier?
                    # new_town_cell new random place for actor (not checked if legal)
                    # cell_list island's land coordinates
                    new_place_cell, cell_list = board.rek.get_free_cell_in_province(cur_cell)

                    # No space for actor
                    if not new_place_cell:
                        continue

                    # 500 tries to find a place for actor
                    ok = False
                    tries = 0
                    while not ok and tries < 500:
                        tries += 1
                        new_place_cell = random.choice(cell_list)
                        if not new_place_cell.soldier:
                            ok = True
                    if tries == 500:
                        ok = False

                    # Count the amount of lvl<6 soldiers on the island
                    level_list = []
                    soldier_counter = 0
                    soldier_counter_2 = 0
                    lvl_1_counter = 0
                    for cur_cell in cell_list:
                        cur_soldier = cur_cell.soldier
                        if cur_soldier:
                            if cur_soldier.get_owner() == board.turn and not cur_soldier.dead:
                                soldier_counter_2 += 1
                                if cur_soldier.level == 1:
                                    lvl_1_counter += 1
                                if cur_soldier.level < 6:
                                    soldier_counter += 1
                                    level_list.append(cur_soldier.level)

                    # Does the island have upgradable soldiers (lvl<6)?
                    if soldier_counter != 0:
                        # When the island has soldiers, it is more likely
                        # to update them. 66% chance to update existing
                        # soldiers.
                        if random.randint(1, 3) != 2:
                            ok = False

                    free_countries = []
                    for cell in cell_list:
                        if not cell.soldier:
                            free_countries.append(cell)

                    # Do we have any soldiers at all?
                    if soldier_counter_2 != 0:
                        # We do, count how many free lands there are per soldier
                        fact = len(free_countries) / soldier_counter_2
                        # If three or more, we need new soldiers
                        if fact >= 3:
                            ok = False
                            while not ok and tries < 500:
                                tries += 1
                                new_place_cell = random.choice(cell_list)
                                if not board.cells[new_place_cell].soldier:
                                    ok = True
                                    # We have probably enough soldiers so update them
                        if fact <= 2:
                            ok = False

                    # BUT If we have upgradable soldiers AND over half of the
                    # possible attack targets need better soldiers, we'll
                    # update soldiers :)
                    # FIXME: pretty complicated
                    danger = False
                    too_weak_count = 0
                    a_searched = []
                    if soldier_counter > 0:
                        for cur_cell in cell_list:
                            edm = board.get_right_edm(cur_cell.pos.y)
                            for i in xrange(6):
                                new_pos = cur_cell.pos + edm[i]
                                if board.valid_xy(new_pos):
                                    if new_pos in a_searched:
                                        continue
                                    if board.cells[new_pos].side != board.turn:
                                        a_searched.append(new_pos)
                                        board.cells[new_pos].build_soldier()
                                        new_soldier = board.cells[new_pos].soldier

                                        found_hard_guy = soldier_counter
                                        for challenger in level_list:
                                            new_soldier.level = challenger
                                            if board.is_blocked(new_soldier, new_pos)[3] == "tooweak":
                                                found_hard_guy -= 1
                                        if found_hard_guy == 0:
                                            too_weak_count += 1
                        if (float(too_weak_count) / float(len(a_searched))) >= 0.3:
                            ok = False
                            danger = True

                    # But if we don't have any soldiers, we'll buy them...
                    if soldier_counter_2 == 0:
                        ok = True

                    # We still shouldn't buy too much
                    if (cur_cell.income - cur_cell.expends) < 1:
                        return

                    # Not enough supplies?
                    if cur_cell.supplies < 1:
                        return

                    if ok:
                        # Okay, WE WILL BUY NEW SOLDIERS
                        m11 = random.randint(0, 1)
                        m22 = random.randint(0, 1)
                        # Little variation...
                        while cur_cell.supplies > m11 and (cur_cell.income - cur_cell.expends) > m22:
                            ok2 = False
                            while not ok2 and tries < 500:
                                tries += 1
                                new_place_cell = random.choice(cell_list)
                                if not board.cells[new_place_cell].soldier:
                                    ok2 = True
                            if ok2:
                                # Add new soldier and make financial calculus

                                cur_cell.supplies -= 1
                                cur_cell.expends += 1
                                cur_cell.income -= 1
                                cur_cell.build_soldier()

                                # 90% - (lvl*10%) chance to update it
                                # So mathematically possibility to update straight to level6:
                                # 0.8 * 0.7 * 0.6 * 0.5 * 0.4 = 7%
                                # Straight to level5:
                                # 17%
                                # Straight to level4:
                                # 34%
                                # And so on...

                                while cur_cell.supplies > 0 and (
                                        cur_cell.income - cur_cell.expends) > 0 and cur_cell.soldier.level < 6:
                                    if random.randint(1, 10) <= (9 - cur_cell.soldier.level):
                                        cur_cell.soldier.level += 1
                                        cur_cell.expends += 1
                                    else:
                                        break

                        # If we didn't buy with every supplies, we can update soldiers
                        if m11 or m22:
                            self.update_own_soldiers(cur_cell, cell_list, lvl_1_counter,
                                                     soldier_counter_2, danger)
                    if not ok:
                        self.update_own_soldiers(cur_cell, cell_list, lvl_1_counter,
                                                 soldier_counter_2, danger)

    def update_own_soldiers(self, town_cell, cell_list, lvl_1_counter, soldier_counter_2, danger):
        # Update soldiers with supplies
        tries = 0

        # When we'll stop?
        critical_cash = 0

        running = True
        # We'll update as long as supplies are used or panic has arisen
        while town_cell.supplies > critical_cash and running:
            tries += 1
            # We'll try up to one hundred times
            if tries == 100:
                running = False

            # Iterate through actors
            for cur_cell in self.board.cells.values():
                if (cur_cell.side == town_cell.side) and cur_cell.soldier:
                    cur_soldier = cur_cell.soldier
                    # Panic - button has been pressed ;)
                    if not running:
                        continue

                    # Do we still have income...?
                    if (cur_cell.income - cur_cell.expends) > 0:
                        # Self - explanatory
                        if cur_cell in cell_list and not cur_soldier.dead and cur_soldier.get_owner() == town_cell.side:
                            # Level 6 are not updated, level 1 have better chance to be updated.
                            # But if we just need better soldiers we'll update everyone (paatos).
                            if cur_soldier.level < 6:
                                # Level 1 soldiers found
                                if lvl_1_counter > 0 and (soldier_counter_2 - lvl_1_counter) > 0:
                                    if cur_soldier.level == 1:
                                        # No critical need for updates?
                                        if not danger:
                                            # 25% change not to update lvl1
                                            if random.randint(1, 4) != 2:
                                                continue

                                # Soldier is updated
                                town_cell.expends += 1
                                town_cell.supplies -= 1
                                cur_soldier.level += 1
                                # Panic with supplies?
                                if town_cell.supplies <= critical_cash:
                                    running = False
                                if (town_cell.income - town_cell.expends) == critical_cash:
                                    running = False