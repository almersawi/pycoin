class Helper:

    @staticmethod
    def get_dict_from_block(block):
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [el.__dict__.copy() for el in dict_block['transactions']]
        return dict_block