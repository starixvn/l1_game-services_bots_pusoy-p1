import pickle
from treys import Card, Evaluator
from treys.lookup import LookupTable


with open("src/res/front_lookup.p", 'rb') as file:
    FRONT_LOOKUP = pickle.load(file)


class ChinesePokerEvaluator(Evaluator):
    """
    This class is used to evaluate the rank of the combo.
    ChinesePokerEvaluator class extended to score an Front cards.
    """
    def __init__(self):
        self.table = LookupTable()

        self.hand_size_map = {
            3: self._three,
            5: self._five,
            6: self._six,
            7: self._seven
        }

    def get_rank_class_front_hand(self, hr):
        """
        Returns the class of front hand given the hand hand_rank returned from evaluate.
        Can only be THREE_OF_A_KIND (rank class: 6), 
                    PAIR (rank class: 8), or
                    HIGH_CARD (rank class: 9)
        """
        if hr >= LookupTable.MAX_STRAIGHT and hr <= LookupTable.MAX_THREE_OF_A_KIND + 1:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_THREE_OF_A_KIND]
        elif hr >= LookupTable.MAX_TWO_PAIR and hr < LookupTable.MAX_PAIR + 1:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_PAIR]
        elif hr >= LookupTable.MAX_PAIR + 1 and hr < LookupTable.MAX_HIGH_CARD + 1:
            return LookupTable.MAX_TO_RANK_CLASS[LookupTable.MAX_HIGH_CARD]
        else:
            raise Exception("Invalid rank for front hand, cannot return rank class")

    def _three(self, cards):
        prime = Card.prime_product_from_hand(cards)
        return FRONT_LOOKUP[prime]

if __name__ == "__main__":
    evaluator = ChinesePokerEvaluator()