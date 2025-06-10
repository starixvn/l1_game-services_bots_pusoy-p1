import pandas as pd
from treys import Card, Deck
import numpy as np
from src.utils.poker_evaluator import ChinesePokerEvaluator
from src.utils.utils import Utils
import itertools
from collections import defaultdict
import math
from src.data_preparation.normalization import Normalization

class FeatureEngineering(object):
    def __init__(self,
                 path_csv_file_mapping=r"src/res/mapping_rank_with_card_string_and_int_strength.csv",
                 path_proba_folder=r"src/res"):
        self.path_csv_file_mapping = path_csv_file_mapping
        self.utils = Utils()
        self.evaluator = ChinesePokerEvaluator()
        self.list_combo_type = ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House",
                    "Flush", "Straight", "Three of a Kind", "Two Pair", "Pair", "High Card"]
        self.mapping_suit_int_to_str = {1: "spade", 2: "heart", 4: "diamond", 8: "club"}
        self.__check_mapping_suit_int_to_str()
        self.mapping_rank_int_to_str = {0: "deuce", 1: "trey", 2: "four", 3: "five", 4: "six", 5: "seven", 
                            6: "eight", 7: "nine", 8: "ten", 9: "jack", 10: "queen", 11: "king", 12: "ace"}
        self.list_key_board_remain_info = self.__get_list_key_board_remain_info()
        self.mapping_rank_count_hist_to_n_Six_Pair = self.__get_mapping_rank_count_hist_to_n_Six_Pair()
        self.mapping_len_card_rank_by_suit_to_n_Three_Flush = self.__get_mapping_len_card_rank_by_suit_to_n_Three_Flush()
        self.path_proba_folder = path_proba_folder
        self.database_search_front = self.gen_proba_table_lookup(f"{self.path_proba_folder}/front_proba_int_with_suit.txt")
        self.database_search_middle = self.gen_proba_table_lookup(f"{self.path_proba_folder}/middle_proba_int_with_suit.txt")
        self.database_search_back = self.gen_proba_table_lookup(f"{self.path_proba_folder}/back_proba_int_with_suit.txt")
        assert len(self.database_search_front) == 455*4 and len(self.database_search_middle) == len(self.database_search_back) == 7462*4
        assert self.database_search_middle['1, 1'] == 100.0 and self.database_search_back['1, 1'] < 100.0
        self.rank_mapping = self.utils.create_rank_mapping_with_new_rank_for_four_three_full_house()
        self.map_front_rank_to_int_strength = self.create_mapping_front_rank_to_int_strength()
        self.set_full_deck = set(Deck().cards) 
        
    def __check_mapping_suit_int_to_str(self):
        for suit_int in self.mapping_suit_int_to_str:
            assert self.mapping_suit_int_to_str[suit_int][0] == Card.INT_SUIT_TO_CHAR_SUIT[suit_int]
    
    def __get_list_key_board_remain_info(self):
        list_key = []
        for rank_str in self.mapping_rank_int_to_str.values():
            list_key.append(f"n_{rank_str}")
        for suit_str in self.mapping_suit_int_to_str.values():
            list_key.append(f"n_{suit_str}")
        assert len(list_key) == 13 + 4, f"The length of list_key is not correct: {len(list_key)}"
        return list_key

    def __count_n_Six_Pair_natural_win(self, rank_count_hist):            
        n_six_pair = 0
        for tuple_n_pair_Four in itertools.product(range(3), repeat=rank_count_hist[4]):
            n_pair_remain = 6 - sum(tuple_n_pair_Four)
            for j in range(n_pair_remain + 1):
                n_six_pair_from_Two_Three = math.comb(rank_count_hist[2], j) * \
                    math.comb(rank_count_hist[3], n_pair_remain - j) * (3 ** (n_pair_remain - j))
                for n_pair_Four_elem in tuple_n_pair_Four:
                    if n_pair_Four_elem == 1:
                        n_six_pair_from_Two_Three *= 6
                n_six_pair += n_six_pair_from_Two_Three
        return n_six_pair

    def __get_mapping_rank_count_hist_to_n_Six_Pair(self):
        mapping_rank_count_hist_to_n_Six_Pair = {}
        for n_pair in range(0, 14):
            for n_three in range(0, 14):
                for n_four in range(0, 10):
                    n_cards = (n_pair * 2) + (n_three * 3) + (n_four * 4)
                    if n_cards > 39 or (n_cards + (13 - n_pair - n_three - n_four) < 39):
                        continue 
                    rank_count_hist = np.array([0, 0, n_pair, n_three, n_four], dtype=np.uint8)
                    n_Six_Pair = self.__count_n_Six_Pair_natural_win(rank_count_hist)
                    mapping_rank_count_hist_to_n_Six_Pair[(n_pair, n_three, n_four)] = n_Six_Pair
        return mapping_rank_count_hist_to_n_Six_Pair

    def __count_flush_two_suit_type(self, len_card_rank_by_suit, n_suit_1, n_suit_2):
        n_flush = 0
        for i in range(4):
            first_flush = math.comb(len_card_rank_by_suit[i], n_suit_1)
            for j in range(4):
                if j == i: continue
                second_flush = math.comb(len_card_rank_by_suit[j], n_suit_2)
                n_flush += first_flush*second_flush
        return n_flush

    def __count_flush_three_suit_type(self, len_card_rank_by_suit):
        n_flush = 0
        for i in range(4):
            first_flush = math.comb(len_card_rank_by_suit[i], 5)
            for j in range(i+1, 4):
                second_flush = math.comb(len_card_rank_by_suit[j], 5)
                for k in range(4):
                    if k in [i, j]: continue
                    third_flush = math.comb(len_card_rank_by_suit[k], 3)
                    n_flush += first_flush*second_flush*third_flush
        return n_flush

    def __count_n_Three_Flush_natural_win(self, len_card_rank_by_suit):
        n_flush_three_suit = self.__count_flush_three_suit_type(len_card_rank_by_suit)
        n_flush_two_suit = self.__count_flush_two_suit_type(len_card_rank_by_suit, 8, 5) + \
                            self.__count_flush_two_suit_type(len_card_rank_by_suit, 10, 3)
        return n_flush_three_suit + n_flush_two_suit

    def __get_mapping_len_card_rank_by_suit_to_n_Three_Flush(self):
        mapping_len_card_rank_by_suit_to_n_Three_Flush = {}
        for first_flush in range(0, 14):
            for second_flush in range(first_flush, 14):
                for third_flush in range(second_flush, 14):
                    for fourth_flush in range(third_flush, 14):
                        if first_flush + second_flush + third_flush + fourth_flush != 39: continue
                        len_card_rank_by_suit = np.array([first_flush, second_flush, 
                                                third_flush, fourth_flush], dtype=np.uint8)
                        n_Three_Flush = self.__count_n_Three_Flush_natural_win(len_card_rank_by_suit)
                        mapping_len_card_rank_by_suit_to_n_Three_Flush[tuple(len_card_rank_by_suit)] = n_Three_Flush
        return mapping_len_card_rank_by_suit_to_n_Three_Flush

    def gen_proba_table_lookup(self, file_path_proba):
        with open(file_path_proba, "r") as file:
            all_data = file.readlines()
        
        dict_database = dict()
        for line in all_data:
            data = line.split(':')
            if len(data) == 2:
                proba = float(data[0])
                cards_info = data[1].strip()
                dict_database[cards_info] = proba
        return dict_database

    def cal_board_remain_info(self, board):
        board_remain = tuple(self.set_full_deck - set(board))

        board_remain_info = defaultdict(int)
        for card_int in board_remain:
            rank_str = self.mapping_rank_int_to_str[Card.get_rank_int(card_int)]
            suit_str = self.mapping_suit_int_to_str[Card.get_suit_int(card_int)]

            board_remain_info[f"n_{rank_str}"] += 1
            board_remain_info[f"n_{suit_str}"] += 1

        return tuple(board_remain_info[key] for key in self.list_key_board_remain_info)
    
    def gen_stats_board_remain_info_column(self, all_data_avg_point):
        first_row = all_data_avg_point.iloc[0]
        board = first_row["back_card"] + first_row["mid_card"] + first_row["front_card"]
        board_remain_info = self.cal_board_remain_info(board)
        all_data_avg_point[self.list_key_board_remain_info] = board_remain_info

    def is_specific_combo_type(self, combo_type, rank, is_front_hand):
        actual_combo_type = self.utils.get_combo_type(rank, is_front_hand)
        return int(actual_combo_type == combo_type)

    def gen_binary_feature_for_bonus_combo(self, all_data_avg_point):
        for combo_type in self.list_combo_type:
            if combo_type == "High Card": continue
            all_data_avg_point[f"is_{combo_type.replace(' ', '_')}_back"] = all_data_avg_point["back_rank"].apply(
                            lambda x: self.is_specific_combo_type(combo_type, x, is_front_hand=False))
        for combo_type in self.list_combo_type:
            all_data_avg_point[f"is_{combo_type.replace(' ', '_')}_mid"] = all_data_avg_point["mid_rank"].apply(
                            lambda x: self.is_specific_combo_type(combo_type, x, is_front_hand=False))
        for combo_type in ["Three of a Kind", "Pair", "High Card"]:
            all_data_avg_point[f"is_{combo_type.replace(' ', '_')}_front"] = all_data_avg_point["front_rank"].apply(
                            lambda x: self.is_specific_combo_type(combo_type, x, is_front_hand=True))       

    def __count_n_RoyalFlush_StraightFlush(self, list_card_rank_by_suit):
        n_Royal_Flush = 0
        n_Straight_Flush = 0
        for suit in list_card_rank_by_suit:
            for slice in self.utils._Utils__generate_all_straight_slice(list_card_rank_by_suit[suit], 5):
                if slice[-1] == 12:
                    n_Royal_Flush += 1
                else:
                    n_Straight_Flush += 1
        return n_Royal_Flush, n_Straight_Flush

    def __count_n_Flush(self, list_card_rank_by_suit):
        return sum([math.comb(len(list_card_rank_by_suit[suit]), 5) for suit in list_card_rank_by_suit])

    def __count_n_Straight(self, dict_count_card_rank):
        list_card_rank = list(dict_count_card_rank.keys())
        n_straight = 0
        for slice in self.utils._Utils__generate_all_straight_slice(list_card_rank, 5):
            n_straight += np.prod([dict_count_card_rank[rank] for rank in slice])
        return n_straight

    def __count_n_Dragon(self, dict_count_card_rank):
        if len(dict_count_card_rank) == 13:
            return np.prod(list(dict_count_card_rank.values()))
        elif len(dict_count_card_rank) < 13:
            return 0
        else:
            raise ValueError(f"The length of dict_count_card_rank is not correct: {len(dict_count_card_rank)}")

    def __cal_rank_count_histogram(self, dict_count_card_rank):
        rank_count_hist = np.zeros(5, dtype=np.uint8)
        for count in dict_count_card_rank.values():
            rank_count_hist[count] += 1
        return rank_count_hist

    def __cal_len_card_rank_by_suit(self, list_card_rank_by_suit):
        len_card_rank_by_suit = np.zeros(4, dtype=np.uint8)
        for idx, suit in enumerate(list_card_rank_by_suit.keys()):
            len_card_rank_by_suit[idx] = len(list_card_rank_by_suit[suit])
        len_card_rank_by_suit.sort()
        return len_card_rank_by_suit

    def cal_combo_type_board_remain(self, board):
        board_remain = tuple(self.set_full_deck - set(board))
        list_card_rank_by_suit = defaultdict(list)
        dict_count_card_rank = defaultdict(int)

        for card in board_remain:
            rank = Card.get_rank_int(card)
            suit = Card.get_suit_int(card)

            list_card_rank_by_suit[suit].append(rank)
            dict_count_card_rank[rank] += 1
        rank_count_hist = self.__cal_rank_count_histogram(dict_count_card_rank)
        len_card_rank_by_suit = self.__cal_len_card_rank_by_suit(list_card_rank_by_suit)
        
        n_Royal_Flush, n_Straight_Flush = self.__count_n_RoyalFlush_StraightFlush(list_card_rank_by_suit)
        n_Flush = self.__count_n_Flush(list_card_rank_by_suit) - n_Royal_Flush - n_Straight_Flush
        n_Straight = self.__count_n_Straight(dict_count_card_rank) - n_Royal_Flush - n_Straight_Flush
        n_Dragon = self.__count_n_Dragon(dict_count_card_rank)
        n_Six_Pair = self.mapping_rank_count_hist_to_n_Six_Pair[(rank_count_hist[2], 
                                            rank_count_hist[3], rank_count_hist[4])]
        n_Three_Flush = self.mapping_len_card_rank_by_suit_to_n_Three_Flush[tuple(len_card_rank_by_suit)]
        return n_Royal_Flush, n_Straight_Flush, n_Flush, n_Straight, n_Dragon, n_Six_Pair, n_Three_Flush

    def gen_stats_combo_type_board_remain_column(self, all_data_avg_point):
        first_row = all_data_avg_point.iloc[0]
        board = first_row["back_card"] + first_row["mid_card"] + first_row["front_card"]
        combo_type_board_remain = self.cal_combo_type_board_remain(board)
        all_data_avg_point[["n_Royal_Flush", "n_Straight_Flush", "n_Flush",
            "n_Straight", "n_Dragon", "n_Six_Pair", "n_Three_Flush"]] = combo_type_board_remain

    def create_mapping_front_rank_to_int_strength(self):
        df = pd.read_csv(self.path_csv_file_mapping)
        return dict(zip(df["rank"], df["rank_strength"]))
    
    def transform_front_rank_to_int_strength(self, all_data_avg_point):
        all_data_avg_point["front_rank"] = all_data_avg_point["front_rank"].map(self.map_front_rank_to_int_strength)

    def transform_Four_Three_Full_House_back_mid_rank(self, all_data_avg_point):
        all_data_avg_point["back_rank"] = all_data_avg_point["back_rank"].map(self.rank_mapping)
        all_data_avg_point["mid_rank"] = all_data_avg_point["mid_rank"].map(self.rank_mapping)

    def create_proba_columns(self, all_data_avg_point):
        all_data_avg_point["back_proba"] = (all_data_avg_point["back_rank"].astype(str) + ", " \
                        + all_data_avg_point["back_suit_strength"].astype(str)).map(self.database_search_back)
        all_data_avg_point["mid_proba"] = (all_data_avg_point["mid_rank"].astype(str) + ", " \
                        + all_data_avg_point["mid_suit_strength"].astype(str)).map(self.database_search_middle)
        all_data_avg_point["front_proba"] = (all_data_avg_point["front_rank"].astype(str) + ", " \
                        + all_data_avg_point["front_suit_strength"].astype(str)).map(self.database_search_front)

    def transform(self, all_data_avg_point):
        all_data_avg_point.reset_index(drop=True, inplace=True)
        self.gen_stats_board_remain_info_column(all_data_avg_point)
        self.gen_stats_combo_type_board_remain_column(all_data_avg_point)
        self.gen_binary_feature_for_bonus_combo(all_data_avg_point)
        # self.create_proba_columns(all_data_avg_point)
        self.transform_front_rank_to_int_strength(all_data_avg_point)
        self.transform_Four_Three_Full_House_back_mid_rank(all_data_avg_point)

        feature_cols = list(all_data_avg_point.columns.difference(["is_3_straight", "is_3_flush",
                                                            "back_card", "mid_card", "front_card"]))
        dataset = all_data_avg_point[feature_cols].copy()
        assert dataset.isnull().sum().sum() == 0

        del all_data_avg_point
        return dataset