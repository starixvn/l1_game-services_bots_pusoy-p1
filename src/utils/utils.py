from treys import Card
from treys.lookup import LookupTable
from collections import Counter
from pydantic import BaseModel
from celery.result import AsyncResult

from typing import Optional

class TaskOut(BaseModel):
    id: str
    status: str
    result: Optional[str] = None
    
def _to_task_out(r: AsyncResult) -> TaskOut:
    return TaskOut(
        id=r.task_id, 
        status=r.status, 
        result=r.traceback if r.failed() else r.result
    )

class Utils(object):
    """
    This class is used to provide some utility functions for the Chinese Poker game.
    """
    mapping_straight_rank_to_highest_card = {1600 + i: 12 - i for i in range(10)}

    def __init__(self):  
        self.mapping_suit_int_to_strength = {1: 1, 2: 2, 4: 4, 8: 3}

    @staticmethod
    def get_combo_type(rank, is_front_hand=False) -> str:
        """
        This function is used to get the type of combo from the given combo's rank.
        Args:
            - combo_rank: int, the rank of the combo
            - is_front_hand: bool, whether the combo is the front hand or not
        Returns:
            - str, the type of combo
        """
        combo_type = None
        if is_front_hand:
            if 1609 <= rank <= 2467 + 1:
                combo_type = "Three of a Kind"
            elif 3325 <= rank < 6185 + 1:
                combo_type = "Pair"
            elif 6185 + 1 <= rank < 7462 + 1:
                combo_type = "High Card"
            else:
                raise Exception("Invalid rank for front hand, cannot return rank class")
        else:
            if rank == 1:
                combo_type = "Royal Flush"
            elif rank <= 10:
                combo_type = "Straight Flush"
            elif rank <= 166:
                combo_type = "Four of a Kind"
            elif rank <= 322:
                combo_type = "Full House"
            elif rank <= 1599:
                combo_type = "Flush"
            elif rank <= 1609:
                combo_type = "Straight"
            elif rank <= 2467:
                combo_type = "Three of a Kind"
            elif rank <= 3325:
                combo_type = "Two Pair"
            elif rank <= 6185:
                combo_type = "Pair"
            elif rank <= 7462:
                combo_type = "High Card"
            else:
                raise Exception("Invalid rank, cannot return rank class")
        return combo_type

    def sort_cards_by_rank(self, cards) -> list:
        """
        This function is used to sort the given cards by rank.
        Args:
            - cards: list, the list of cards
        Returns:
            - list, the list of cards sorted by rank
        """
        return sorted(cards, key=lambda card: Card.get_rank_int(card))
    
    def create_mapping_an_unique_value_for_each_interval(self, rank_range, interval):
        mapping = {}
        for i in range(len(rank_range)):
            mapping[rank_range[i]] = rank_range[(i//interval) * interval]
        return mapping
    
    def create_rank_mapping_with_new_rank_for_four_three_full_house(self):
        four_of_a_kind_rank_range = list(range(LookupTable.MAX_STRAIGHT_FLUSH + 1, LookupTable.MAX_FOUR_OF_A_KIND + 1))
        three_of_a_kind_rank_range = list(range(LookupTable.MAX_STRAIGHT + 1, LookupTable.MAX_THREE_OF_A_KIND + 1)) 
        full_house_rank_range = list(range(LookupTable.MAX_FOUR_OF_A_KIND + 1, LookupTable.MAX_FULL_HOUSE + 1))

        rank_mapping = {}
        for i in range(1, LookupTable.MAX_HIGH_CARD + 1):
            rank_mapping[i] = i
        for rank_range in [four_of_a_kind_rank_range, three_of_a_kind_rank_range, full_house_rank_range]:
            interval = len(rank_range) // 13
            mapping = self.create_mapping_an_unique_value_for_each_interval(rank_range, interval)
            rank_mapping.update(mapping)
        return rank_mapping

    @staticmethod
    def get_suit_strength_of_highest_card_HighCard(combo):
        highest_card = None
        max_rank_int = -1

        for card in combo:
            rank_int = ((card >> 8) & 0xF)
            if rank_int > max_rank_int:
                max_rank_int = rank_int
                highest_card = card

        highest_card_suit_int = ((highest_card >> 12) & 0xF)
        if highest_card_suit_int == 8: highest_card_suit_int = 3
        return highest_card_suit_int
    
    @staticmethod
    def get_suit_strength_of_highest_card_Flush_StraightFlush_RoyalFlush(combo):
        #These 3 combo have the same suit of 5 cards, so we just need to get the suit of any card
        suit_int = ((combo[0] >> 12) & 0xF)
        if suit_int == 8: suit_int = 3
        return suit_int
    
    @staticmethod
    def get_suit_strength_of_highest_card_Straight(straight_combo, rank):
        highest_card = Utils.mapping_straight_rank_to_highest_card[rank]
        for card in straight_combo:
            if ((card >> 8) & 0xF) == highest_card:
                suit_strength = ((card >> 12) & 0xF)
                if suit_strength == 8: suit_strength = 3
                return suit_strength
    
    @staticmethod
    def get_suit_strength_of_one_pair(pair_combo):
        rank_suit_strength = {}
        max_suit_strength_of_pair = -1
        for card in pair_combo:
            rank = ((card >> 8) & 0xF)
            suit_strength = ((card >> 12) & 0xF)
            if suit_strength == 8: suit_strength = 3

            if rank in rank_suit_strength:
                max_suit_strength_of_pair = max(rank_suit_strength[rank], suit_strength)
                break    
            else:
                rank_suit_strength[rank] = suit_strength

        return max_suit_strength_of_pair
    
    @staticmethod
    def get_suit_strength_of_two_pair(two_pair_combo):
        rank_suit_strength = {}
        max_pair_rank = -1
        max_suit_strength_of_pair = -1
        for card in two_pair_combo:
            rank = ((card >> 8) & 0xF)
            suit_strength = ((card >> 12) & 0xF)
            if suit_strength == 8: suit_strength = 3

            if rank in rank_suit_strength:
                if rank > max_pair_rank:
                    max_pair_rank = rank
                    max_suit_strength_of_pair = max(rank_suit_strength[rank], suit_strength)
            else:
                rank_suit_strength[rank] = suit_strength
                    
        return max_suit_strength_of_pair 
        
    @staticmethod
    def get_suit_strength_back_mid(combo, combo_rank):
        if 10 < combo_rank <= 322 or 1609 < combo_rank <= 2467:
            return 4
        elif 3325 < combo_rank <= 6185:
            return Utils.get_suit_strength_of_one_pair(combo)
        elif 2467 < combo_rank <= 3325:
            return Utils.get_suit_strength_of_two_pair(combo)
        elif 1 <= combo_rank <= 10 or 322 < combo_rank <= 1599:
            return Utils.get_suit_strength_of_highest_card_Flush_StraightFlush_RoyalFlush(combo)
        elif 1599 < combo_rank <= 1609:
            return Utils.get_suit_strength_of_highest_card_Straight(combo, combo_rank)
        elif 6185 < combo_rank <= 7462:
            return Utils.get_suit_strength_of_highest_card_HighCard(combo)
        else:
            raise Exception(f"Invalid combo rank: {combo_rank}")
        
    @staticmethod
    def get_suit_strength_front(combo, combo_rank):
        if 1609 <= combo_rank <= 2467 + 1:
            return 4
        elif 3325 <= combo_rank < 6185 + 1:
            return Utils.get_suit_strength_of_one_pair(combo)
        elif 6185 + 1 <= combo_rank < 7462 + 1:
            return Utils.get_suit_strength_of_highest_card_HighCard(combo)
        else:
            raise Exception(f"Invalid combo rank: {combo_rank}")
        
    @staticmethod
    def is_natural_win_six_pair(board):
        assert len(board) == 13
        max_pair_rank = -1
        map_rank_with_count_and_suit = {}

        for card in board:
            rank = ((card >> 8) & 0xF)
            suit_strength = ((card >> 12) & 0xF)
            if suit_strength == 8: suit_strength = 3

            if rank in map_rank_with_count_and_suit:
                if rank > max_pair_rank: max_pair_rank = rank

                count, old_suit_strength = map_rank_with_count_and_suit[rank]
                if suit_strength > old_suit_strength:
                    map_rank_with_count_and_suit[rank] = (count + 1, suit_strength)
                else:
                    map_rank_with_count_and_suit[rank] = (count + 1, old_suit_strength)
            else:
                map_rank_with_count_and_suit[rank] = (1, suit_strength)
        
        n_pair = sum([(count // 2) for count, _ in map_rank_with_count_and_suit.values()])
        if n_pair == 6:
            return True, max_pair_rank, map_rank_with_count_and_suit[max_pair_rank][1]
        else:
            return False, -1, -1
        
    @staticmethod
    def is_natural_win_dragon(board):
        assert len(board) == 13
        
        rank_suit_strength = {}
        for card in board:
            rank = ((card >> 8) & 0xF)
            suit_strength = ((card >> 12) & 0xF)
            if suit_strength == 8: suit_strength = 3

            rank_suit_strength[rank] = suit_strength
        if len(rank_suit_strength) == 13:
            return True, rank_suit_strength[12]
        else:
            return False, -1
        
    @staticmethod
    def is_straight(list_rank): 
        is_straight = False    

        rank_set = set(list_rank)
        if len(rank_set) == len(list_rank):
            rank_range = max(rank_set) - min(rank_set) + 1
            if rank_range == len(list_rank):
                is_straight = True
            else: #Check for the case of A2345 or A23, ...
                if 12 in rank_set:
                    if rank_set == {12} | set(range(len(rank_set) - 1)):
                        is_straight = True
        return is_straight

    @staticmethod
    def is_three_flush_general(board):
        list_suit = [((card >> 12) & 0xF) for card in board]
        suit_counter = Counter(list_suit).most_common()
        list_suit_count = []
        for _, count in suit_counter:
            list_suit_count.append(count)
        assert sorted(list_suit_count, reverse=True) == list_suit_count, \
            "The list_suit_count should be sorted in descending order"
        if list_suit_count == [5, 5, 3] or list_suit_count == [8, 5] or list_suit_count == [10, 3]:            
            return True
        else:
            return False   

    @staticmethod
    def __remove_multiple_elements_from_list(list_rank, list_remove):
        list_rank_after_remove = list_rank.copy()
        for rank in list_remove:
            list_rank_after_remove.remove(rank)
        return list_rank_after_remove

    @staticmethod
    def __generate_all_straight_slice(list_rank, len_straight):
        list_unique_rank = list(set(list_rank))
        list_unique_rank.sort()
        
        for i in range(len(list_unique_rank)):
            slice_list = list_unique_rank[i:i+len_straight]
            if len(slice_list) < len_straight:
                slice_list += list_unique_rank[:len_straight - len(slice_list)]

            if Utils.is_straight(slice_list):
                yield slice_list

    @staticmethod
    def is_three_straight_general(board):
        list_rank = [((card >> 8) & 0xF) for card in board]

        for slice_1 in Utils.__generate_all_straight_slice(list_rank, 5):
            list_rank_remain = Utils.__remove_multiple_elements_from_list(list_rank, slice_1)
                
            for slice_2 in Utils.__generate_all_straight_slice(list_rank_remain, 5):
                three_card_remain = Utils.__remove_multiple_elements_from_list(list_rank_remain, slice_2)

                if Utils.is_straight(three_card_remain):
                    return True
        return False   
    
    @staticmethod
    def is_natural_win_three_flush_special_only_flush(back_rank, mid_rank, front_card):
        if 322 < back_rank <= 1599 and 322 < mid_rank <= 1599:
            list_front_suit = set([((card >> 12) & 0xF) for card in front_card])
            if len(list_front_suit) == 1:
                return True
        return False
    
    @staticmethod
    def is_natural_win_three_straight_special_only_straight(back_rank, mid_rank, front_card):
        if 1599 < back_rank <= 1609 and 1599 < mid_rank <= 1609:
            list_front_rank = [((card >> 8) & 0xF) for card in front_card]
            if Utils.is_straight(list_front_rank):
                return True
        return False

if __name__ == "__main__":
    from treys import Deck

    combo = Deck().draw(5)
    Utils.get_suit_strength_of_combo(combo, "Flush")