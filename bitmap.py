import numpy as np
import streamlit as st
import plotly.express as px

st.header("Fuzz Bitmap Coverage Visualization")

with open('out/main/fuzz_bitmap', 'rb') as f:
    bits = np.unpackbits(np.frombuffer(f.read(), dtype=np.uint8))
size = int(np.ceil(np.sqrt(len(bits))))
img = np.zeros((size, size), dtype=np.uint8)
img.flat[:len(bits)] = bits

fig = px.imshow(
    img,
    color_continuous_scale='gray_r',
    aspect='equal',
    width=1000,
    height=1000,
    labels={'color': 'Coverage'},
)
fig.update_xaxes(showticklabels=False)
fig.update_yaxes(showticklabels=False)
fig.update_layout(coloraxis_showscale=False)

st.plotly_chart(fig)
