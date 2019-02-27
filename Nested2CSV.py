import pandas as pd


class Nested2CSV:

    def __init__(self, data):
        self.data = data

    @staticmethod
    def __norm_dict(data_dict):
        d = {}
        for k, v in data_dict.items():
            if type(v) is str:
                d[k] = v
        return d

    @staticmethod
    def __has_nested_levels(d):
        for v in d.values():
            if type(v) is list:
                return True
        return False

    @staticmethod
    def __collect_recursive(data, row={}, result=[]):
        if type(data) is list:
            for i in data:
                if type(i) is dict:
                    row.update(Nested2CSV.__norm_dict(i))  # collect all non-list entries in dict at this level
                    if not Nested2CSV.__has_nested_levels(i):
                        result.append(row.copy())
                    for k, v in i.items():
                        Nested2CSV.__collect_recursive(v, row, result)

        return result

    def to_csv(self, filename):
        data_list = self.__collect_recursive(self.data)
        df = pd.DataFrame(data_list, columns=data_list[0].keys())
        df.to_csv(filename, encoding='utf-8', index=False)

        # pd.set_option('display.max_rows', 500)
        # pd.set_option('display.max_columns', 500)
        # pd.set_option('display.width', 1000)
        # print(df)
