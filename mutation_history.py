import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(layout='wide')

UPDATE_INTERVAL = 60

rows = []
with open('sample-data/main/introspection.txt') as f:
    for line in f:
        line = line.strip()
        if not line.startswith("QUEUE "):
            continue
        # Remove "QUEUE " prefix
        line = line[len("QUEUE "):]
        # print('line:', line)
        # Split at the first '='
        if '=' in line:
            left, right = line.split('=', 1)
            left = left.strip()
            right = right.strip()
            # print('left:', left)
            # print('right:', right)
            # Split left at the first space to get mutation history
            if ' ' in left:
                orig_info, mutation = left.split(' ', 1)
            else:
                orig_info, mutation = left, ''
            # print('orig info:', orig_info)
            # print('mutation:', mutation)
            rows.append({
                'original': orig_info,
                'mutation': mutation,
                'result': right
            })

    df = pd.DataFrame(rows)

    return df

df = load_mutation_history()
selected_result = st.selectbox(
    "Select resulting file to view mutation history:",
    df['result']
)

selected_row = df[df['result'] == selected_result].iloc[0]

st.divider()

st.subheader('Original Seed')
st.code(selected_row['original'], language=None)

st.subheader('Resulting Seed')
st.code(selected_row['result'], language=None)

st.subheader('Mutation History')
st.json(selected_row['mutation'])

load_mutation_history()

st.caption(
    f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")