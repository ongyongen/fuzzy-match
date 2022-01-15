import uuid
import pandas as pd

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox 

import functions
from functions import *

class FuzzyMatch:

    def __init__(self, root, **args):
        
        self.base = None
        self.mapping = None
        
        self.base_file_name = None
        self.mapping_file_name = None
        
        self.base_name = None
        self.mapping_name = None
        
        self.base_cc_id = None
        self.mapping_cc_id = None
        
        self.base_name_options = ['Nil']
        self.base_cc_id_options = ['Nil']
        
        self.mapping_name_options = ['Nil']
        self.mapping_cc_id_options = ['Nil']

        self.generate_template()

    def generate_template(self):
        root.title("Fuzzy Match") 
        root.geometry("700x200")
        
        name_label = Label(root, text="Name Col")
        name_label.grid(row=1, column=4)
        
        cc_id_label = Label(root, text="CC ID Col")
        cc_id_label.grid(row=1, column=5)
        
        base_label = Label(root, text="Base File")
        base_label.grid(row=2, column=1)
        
        mapping_label = Label(root, text="Mapping File")
        mapping_label.grid(row=3, column=1)
    
        base_button = Button(root, text ="Upload", command=self.import_base_csv)
        base_button.grid(row=2, column=2)
        
        mapping_button = Button(root, text ="Upload", command=self.import_mapping_csv)
        mapping_button.grid(row=3, column=2)

        base_name_box = ttk.Combobox(root, values = self.base_name_options)
        base_name_box.grid(row=2, column=4)

        base_cc_id_box = ttk.Combobox(root, values = self.base_cc_id_options)
        base_cc_id_box.grid(row=2, column=5)

        mapping_name_box = ttk.Combobox(root, values = self.mapping_name_options)
        mapping_name_box.grid(row=3, column=4)

        mapping_cc_id_box = ttk.Combobox(root, values = self.mapping_cc_id_options)
        mapping_cc_id_box.grid(row=3, column=5)

        fuzzy_match_button = Button(root, text ="Start Fuzzy Matching", command=self.fuzzy_match_base_mapping)
        fuzzy_match_button.grid(row=4, column=5)


    def import_base_csv(self):
        
        base_path = askopenfilename()
        self.base = pd.read_csv(base_path)
        
        self.base_file_name = base_path.split('/')[-1].split('.')[0]
        base_file_name_label = Label(root, text=self.base_file_name)
        base_file_name_label.grid(row=2,column=3)
        
        base_name_options_lst = list(self.base.columns)
        self.base_name_options = ttk.Combobox(root, values = base_name_options_lst)
        self.base_name_options.grid(row=2, column=4)
        self.base_name_options.current(0)
        
        base_cc_id_options_lst = list(self.base.columns)
        self.base_cc_id_options = ttk.Combobox(root, values = base_cc_id_options_lst)
        self.base_cc_id_options.grid(row=2, column=5)
        self.base_cc_id_options.current(0)
    
        
    def import_mapping_csv(self):
        
        mapping_path = askopenfilename()
        self.mapping = pd.read_csv(mapping_path)

        self.mapping_file_name = mapping_path.split('/')[-1].split('.')[0]
        mapping_file_name_label = Label(root, text=self.mapping_file_name)
        mapping_file_name_label.grid(row=3,column=3)
        
        mapping_name_options_lst = list(self.mapping.columns)
        self.mapping_name_options = ttk.Combobox(root, values = mapping_name_options_lst)
        self.mapping_name_options.grid(row=3, column=4)
        self.mapping_name_options.current(0)
        
        mapping_cc_id_options_lst = list(self.mapping.columns)
        self.mapping_cc_id_options = ttk.Combobox(root, values = mapping_cc_id_options_lst)
        self.mapping_cc_id_options.grid(row=3, column=5)
        self.mapping_cc_id_options.current(0)
        
        
    def fuzzy_match_base_mapping(self):    

        #Names to set
        std_name_col = 'name_std'
        mapped_name_col = 'name_mapped'
        mapping_sim_score_name = 'sim_score_name'
        mapping_check_col_name = 'Missing matches?'
        mapping_check_cc_name = 'check_cost_center'

        # Parameters to change
        base_df = self.base
        mapping_df = self.mapping

        base_df_name_col = self.base_name_options.get()
        mapping_df_name_col = self.mapping_name_options.get()

        base_df_cc_id = self.base_cc_id_options.get()
        mapping_df_cc_id = self.mapping_cc_id_options.get()

        base_df_name = self.base_file_name
        mapping_df_name = self.mapping_file_name

        base_df = remove_entries_with_na(base_df, base_df_name_col)
        mapping_df = remove_entries_with_na(mapping_df, mapping_df_name_col)

        base_df = standardize_name(base_df, base_df_name_col, std_name_col)
        mapping_df = standardize_name(mapping_df, mapping_df_name_col, std_name_col)

        base_df = standardize_cc_id(base_df,base_df_cc_id)
        mapping_df = standardize_cc_id(mapping_df,mapping_df_cc_id)

        base_df = match_by_cc_id_and_name(mapping_df,mapping_df_name_col, mapping_df_cc_id,base_df,
                                        base_df_cc_id,std_name_col,mapped_name_col)

        base_df = match_all_names_by_exact_substring(base_df, std_name_col,mapping_df, mapping_df_name_col,mapped_name_col)

        base_df = match_name_by_exact_alphabets(base_df, mapping_df,mapping_df_name_col, std_name_col,mapped_name_col)

        base_df = check_occurence_of_base_df_name_substring_across_entire_mapping_df(base_df, mapping_df, std_name_col, mapping_check_col_name)

        base_df = check_for_spelling_error_mismatches(base_df, mapping_check_col_name,mapped_name_col)

        base_df = match_all_entries_by_fuzz_tsr(base_df, mapping_df, std_name_col, mapped_name_col, mapping_sim_score_name,mapping_df_name_col)

        base_df = map_all_data(base_df, mapping_df,mapping_df_name_col,mapped_name_col,mapping_df_cc_id,mapping_df_name)

        base_df = check_match_based_on_cost_center(base_df,base_df_cc_id, mapping_df_cc_id,mapping_check_cc_name, mapping_df_name)
        
        downloaded_file_name = f"{str(uuid.uuid4())}.csv"
        base_df.to_csv(downloaded_file_name)

        messagebox.showinfo("",f"{downloaded_file_name} has been downloaded to your computer") 

        
        
root = Tk()
FuzzyMatch(root)
root.mainloop()
