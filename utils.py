import pandas as pd
import os
from typing import *
import glob
import streamlit as st
from stqdm import stqdm
import logging
import time
from datetime import datetime


# logging configuration
logging.basicConfig(
    filename='logs/utils.log',
    level=logging.INFO,
    format='%(asctime)s,%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='a'
)
logger = logging.getLogger()


def load_fuzzer_stats(directory_path: str) -> pd.DataFrame:
    """
    Loads and combines fuzzer_stats files into a single DataFrame.

    Args:
        file_paths (List[str]): List of file paths to fuzzer_stats files.

    Returns:
        pd.DataFrame: DataFrame indexed by fuzzer name.
    """
    start_time = time.time()
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

    logger.info(f"load_fuzzer_stats,{time.time() - start_time}")
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
    start_time = time.time()
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    logger.info(f"load_plot_data,{time.time() - start_time}")
    return df


def load_queue_data(file_path: str, skip_rows: int = 0) -> pd.DataFrame:
    start_time = time.time()
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'filename'}, inplace=True)
    logger.info(f"load_queue_data,{time.time() - start_time}")
    return df


def update_session_fuzzer_stats(directory_path):
    start_time = time.time()
    st.session_state.fuzzer_stats = load_fuzzer_stats(directory_path)
    logger.info(f"update_session_fuzzer_stats,{time.time() - start_time}")


def update_session_plot_data(directory_path):
    start_time = time.time()
    for file_path in stqdm(glob.glob(os.path.join(directory_path, "*", "plot_data")), desc="Updating plot data"):
        base_name = os.path.basename(os.path.dirname(file_path))
        if base_name not in st.session_state or 'plot_data' not in st.session_state[base_name]:
            plot_data = load_plot_data(file_path)
            st.session_state[base_name] = {
                'plot_data': plot_data,
                'plot_data_len': len(plot_data)
            }

        else:
            existing_plot_data = st.session_state[base_name]['plot_data']
            existing_plot_data_len = st.session_state[base_name]['plot_data_len']
            new_plot_data = load_plot_data(
                file_path, skip_rows=existing_plot_data_len)

            if not new_plot_data.empty:
                updated_data = pd.concat(
                    [existing_plot_data, new_plot_data], ignore_index=True)

                st.session_state[base_name] = {
                    'plot_data': updated_data,
                    'plot_data_len': len(updated_data),
                    'new_plot_data': new_plot_data
                }
    logger.info(f"update_session_plot_data,{time.time() - start_time}")


def update_session_queue_data(directory_path):
    start_time = time.time()
    for file_path in stqdm(glob.glob(os.path.join(directory_path, "*", "queue_data")), desc="Updating queue data"):
        base_name = os.path.basename(os.path.dirname(file_path))
        if base_name not in st.session_state or 'queue_data' not in st.session_state[base_name]:
            queue_data = load_queue_data(file_path)
            st.session_state[base_name] = {
                'queue_data': queue_data,
                'queue_data_len': len(queue_data)
            }

        else:
            existing_queue_data = st.session_state[base_name]['queue_data']
            existing_queue_data_len = st.session_state[base_name]['queue_data_len']
            new_queue_data = load_queue_data(
                file_path, skip_rows=existing_queue_data_len)

            if not new_queue_data.empty:
                updated_data = pd.concat(
                    [existing_queue_data, new_queue_data], ignore_index=True)

                st.session_state[base_name] = {
                    'queue_data': updated_data,
                    'queue_data_len': len(updated_data),
                }

    logger.info(f"update_session_queue_data,{time.time() - start_time}")

def check_last_updated(update_interval):
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {update_interval}s)"