import pandas as pd
import streamlit as st
from datetime import datetime
import os
import plotly.express as px
import glob

UPDATE_INTERVAL = 60
DATA_DIRECTORY = 'sample-data'
PLOT_DATA_FILEPATH = 'sample-data/main/plot_data'

st.set_page_config(
    layout="wide"
)


def load_fuzzer_stats(directory='out'):
    fuzzer_stats_dfs = {}
    backup_pattern = os.path.join(directory, "*", "fuzzer_stats")
    for fpath in glob.glob(backup_pattern):
        fname = os.path.basename(os.path.dirname(fpath))
        try:
            df = pd.read_csv(fpath, sep=':', header=None)
            df[0] = df[0].str.strip()
            df[1] = df[1].str.strip()
            df = df.set_index(0).T
            df.index = [fname]  # Set the index to the fuzzer name
            fuzzer_stats_dfs[fname] = df
        except Exception as e:
            st.warning(f"Could not load {fpath}: {e}")
    if fuzzer_stats_dfs:
        combined_fuzzer_stats_df = pd.concat(fuzzer_stats_dfs.values())
        run_time_sec = pd.to_numeric(
            combined_fuzzer_stats_df['run_time'], errors='coerce').fillna(0).astype(int)
        combined_fuzzer_stats_df['run_time'] = run_time_sec.apply(
            lambda x: f"{x//60}:{x % 60}")
        columns = [
            'run_time', 'execs_done', 'execs_per_sec', 'corpus_count',
            'edges_found', 'total_edges', 'bitmap_cvg', 'saved_crashes', 'saved_hangs',
            'max_depth', 'pending_total', 'stability'
        ]
        return combined_fuzzer_stats_df[columns]
    else:
        return None


def load_plot_data(file_path, skip_rows=0):
    if skip_rows > 0:
        df = pd.read_csv(file_path, skiprows=range(1, skip_rows + 1))
    else:
        df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    return df


if st.button("Refresh") or 'fuzzer_stats' or 'plot_data' not in st.session_state:
    st.session_state.fuzzer_stats = load_fuzzer_stats(DATA_DIRECTORY)
    st.session_state.plot_data = load_plot_data(PLOT_DATA_FILEPATH)
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
        PLOT_DATA_FILEPATH, skip_rows=st.session_state.plot_data_len)
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
    crash_hang_df = st.session_state.fuzzer_stats.reset_index()[['index', 'saved_crashes', 'saved_hangs']].copy()
    crash_hang_df['saved_crashes'] = pd.to_numeric(crash_hang_df['saved_crashes'], errors='coerce').fillna(0).astype(int)
    crash_hang_df['saved_hangs'] = pd.to_numeric(crash_hang_df['saved_hangs'], errors='coerce').fillna(0).astype(int)
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
