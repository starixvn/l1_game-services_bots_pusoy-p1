from treys import Card

class PreProcessing(object):
    """
    This class is used to preprocess the input data.
    """
    def __init__(self, list_card_value):
        """
        self.list_card_value: list, the list of card value (from 0 to 51)
        """
        self.list_card_value = list_card_value

    def preprocessing_input(self) -> list:
        """
        This function is used to convert the list of card value to the list of card input for the algorithm.
        Returns:
            - list, the list of card input for the algorithm
        """
        list_rank = [str(i) for i in range(2, 10)] + ["T", "J", "Q", "K", "A"]
        list_suit = ["s", "h", "c", "d"]

        list_input = [Card.new(f"{list_rank[elem // 4]}{list_suit[elem % 4]}") for elem in self.list_card_value]
        return list_input