import pandas as pd
import os
from typing import *
import glob


def load_fuzzer_stats(directory_path: str) -> pd.DataFrame:
    """
    Loads and combines fuzzer_stats files into a single DataFrame.

    Args:
        file_paths (List[str]): List of file paths to fuzzer_stats files.

    Returns:
        pd.DataFrame: DataFrame indexed by fuzzer name.
    """
    fuzzer_stats_dfs = {}

    file_paths = glob.glob(os.path.join(directory_path, "*", "fuzzer_stats"))

    for file_path in file_paths:
        directory_name = os.path.dirname(file_path)
        # fuzzer name e.g. main, asan, bsan
        base_name = os.path.basename(directory_name)
        df = pd.read_csv(file_path, sep=':', header=None)

        # Clean and transpose the key-value pairs so each fuzzer's stats is a row
        df[0] = df[0].str.strip()
        df[1] = df[1].str.strip()
        df = df.set_index(0).T
        df.index = [base_name]
        fuzzer_stats_dfs[base_name] = df

    combined_fuzzer_stats_df = pd.concat(fuzzer_stats_dfs.values())
    run_time_sec = pd.to_numeric(
        combined_fuzzer_stats_df['run_time'], errors='coerce').fillna(0).astype(int)
    combined_fuzzer_stats_df['run_time'] = run_time_sec.apply(
        lambda x: f"{x//60}:{x % 60}")

    return combined_fuzzer_stats_df

# Currently not in use. Refer to commit 7186c0f157a33a72c8aab2bd514ef7ef4910c876.
# def load_plot_data(directory_path: str, skip_rows: int = 0) -> Dict:
#     plot_data_dfs = {}
#     file_paths = glob.glob(os.path.join(directory_path, "*", "plot_data"))

#     for file_path in file_paths:
#         base_name = os.path.basename(os.path.dirname(file_path))

#         # only read new rows not previously stored in session state
#         if skip_rows > 0:
#             df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
#         else:
#             df = pd.read_csv(file_path)

#         df.columns = df.columns.str.strip()
#         df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
#         plot_data_dfs[base_name] = df
    
#     return plot_data_dfs


def load_plot_data(file_path: str, skip_rows: int = 0) -> pd.DataFrame:
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    return df
