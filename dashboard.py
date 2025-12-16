import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import *
from utils import *

UPDATE_INTERVAL = 60
DATA_DIRECTORY_PATH = 'sample-data'

st.set_page_config(
    layout="wide"
)


if st.button("Refresh") or 'fuzzer_stats' or 'plot_data' not in st.session_state:
    st.session_state.fuzzer_stats = load_fuzzer_stats(DATA_DIRECTORY_PATH)
    for file_path in glob.glob(os.path.join(DATA_DIRECTORY_PATH, "*", "plot_data")):
        base_name = os.path.basename(os.path.dirname(file_path))
        plot_data = load_plot_data(file_path)
        st.session_state[base_name] = {
            'plot_data': plot_data,
            'plot_data_len': len(plot_data)
        }


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
    plot_data_fig = go.Figure()

    for file_path in glob.glob(os.path.join(DATA_DIRECTORY_PATH, "*", "plot_data")):
        base_name = os.path.basename(os.path.dirname(file_path))
        session_plot_data = st.session_state[base_name]['plot_data']
        session_plot_data_len = st.session_state[base_name]['plot_data_len']
        new_plot_data = load_plot_data(
            file_path, skip_rows=session_plot_data_len)
        print(new_plot_data.tail())
        if not new_plot_data.empty:
            updated_plot_data = pd.concat(
                [session_plot_data, new_plot_data], ignore_index=True),
            st.session_state[base_name] = {
                'plot_data': updated_plot_data,
                'plot_data_len': len(updated_plot_data)
            }

        plot_data_fig.add_trace(go.Scatter(
            x=session_plot_data['relative_time'],
            y=session_plot_data['edges_found'],
            # mode='lines'
            name=base_name
        ))

    st.plotly_chart(plot_data_fig)

    if st.checkbox('Show latest data'):
        st.dataframe(new_plot_data.tail())


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

    generate_chart()

with col2:
    generate_crash_hangs_bar()

st.caption(
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")
