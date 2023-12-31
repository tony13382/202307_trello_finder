import numpy as np

def convert_to_np_array(lst):
    # 檢查 lst 是否為 None 或為具有值的列表
    if lst is None:
        return np.zeros(768)
    elif isinstance(lst, list):
        return np.array(lst)
    else:
        return np.zeros(768)


#####################
# Request Variables
# -------------------
# set : list of dict
#   - weight : float
#   - array : np.array
# len_array : int (length of array)
#####################
def calc_array_mean(set, len_array):
    # Define weight that need to sum
    sum_weight = 0
    # Define sum_array to sum all array
    sum_array = np.zeros(len_array)
    for item in set:
        item['array'] = convert_to_np_array(item['array'])
        # Check Array is empty
        if(item["array"].sum() == 0):
            # No calculate this weight
            sum_weight += 0
        else:
            # Calculate this weight
            sum_weight += item['weight']
            # Add to sum_array
            sum_array += item['array'] * item['weight']

    return sum_array / sum_weight