import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

UPDATE_INTERVAL = 60 
LOG_FILE_PATH = 'logs/utils.log'

st.set_page_config(layout='wide')


def load_log_data(file_path, skip_rows=0):
    # Read only new rows, preserving the header
    df = pd.read_csv(file_path, skiprows=skip_rows, names=['asctime', 'function', 'elapsed'])
    df.columns = df.columns.str.strip()
    return df


def update_session_log_data(file_path):
    if 'log_data' not in st.session_state:
        log_data = load_log_data(file_path)
        st.session_state.log_data = log_data
        st.session_state.log_data_len = len(log_data)
    else:
        existing_log_data = st.session_state.log_data
        existing_log_data_len = st.session_state.log_data_len
        new_log_data = load_log_data(
            file_path, skip_rows=existing_log_data_len)

        if not new_log_data.empty:
            updated_data = pd.concat(
                [existing_log_data, new_log_data], ignore_index=True)

            st.session_state.log_data = updated_data
            st.session_state.log_data_len  = len(updated_data)
            st.session_state.new_log_data = new_log_data

@st.fragment(run_every=UPDATE_INTERVAL)
def generate_chart():
    update_session_log_data(LOG_FILE_PATH)

    fig = px.line(
        st.session_state.log_data,
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

generate_chart()

if 'new_log_data' in st.session_state:
    with st.expander("Show latest data"):
        st.dataframe(st.session_state.new_log_data)

if st.button("Refresh"):
    update_session_log_data(LOG_FILE_PATH)