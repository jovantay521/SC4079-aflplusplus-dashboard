import pandas as pd
import streamlit as st
import glob
import os
import plotly.graph_objects as go
from utils import *

DATA_DIRECTORY_PATH = 'sample-data'

st.set_page_config(
    layout="wide"
)

df = pd.read_csv("sample-data/main/plot_data")
df.columns = df.columns.str.strip()
df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)

# Add 'hour' column based on 'relative_time'
df['hour'] = (df['relative_time'] // 3600).astype(int)

# Aggregate only the desired columns, but retain all original columns for reference
agg_df = df.groupby('hour').agg({
    'total_execs': 'sum',
    'saved_crashes': 'sum',
    'execs_per_sec': 'mean'
}).reset_index()
agg_df['relative_time'] = agg_df['hour'] * 3600
# Reference last hour info
if agg_df.iloc[-1]['execs_per_sec'] < 500:
    st.warning("Low execution speed in past hour, refer to https://aflplus.plus/docs/best_practices/#improving-speed")

total_execs_fig = go.Figure()
total_execs_fig.add_trace(go.Scatter(
    x=df['relative_time'] / 60,
    y=df['total_execs'],
    # mode='lines+markers'
))

total_execs_fig.update_layout(title='total_execs')
st.plotly_chart(total_execs_fig)

saved_crashes_fig = go.Figure()
saved_crashes_fig.add_trace(go.Scatter(
    x=df['relative_time'],
    y=df['saved_crashes']
))

saved_crashes_fig.update_layout(title='saved_crashes')
st.plotly_chart(saved_crashes_fig)

execs_per_sec_fig = go.Figure()
execs_per_sec_fig.add_trace(go.Scatter(
    x=df['relative_time'],
    y=df['execs_per_sec']
))

execs_per_sec_fig.update_layout(title='execs_per_sec')
st.plotly_chart(execs_per_sec_fig)

# st.dataframe(df)

fuzzer_stats = pd.read_csv("out/main/fuzzer_stats", sep=':', header=None)

# Clean and transpose the key-value pairs so each fuzzer's stats is a row
fuzzer_stats[0] = fuzzer_stats[0].str.strip()
fuzzer_stats[1] = fuzzer_stats[1].str.strip()
fuzzer_stats = fuzzer_stats.set_index(0).T
st.dataframe(fuzzer_stats)

run_time = int(fuzzer_stats['run_time'].values[0])
time_wo_finds = int(fuzzer_stats['time_wo_finds'].values[0])
run_time = 700
time_wo_finds = 650
if 800 > run_time > 600 and time_wo_finds > 600:
    st.warning("No new paths found within the first 10 minutes. Check if the target binary is invoked correctly, memory limits, or input file validity.")