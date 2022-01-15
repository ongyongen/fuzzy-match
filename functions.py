import pandas as pd

from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def remove_entries_with_na(df, name_col):
    df = df[df[name_col].isna() == False].reset_index().drop(columns=['index'])
    return df

def standardize_cc_id(df, cc_id_col):
    df[cc_id_col] = list(map(lambda x: int(x), list(df[cc_id_col])))
    return df

def standardize_name(df, name_col, std_name_col):
    df[std_name_col] = list(map(lambda x: x.lower().translate(x.maketrans({'(':'',')':'',"'":''})), list(df[name_col])))
    return df

def match_by_cc_id_and_name(mapping_df,mapping_df_name_col, mapping_df_cc_id,base_df, base_df_cc_id,std_name_col,mapped_name_col):
    d_mapping_df = {}
    for i in range(len(mapping_df)):
        cc_id = mapping_df.loc[i,mapping_df_cc_id]
        std_name = mapping_df.loc[i,std_name_col]
        actual_name = mapping_df.loc[i,mapping_df_name_col]
        if cc_id not in d_mapping_df:
            d_mapping_df[cc_id] = [(std_name,actual_name)]
        else:
            d_mapping_df[cc_id] += [(std_name,actual_name)]

    base_df[mapping_df_cc_id] = 'NIL'
    base_df[mapped_name_col] = 'NIL'

    for i in range(len(base_df)):
        each_base_df_cc_id = base_df.loc[i,base_df_cc_id]
        base_df_name = base_df.loc[i,std_name_col]
        if each_base_df_cc_id in d_mapping_df:
            mapping_name_lst = d_mapping_df[each_base_df_cc_id]
            for mapping_name in mapping_name_lst:
                bool_lst_base_in_mapping = [base_name_substring in mapping_name[0].split(' ') for 
                                            base_name_substring in base_df_name.split(' ')]
                bool_lst_mapping_in_base = [mapping_name_substring in base_df_name.split(' ') for
                                            mapping_name_substring in mapping_name[0].split(' ')]
                if False not in bool_lst_base_in_mapping or False not in bool_lst_mapping_in_base:
                    base_df.loc[i,mapped_name_col] = mapping_name[1]
                    base_df.loc[i,mapping_df_cc_id] = each_base_df_cc_id 
                    break
    return base_df

def match_all_names_by_exact_substring(base_df, std_name_col, mapping_df, mapping_df_name_col,mapped_name_col):

    def match_each_name_by_exact_substring(base_df_name):
        mapping_df_name_split = list(map(lambda x: x.split(' '), list(mapping_df[std_name_col])))
        match_lst = list(map(lambda x: [i in x for i in base_df_name.split(' ')], mapping_df_name_split))
        match_lst_bool = list(map(lambda x: False not in x, match_lst))
        if True in match_lst_bool:
            return list(mapping_df[mapping_df_name_col])[match_lst_bool.index(True)]
        else:
            return 'NIL'

    base_df[mapped_name_col] = list(map(lambda x,y: match_each_name_by_exact_substring(x) if y == 'NIL' else y,
                                        list(base_df[std_name_col]), list(base_df[mapped_name_col])))
    return base_df

def match_name_by_exact_alphabets(base_df, mapping_df, mapping_df_name_col, std_name_col, mapped_name_col):
    base_df_names = list(map(lambda x:''.join(sorted(x)).replace(' ',''), list(base_df[std_name_col])))
    mapping_df_names = list(map(lambda x:''.join(sorted(x)).replace(' ',''), list(mapping_df[std_name_col])))
    matching_name_index = list(map(lambda x: mapping_df_names.index(x) if x in mapping_df_names else 'NIL', base_df_names))
    matching_name = list(map(lambda x: list(mapping_df[mapping_df_name_col])[x] if x != 'NIL' else x, matching_name_index))
    base_df[mapped_name_col] = list(map(lambda x,y: x if y == 'NIL' else y, matching_name, list(base_df[mapped_name_col])))
    return base_df

def check_occurence_of_base_df_name_substring_across_entire_mapping_df(base_df, mapping_df, std_name_col, mapping_check_col_name):
    bag_of_words = [x for name in list(map(lambda x: x.split(' '), list(mapping_df[std_name_col]))) for x in name]
    check_lst = list(map(lambda x: [i in bag_of_words for i in x.split(' ')], list(base_df[std_name_col])))
    check_lst_bool = list(map(lambda x: True not in x, check_lst))
    base_df[mapping_check_col_name] = list(map(lambda x: 'Most likely missing match' if x == True else '', check_lst_bool))
    return base_df

