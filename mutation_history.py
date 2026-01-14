import streamlit as st
import pandas as pd
import re

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

selected_result = st.selectbox(
    "Select resulting file to view mutation history:",
    df['result']
)

selected_row = df[df['result'] == selected_result].iloc[0]
st.write('original seed')
st.code(selected_row['original'], language=None)
st.write('mutation history')
st.code(selected_row['mutation'], language=None)
st.write('resulting seed')
st.code(selected_row['result'], language=None)

st.caption("Under construction")
