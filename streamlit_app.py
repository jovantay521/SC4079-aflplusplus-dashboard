import os
import streamlit as st

debug_mode = os.environ.get("DEBUG") == "1"

development = st.Page("development.py", title="Development", default=True)
dashboard = st.Page("dashboard.py", title="Dashboard")
queue = st.Page("queue.py", title="Queue")
mutation_history = st.Page(
    "mutation_history.py", title="Mutation History")
crashes_hangs = st.Page("crashes_hangs.py", title="Crashes & Hangs")
debug = st.Page("debug.py", title="Debug")
# bitmap = st.Page("bitmap.py", title="Bitmap")
if debug_mode:
    print("[*] Debug mode")
    pg = st.navigation([dashboard, queue, mutation_history,
                       crashes_hangs, debug], position="top")
else:
    pg = st.navigation([development, dashboard, queue, mutation_history,
                       crashes_hangs], position="top")
pg.run()
