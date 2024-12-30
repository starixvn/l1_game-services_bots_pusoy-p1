import pandas as pd
from treys import Card, Deck
import itertools
import time
from src.utils.utils import Utils
from src.utils.poker_evaluator import ChinesePokerEvaluator
from src.data_preparation.feature_engineer import FeatureEngineering
from src.data_preparation.normalization import Normalization
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from keras.models import load_model

class PusoyBot(object):
    def __init__(self, 
                board=None,
                model_dir=r"src/model/multi_layer_perceptron.keras"):
        self.board = board if board is not None else Deck().draw(13)
        self.evaluator = ChinesePokerEvaluator() 
        self.utils = Utils()
        self.MLP_model = load_model(model_dir)
        self.feature_engineer = FeatureEngineering()
        self.normalizer = Normalization()

    def is_trivial_arrangement(self, back_rank, mid_rank):
        back_type = self.utils.get_combo_type(back_rank)
        mid_type = self.utils.get_combo_type(mid_rank)
        if (back_type == "High Card") or (back_type == "Pair" and mid_type == "High Card"):
            return True
        return False

    def update_arrangement_info_with_back_mid_front_card(self, arrangement_info, 
                                                back_card, mid_card, front_card):
        back_card_dict = {f"back_card_{i+1}": card for i, card in enumerate(back_card)}
        mid_card_dict = {f"mid_card_{i+1}": card for i, card in enumerate(mid_card)}
        front_card_dict = {f"front_card_{i+1}": card for i, card in enumerate(front_card)}
        arrangement_info.update(back_card_dict)
        arrangement_info.update(mid_card_dict)
        arrangement_info.update(front_card_dict)

    def gen_database_arrangement(self) -> pd.DataFrame:
        """
        This function is used to generate the database of all possible arrangements of the given 13 cards.
        """
        data_arrangement = []
        for back_card in itertools.combinations(self.board, 5):
            back_rank = self.evaluator.evaluate(back_card, tuple())           

            board_remain = [card for card in self.board if card not in back_card]
            for mid_card in itertools.combinations(board_remain, 5):
                mid_rank = self.evaluator.evaluate(mid_card, tuple())                

                if back_rank <= mid_rank:  # The strength of back combo must be greater than or equal to the mid combo                    
                    front_card = tuple([card for card in board_remain if card not in mid_card])
                    front_rank = self.evaluator.evaluate(front_card, tuple())
                    
                    if mid_rank <= front_rank: # The strength of mid combo must be greater than or equal to the front combo
                        back_suit_strength = self.utils.get_suit_strength_back_mid(back_card, back_rank)
                        mid_suit_strength = self.utils.get_suit_strength_back_mid(mid_card, mid_rank)
                        if back_rank == mid_rank and back_suit_strength < mid_suit_strength:
                            continue
                        if self.is_trivial_arrangement(back_rank, mid_rank):
                            continue
                        front_suit_strength = self.utils.get_suit_strength_front(front_card, front_rank)

                        arrangement_info = {
                            "back_rank": back_rank,
                            "mid_rank": mid_rank,
                            "front_rank": front_rank,

                            "back_suit_strength": back_suit_strength,
                            "mid_suit_strength": mid_suit_strength,
                            "front_suit_strength": front_suit_strength,

                            "is_3_straight": self.utils.is_natural_win_three_straight_special_only_straight(
                                back_rank, mid_rank, front_card),
                            "is_3_flush": self.utils.is_natural_win_three_flush_special_only_flush(
                                back_rank, mid_rank, front_card),
                        }
                        self.update_arrangement_info_with_back_mid_front_card(arrangement_info,
                                                                back_card, mid_card, front_card)
                        data_arrangement.append(arrangement_info)
                        
        return pd.DataFrame(data_arrangement).drop_duplicates(subset=["back_rank", "mid_rank", "front_rank", 
                                        "back_suit_strength", "mid_suit_strength", "front_suit_strength"])

    def update_average_point_of_natural_win_3_straight_and_3_flush(self, data_arrange):
        #For the row which is is_3_straight = True or is_3_flush = True, we will update the Average_Point_Predicted to 9.0
        data_arrange.loc[data_arrange["is_3_straight"] | data_arrange["is_3_flush"], 
                         "Average_Point_Predicted"] = 9.0
        return data_arrange
                
    def predict_average_point(self, data_arrange):
        dataset = self.feature_engineer.transform(data_arrange.copy())
        self.normalizer.normalize_dataset(dataset)
        X = dataset.values
        y = self.MLP_model.predict(X)
        data_arrange["Average_Point_Predicted"] = y
        return data_arrange
    
    def gen_database_arrangement_with_predict_average_point(self):
        data_arrange = self.gen_database_arrangement()
        data_arrange = self.predict_average_point(data_arrange)
        data_arrange = self.update_average_point_of_natural_win_3_straight_and_3_flush(data_arrange)
        return data_arrange

    def get_best_arrangement(self):
        data_arrange = self.gen_database_arrangement_with_predict_average_point()
        data_arrange.reset_index(drop=True, inplace=True)
        best_arrangement = data_arrange.loc[data_arrange["Average_Point_Predicted"].idxmax()].to_dict()
        return best_arrangement

    def gen_sorted_database_arrangement_with_predict_average_point(self):
        data_arrange = self.gen_database_arrangement_with_predict_average_point()
        data_arrange_sorted = data_arrange.sort_values(by="Average_Point_Predicted", ascending=False)
        return data_arrange_sorted
    
    def gen_back_mid_front_type(self, data_arrange):
        for position, is_front_hand in zip(["back", "mid", "front"], [False, False, True]):
            data_arrange[f"{position}_type"] = data_arrange[f"{position}_rank"].apply(
                                        lambda x: self.utils.get_combo_type(x, is_front_hand=is_front_hand))
        return data_arrange

    def get_best_arrangement_for_each_back_mid_front_type(self):
        data_arrange_sorted = self.gen_sorted_database_arrangement_with_predict_average_point()
        data_arrange_sorted = self.gen_back_mid_front_type(data_arrange_sorted)
        return data_arrange_sorted.drop_duplicates(subset=["back_type", "mid_type", "front_type"], keep="first")
    
    def get_top_k_back_mid_front_type_arrangements(self, k=16):
        data_best_arrangement_for_each_back_mid_front_type = self.get_best_arrangement_for_each_back_mid_front_type()
        return data_best_arrangement_for_each_back_mid_front_type.iloc[:k].to_dict(orient='records')

    def print_one_hand(self, position, cards) -> None:
        print(f"{position}: ", end="")
        Card.print_pretty_cards(self.utils.sort_cards_by_rank(cards))
        rank = self.evaluator.evaluate(cards, tuple())
        combo_type = self.utils.get_combo_type(rank) if position != "Front" else self.utils.get_combo_type(rank, is_front_hand=True)
        suit_strength = self.utils.get_suit_strength_back_mid(cards, rank) if position != "Front" else self.utils.get_suit_strength_front(cards, rank)
        print("Type: {}, Rank: {}, Suit Strength: {}".format(combo_type, rank, suit_strength))

    def print_one_arrangement(self, data) -> None:
        print("\nAverage Point Predicted:", data["Average_Point_Predicted"])
        self.print_one_hand("Back", tuple(data[col] for col in self.feature_engineer.list_back_card_name))
        self.print_one_hand("Mid", tuple(data[col] for col in self.feature_engineer.list_mid_card_name))
        self.print_one_hand("Front", tuple(data[col] for col in self.feature_engineer.list_front_card_name))



if __name__ == "__main__":
    cls_test = PusoyBot()
    start_time = time.time()
    list_best_arrangement = cls_test.get_top_k_back_mid_front_type_arrangements(k=16)
    for i, data in enumerate(list_best_arrangement):
        cls_test.print_one_arrangement(data)
    print(f"Execution time: {time.time() - start_time} seconds")