def check_for_spelling_error_mismatches(base_df, mapping_check_col_name, mapped_name_col):
    base_df[mapping_check_col_name] = list(map(lambda x,y: 'Possible spelling error mismatch' 
                                    if len(x) == 0 and y == 'NIL' else x,
                                    list(base_df[mapping_check_col_name]), list(base_df[mapped_name_col])))
    return base_df



def match_all_entries_by_fuzz_tsr(base_df, mapping_df, std_name_col, mapped_name_col, mapping_sim_score_name,mapping_df_name_col):

    def match_each_entry_by_fuzz_tsr(base_df_name):
        mapping_df_names_tsr = list(mapping_df[std_name_col])
        score_lst = list(map(lambda x: fuzz.token_sort_ratio(x, base_df_name), mapping_df_names_tsr))
        max_score = max(score_lst)
        max_score_index = score_lst.index(max_score)
        match = list(mapping_df[mapping_df_name_col])[max_score_index]
        return match

    base_df[mapped_name_col] = list(map(lambda x,y: match_each_entry_by_fuzz_tsr(x) if y == 'NIL' else y,
                                        list(base_df[std_name_col]), list(base_df[mapped_name_col])))
    base_df[mapping_sim_score_name] = list(map(lambda x,y: fuzz.token_sort_ratio(x,y),
                                    list(base_df[std_name_col]), list(base_df[mapped_name_col])))

    return base_df

def map_all_data(base_df, mapping_df,mapping_df_name_col,mapped_name_col,mapping_df_cc_id,mapping_df_name):
    index_lst = list(map(lambda x: list(mapping_df[mapping_df_name_col]).index(x), list(base_df[mapped_name_col])))
    mapping_df_col = list(mapping_df.columns) 
    for col in mapping_df_col:
        if col != mapping_df_cc_id:
            base_df[f"{col} ({mapping_df_name})"] = list(map(lambda x: list(mapping_df[col])[x], index_lst))
        else:
            mapping_cc_id_lst = list(map(lambda x: list(mapping_df[mapping_df_cc_id])[x], index_lst))
            base_df[f"{col} ({mapping_df_name})"] = list(map(lambda x,y: x if y == 'NIL' else y,
                                                            mapping_cc_id_lst, list(base_df[mapping_df_cc_id])))
            base_df = base_df.drop(columns=[mapping_df_cc_id])

    return base_df

def check_match_based_on_cost_center(base_df,base_df_cc_id, mapping_df_cc_id,mapping_check_cc_name, mapping_df_name):
    base_df[mapping_check_cc_name] = list(map(lambda x,y: x == y, 
                                            list(base_df[f"{mapping_df_cc_id} ({mapping_df_name})"]), 
                                            list(base_df[base_df_cc_id])))
    return base_df

def fuzzy_match(base_df, mapping_df):
    base_df = remove_entries_with_na(base_df, base_df_name_col)
    mapping_df = remove_entries_with_na(mapping_df, mapping_df_name_col)

    base_df = standardize_name(base_df, base_df_name_col, std_name_col)
    mapping_df = standardize_name(mapping_df, mapping_df_name_col, std_name_col)

    base_df = standardize_cc_id(base_df,base_df_cc_id)
    mapping_df = standardize_cc_id(mapping_df,mapping_df_cc_id)

    base_df = match_by_cc_id_and_name(mapping_df,mapping_df_name_col, mapping_df_cc_id,base_df,
                                    base_df_cc_id,std_name_col,mapped_name_col)

    base_df = match_all_names_by_exact_substring(base_df, std_name_col,mapping_df, mapping_df_name_col)

    base_df = match_name_by_exact_alphabets(base_df, mapping_df,mapping_df_name_col, std_name_col,mapped_name_col)

    base_df = check_occurence_of_base_df_name_substring_across_entire_mapping_df(base_df, mapping_df, std_name_col, mapping_check_col_name)

    base_df = check_for_spelling_error_mismatches(base_df, mapping_check_col_name,mapped_name_col)

    base_df = match_all_entries_by_fuzz_tsr(base_df, mapping_df, std_name_col, mapped_name_col, mapping_sim_score_name)

    base_df = map_all_data(base_df, mapping_df,mapping_df_name_col,mapped_name_col,mapping_df_name)

    base_df = check_match_based_on_cost_center(base_df,base_df_cc_id, mapping_df_cc_id,mapping_check_cc_name, mapping_df_name)
    return base_df

