import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import logging

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


queue_data_filepath = 'sample-data/main/queue_data'
plot_data_filepath = 'sample-data/main/plot_data'

st.set_page_config(layout='wide')
# @st.cache_data(ttl=60)
# def load_queue_data(file_path):
#     df = pd.read_csv(file_path)
#     df.columns = df.columns.str.strip()
#     df.rename(columns={df.columns[0]: 'filename'}, inplace=True)
#     return df


def load_plot_data(file_path, skip_rows=0):
    start_time = time.time()
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    logger.info(
        f"load_plot_data,{time.time() - start_time},skip_rows={skip_rows}")
    return df


if st.button("Refresh") or 'plot_data' not in st.session_state:
    st.session_state.plot_data = load_plot_data(plot_data_filepath)
    st.session_state.plot_data_len = len(st.session_state.plot_data)


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_chart():
    start_time = time.time()
    new_data = load_plot_data(
        plot_data_filepath, skip_rows=st.session_state.plot_data_len)
    if not new_data.empty:
        st.session_state.plot_data = pd.concat(
            [st.session_state.plot_data, new_data], ignore_index=True)
    st.session_state.plot_data_len = len(st.session_state.plot_data)
    fig = px.line(
        st.session_state.plot_data,
        x='relative_time',
        y=['corpus_count', 'pending_total', 'pending_favs'],
        labels={'value': 'Count', 'variable': 'Metric',
                'relative_time': 'Time'},
        title="Queue Metrics Over Time",
        hover_data=['cur_item']
    )

    st.plotly_chart(fig, width='stretch')
    st.caption(
        f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")
    if st.checkbox('Show latest data'):
        st.dataframe(new_data.tail())
    logger.info(f"generate_chart,{time.time() - start_time}")


generate_chart()
