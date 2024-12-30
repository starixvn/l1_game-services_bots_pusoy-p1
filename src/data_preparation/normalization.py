import numpy as np

class Normalization(object):
    def __init__(self):
        pass
    
    @staticmethod
    def check_range_value_of_a_series(column_series, min_value=0, max_value=1):
        assert (min_value <= column_series).all() and (column_series <= max_value).all(), \
            f"The range value of the column {column_series.name} is not correct"
        assert column_series.dtype in [np.int64, float], \
            f"The data type of the column {column_series.name} is not correct: {column_series.dtype}"

    @staticmethod
    def check_range_value_after_min_max_scale(dataset):
        for col_name in dataset.columns:
            if col_name in ["average_point"]:
                continue
            Normalization.check_range_value_of_a_series(dataset[col_name])

    @staticmethod
    def customize_min_max_scaler(column_series, min_value, max_value):
        return (column_series - min_value) / (max_value - min_value)

    @staticmethod
    def normalize_dataset(dataset):
        for col_name in ["back_rank", "mid_rank"]:
            dataset[col_name] = Normalization.customize_min_max_scaler(dataset[col_name], 1, 7462)
        dataset["front_rank"] = Normalization.customize_min_max_scaler(dataset["front_rank"], 1, 455)
        for col_name in ["back_suit_strength", "mid_suit_strength", "front_suit_strength"]:
            dataset[col_name] = Normalization.customize_min_max_scaler(dataset[col_name], 1, 4)

        for col_name in ["n_deuce", "n_trey", "n_four", "n_five", "n_six", "n_seven", 
                         "n_eight", "n_nine", "n_ten", "n_jack", "n_queen", "n_king", "n_ace"]:
            dataset[col_name] = Normalization.customize_min_max_scaler(dataset[col_name], 0, 4)
        for col_name in ["n_spade", "n_heart", "n_diamond", "n_club"]:
            dataset[col_name] = Normalization.customize_min_max_scaler(dataset[col_name], 0, 13)

        dataset["n_Royal_Flush"] = Normalization.customize_min_max_scaler(dataset["n_Royal_Flush"], 0, 4)
        dataset["n_Straight_Flush"] = Normalization.customize_min_max_scaler(dataset["n_Straight_Flush"], 0, 36)
        dataset["n_Flush"] = Normalization.customize_min_max_scaler(dataset["n_Flush"], 0, 5108)
        dataset["n_Straight"] = Normalization.customize_min_max_scaler(dataset["n_Straight"], 0, 10200)
        dataset["n_Dragon"] = Normalization.customize_min_max_scaler(dataset["n_Dragon"], 0, 1594323)
        dataset["n_Six_Pair"] = Normalization.customize_min_max_scaler(dataset["n_Six_Pair"], 1250964, 8033340)
        dataset["n_Three_Flush"] = Normalization.customize_min_max_scaler(dataset["n_Three_Flush"], 61818714, 1431593592)

        for col_name in ["back_proba", "mid_proba", "front_proba"]:
            dataset[col_name] /= 100.0

        Normalization.check_range_value_after_min_max_scale(dataset)