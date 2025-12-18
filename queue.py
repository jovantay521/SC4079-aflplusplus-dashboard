import streamlit as st
import pandas as pd
# import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import logging
import glob
import os
from utils import *

# logging configuration
logging.basicConfig(
    filename='queue.log',
    level=logging.INFO,
    format='%(asctime)s,%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='a'
)
logger = logging.getLogger()

UPDATE_INTERVAL = 60
DATA_DIRECTORY_PATH = 'sample-data'

st.set_page_config(layout='wide')


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_plot_data_chart():
    update_session_plot_data(DATA_DIRECTORY_PATH)
    update_session_fuzzer_stats(DATA_DIRECTORY_PATH)
    metrics = ['corpus_count', 'pending_total', 'pending_favs']
    metric_titles = {
        'corpus_count': 'Corpus Count Over Time',
        'pending_total': 'Pending Total Over Time',
        'pending_favs': 'Pending Favs Over Time'
    }
    cols = st.columns(3, border=True)
    for idx, metric in enumerate(metrics):
        fig = go.Figure()
        for file_path in glob.glob(os.path.join(DATA_DIRECTORY_PATH, "*", "plot_data")):
            base_name = os.path.basename(os.path.dirname(file_path))
            session_plot_data = st.session_state[base_name]['plot_data']
            fig.add_trace(go.Scatter(
                x=session_plot_data['relative_time'],
                y=session_plot_data[metric],
                name=base_name,
            ))
        fig.update_layout(title=metric_titles[metric])
        with cols[idx]:
            st.plotly_chart(fig)


generate_plot_data_chart()


def generate_queue_data_chart():
    update_session_fuzzer_stats(DATA_DIRECTORY_PATH)
    update_session_queue_data(DATA_DIRECTORY_PATH)
    queue_data_dfs = []
    for idx, row in st.session_state.fuzzer_stats.iterrows():
        cur_item = row['cur_item']
        queue_data = st.session_state[idx]['queue_data']
        regex_pattern = rf'id:0*{cur_item}\b'
        queue_data_df = queue_data[queue_data['filename'].str.contains(
            regex_pattern)]
        queue_data_df = queue_data_df.copy()
        queue_data_df.loc[:, 'fuzzer'] = idx
        queue_data_df = queue_data_df.set_index('fuzzer')
        # st.dataframe(queue_data_df)
        queue_data_dfs.append(queue_data_df)

    result = pd.concat(queue_data_dfs)
    st.title("Current queue")
    st.dataframe(result)


generate_queue_data_chart()

st.caption(
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")

if st.button("Refresh"):
    update_session_fuzzer_stats(DATA_DIRECTORY_PATH)
    update_session_queue_data(DATA_DIRECTORY_PATH)
    update_session_plot_data(DATA_DIRECTORY_PATH)
