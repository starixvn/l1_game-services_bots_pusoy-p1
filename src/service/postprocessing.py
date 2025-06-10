from treys import Card

class PostProcessing:
    """
    This class is used to convert the algorithm's best arrangement to the output format.
    """
    def __init__(self, list_card_value, best_arrangement):
        """
        self.list_card_value: list, the input list of card value (from 0 to 51)
        self.best_arrangement: dict, the algorithm's best arrangement
                            or list[dict], the algorithm's best arrangement list
        """
        self.list_card_value = list_card_value
        self.best_arrangement = best_arrangement
    
    def postprocessing_hand(self, hand_cards) -> list:
        """
        This function is used to convert the list of hand cards to the list of hand values [rank * 4 + suit].
        Args:
            - hand_cards: list, the list of hand cards
        Returns:
            - list, the list of hand values = [rank * 4 + suit]
        """
        mapping_suit_char_to_value = {
            "s": 0,
            "h": 1,
            "c": 2,
            "d": 3
        }
        hand_output = []
        for card in hand_cards:
            rank = Card.get_rank_int(card)
            suit_char = Card.INT_SUIT_TO_CHAR_SUIT[Card.get_suit_int(card)]
            suit = mapping_suit_char_to_value[suit_char]
            hand_output.append(rank * 4 + suit)
        return hand_output

    def process_and_format_data_arrangement(self, data_arrangement) -> dict:
        return {
            "segment_1": self.postprocessing_hand(data_arrangement["back_card"]),
            "segment_2": self.postprocessing_hand(data_arrangement["mid_card"]),
            "segment_3": self.postprocessing_hand(data_arrangement["front_card"]),
        }

    def postprocessing_output(self) -> dict:
        """
        This function is used to convert the algorithm's best arrangement to the output format.
        Returns:
            - dict, the output format
        """
        if isinstance(self.best_arrangement, dict):
            arrangement_formatted = self.process_and_format_data_arrangement(self.best_arrangement)
        else:
            assert isinstance(self.best_arrangement, list)
            arrangement_formatted = [self.process_and_format_data_arrangement(arrangement) 
                                     for arrangement in self.best_arrangement]

        output = {
            "player_id": "string",
            "arrangement_id": "string",
            "input_hash": 0,
            "input": self.list_card_value,
            "output": arrangement_formatted
        }
        return output