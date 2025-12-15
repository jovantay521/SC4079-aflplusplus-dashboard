import pandas as pd
import os
from typing import *
import glob


def get_file_paths(directory_path: str, file_name: str) -> List[str]:
    """
    Returns a list of file paths matching the specified file name within all subdirectories of the given directory.

    Args:
        directory_path (str): The path to the parent directory to search within.
        file_name (str): The name of the file to search for in each subdirectory.

    Returns:
        List[str]: A list of full file paths that match the specified file name within the subdirectories.

    Example:
        get_file_paths("home/user/sample-data", "fuzzer_stats")
        Returns: ['sample-data/compcov/fuzzer_stats', 'sample-data/asan/fuzzer_stats', 'sample-data/main/fuzzer_stats', 'sample-data/ubsan/fuzzer_stats', 'sample-data/cmplog/fuzzer_stats']
    """
    file_paths = glob.glob(os.path.join(directory_path, "*", file_name))
    return file_paths


def load_fuzzer_stats(file_paths: List[str]) -> pd.DataFrame:
    """
    Loads and combines fuzzer_stats files into a single DataFrame.

    Args:
        file_paths (List[str]): List of file paths to fuzzer_stats files.

    Returns:
        pd.DataFrame: DataFrame indexed by fuzzer name.
    """
    fuzzer_stats_dfs = {}

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
