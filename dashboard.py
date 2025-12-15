import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import *
from utils import *

UPDATE_INTERVAL = 60
DATA_DIRECTORY_PATH = 'sample-data'
FUZZER_STATS_FILE_NAME = 'fuzzer_stats'
PLOT_DATA_file_path = 'sample-data/main/plot_data'

st.set_page_config(
    layout="wide"
)


# TODO: return a list of dataframes based on given DATA_DIRECTORY_PATH and PLOT_DATA_FILE_NAME
def load_plot_data(file_path, skip_rows=0):
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    return df



if st.button("Refresh") or 'fuzzer_stats' or 'plot_data' not in st.session_state:
    st.session_state.fuzzer_stats = load_fuzzer_stats(
        get_file_paths(DATA_DIRECTORY_PATH, FUZZER_STATS_FILE_NAME))
    st.session_state.plot_data = load_plot_data(PLOT_DATA_file_path)
    st.session_state.plot_data_len = len(st.session_state.plot_data)


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_progress_bar():
    st.write("Code Coverage")
    for idx, row in st.session_state.fuzzer_stats.iterrows():
        edges_found = pd.to_numeric(row['edges_found'])
        total_edges = pd.to_numeric(row['total_edges'])
        percentage = (edges_found / total_edges) * 100 if total_edges else 0
        st.progress(
            percentage / 100,
            text=f"**{idx}**: {percentage:.2f}% ({edges_found} / {total_edges})"
        )


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_chart():
    new_data = load_plot_data(
        PLOT_DATA_file_path, skip_rows=st.session_state.plot_data_len)
    if not new_data.empty:
        st.session_state.plot_data = pd.concat(
            [st.session_state.plot_data, new_data], ignore_index=True)
    st.session_state.plot_data_len = len(st.session_state.plot_data)
    fig = px.line(
        st.session_state.plot_data,
        x='relative_time',
        y='edges_found',
        # title="Queue Metrics Over Time",
        # hover_data=['cur_item']
    )

    st.plotly_chart(fig, width='stretch')
    if st.checkbox('Show latest data'):
        st.dataframe(new_data.tail())


@st.fragment(run_every=UPDATE_INTERVAL)
def generate_crash_hangs_bar():
    # Show crashes and hangs per fuzzer
    st.write("Crashes and Hangs Per Fuzzer")
    # Prepare data for bar chart
    crash_hang_df = st.session_state.fuzzer_stats.reset_index(
    )[['index', 'saved_crashes', 'saved_hangs']].copy()
    crash_hang_df['saved_crashes'] = pd.to_numeric(
        crash_hang_df['saved_crashes'], errors='coerce').fillna(0).astype(int)
    crash_hang_df['saved_hangs'] = pd.to_numeric(
        crash_hang_df['saved_hangs'], errors='coerce').fillna(0).astype(int)
    crash_hang_df = crash_hang_df.melt(id_vars='index', value_vars=['saved_crashes', 'saved_hangs'],
                                       var_name='Type', value_name='Count')

    bar_fig = px.bar(
        crash_hang_df,
        x='index',
        y='Count',
        color='Type',
        labels={'index': 'Fuzzer', 'Count': 'Count', 'Type': 'Type'},
        title="Saved Crashes and Hangs Per Fuzzer",
        height=400
    )
    bar_fig.update_layout(
        barmode='group',
        margin=dict(t=40, b=20, l=20, r=20)
    )

    st.plotly_chart(bar_fig, width='stretch')


generate_progress_bar()

col1, col2 = st.columns(2, border=True)

with col1:
    plot_data_fig = go.Figure()
    for filepath in get_file_paths(DATA_DIRECTORY_PATH, 'plot_data'):
        plot_data_df = load_plot_data(filepath)
        base_name = os.path.basename(os.path.dirname(filepath))
        # plot_data_df['fuzzer'] = base_name
        # print(plot_data_df.tail())
        plot_data_fig.add_trace(go.Scatter(
            x=plot_data_df['relative_time'],
            y=plot_data_df['edges_found'],
            # mode='lines'
            name=base_name
        ))

    st.plotly_chart(plot_data_fig)

    # generate_chart()

with col2:
    generate_crash_hangs_bar()

st.caption(
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")
