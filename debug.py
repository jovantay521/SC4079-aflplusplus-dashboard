import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

UPDATE_INTERVAL = 60 
queue_performance_filepath = 'queue.log'

st.set_page_config(layout='wide')

def load_queue_performance(file_path):
    df = pd.read_csv(file_path, names=['asctime', 'function', 'elapsed'])
    df.columns = df.columns.str.strip()
    return df


def load_new_rows(file_path, queue_performance_len):
    # Read only new rows, preserving the header
    df = pd.read_csv(file_path, skiprows=queue_performance_len, names=['asctime', 'function', 'elapsed'])
    df.columns = df.columns.str.strip()
    return df


if st.button("Refresh") or 'queue_performance' not in st.session_state:
    st.session_state.queue_performance = load_queue_performance(
        queue_performance_filepath)
    st.session_state.queue_performance_len = len(
        st.session_state.queue_performance)


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_chart():
    new_data = load_new_rows(
        queue_performance_filepath, st.session_state.queue_performance_len)
    if not new_data.empty:
        st.session_state.queue_performance = pd.concat(
            [st.session_state.queue_performance, new_data], ignore_index=True)
    st.session_state.queue_performance_len = len(
        st.session_state.queue_performance)

    fig = px.line(
        st.session_state.queue_performance,
        x='asctime',
        y='elapsed',
        color='function',  # Different color for each function
        title="Performance by Function",
        labels={'elapsed': 'Elapsed Time',
                'asctime': 'Timestamp', 'function': 'Function'}
    )
    st.plotly_chart(fig)
    st.caption(
        f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")

    if st.checkbox('Show latest data'):
        st.dataframe(new_data.tail())

generate_chart()
