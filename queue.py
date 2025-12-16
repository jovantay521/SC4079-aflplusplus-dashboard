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


if st.button("Refresh") or 'plot_data' not in st.session_state:
    for file_path in glob.glob(os.path.join(DATA_DIRECTORY_PATH, "*", "plot_data")):
        base_name = os.path.basename(os.path.dirname(file_path))
        plot_data = load_plot_data(file_path)
        st.session_state[base_name] = {
            'plot_data': plot_data,
            'plot_data_len': len(plot_data)
        }


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_chart():
    # update session plot data
    for file_path in glob.glob(os.path.join(DATA_DIRECTORY_PATH, "*", "plot_data")):
        base_name = os.path.basename(os.path.dirname(file_path))
        session_plot_data = st.session_state[base_name]['plot_data']
        session_plot_data_len = st.session_state[base_name]['plot_data_len']
        new_plot_data = load_plot_data(
            file_path, skip_rows=session_plot_data_len)
        if not new_plot_data.empty:
            updated_plot_data = pd.concat(
                [session_plot_data, new_plot_data], ignore_index=True)
            st.session_state[base_name] = {
                'plot_data': updated_plot_data,
                'plot_data_len': len(updated_plot_data)
            }
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


generate_chart()

st.caption(
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")