import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

UPDATE_INTERVAL = 60

st.set_page_config(
    layout="wide"
)
# st.checkbox("Show all stats")
# st.caption(
#     f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Update interval: {UPDATE_INTERVAL}s)")


@st.fragment(run_every=UPDATE_INTERVAL)
def load_plot_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'relative_time'}, inplace=True)
    return df


@st.fragment(run_every=UPDATE_INTERVAL)
def load_queue_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: 'filename'}, inplace=True)
    return df


@st.fragment(run_every=UPDATE_INTERVAL)
def load_introspection(file_path):
    rows = []
    with open(file_path) as f:
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


@st.fragment(run_every=UPDATE_INTERVAL)
def load_fuzzer_stats(file_path):
    df = pd.read_csv(file_path, sep=':', header=None)
    df[0] = df[0].str.strip()
    df[1] = df[1].str.strip()
    df = df.set_index(0).T

    return df


fuzzer_stats = load_fuzzer_stats('sample-data/main/fuzzer_stats')
plot_data = load_plot_data('sample-data/main/plot_data')
queue_data = load_queue_data('out/main/queue_data')
introspection = load_introspection('out/main/introspection.txt')
# st.dataframe(plot_data)
# st.dataframe(fuzzer_stats)
# st.dataframe(introspection)
# st.dataframe(queue_data)

cycles_done = int(fuzzer_stats['cycles_done'].iloc[0])
cycles_without_find = int(fuzzer_stats['cycles_wo_finds'].iloc[0])
pending_total = int(fuzzer_stats['pending_total'].iloc[0])
minutes_without_find = int(fuzzer_stats['time_wo_finds'].iloc[0]) / 60
last_find_time = int(fuzzer_stats['last_find'].iloc[0])
latest_time = plot_data['relative_time'].max()
past_hour = plot_data[plot_data['relative_time'] >= latest_time - 3600]
avg_execs_per_sec = past_hour['execs_per_sec'].mean()
stability_str = fuzzer_stats['stability'].iloc[0]
stability = float(fuzzer_stats['stability'].iloc[0].strip('%'))
var_byte_count = int(fuzzer_stats['var_byte_count'].iloc[0])

# If first cycle is not completed, info will be triggered.
# Reference: https://aflplus.plus/docs/afl-fuzz_approach/#overall-results
if cycles_done == 0 and minutes_without_find < 15:
    with st.container():
        st.info("Allow fuzzer to complete first cycle, sit back and relax",
                icon=":material/info:")
        with st.expander("More Info"):
            st.markdown(
                """
                It is recommended to allow each fuzzing session to complete at least one full cycle before drawing any conclusions. Ideally, fuzzing should continue well beyond the initial cycle to maximize coverage and effectiveness. Please note that the first cycle may require a day or more to complete.

                Reference: https://aflplus.plus/docs/afl-fuzz_approach/#overall-results
                """
            )

# If no new paths are found in the first several minutes of starting, warning will be triggered.
# Reference: https://aflplus.plus/docs/afl-fuzz_approach/#process-timing
if last_find_time == 0:
    with st.container():
        st.error("No new paths found within several minutes of starting. Check if the target binary is invoked correctly, memory limits, or input file validity.",
                 icon=":material/error:")
        with st.expander("More Info"):
            st.markdown(
                """
            If the fuzzer is not finding new paths within several minutes of starting, it is likely that the target binary is not being invoked correctly and does not process the input files as expected.

            Other possible causes:
            - The default memory limit (`-m`) is too restrictive, causing the program to exit early due to allocation failures.
            - The input files are invalid and always fail basic checks.

            **Recommended Actions:**
            - Verify the command line, arguments, and input redirection (`@@` for input file).
            - Increase or disable the memory limit if necessary.
            - Manually run the target with input files to confirm correct behavior.

            **Example Commands:**
            - Run the target manually with a sample input:
              ```
              ./target_binary < input_file
              ```
            - Run with memory limit disabled:
              ```
              afl-fuzz -m none -i input_dir -o output_dir -- ./target_binary @@
              ```
            - Check input file validity:
              ```
              file input_file
              hexdump -C input_file | head
              ```

            Reference: https://aflplus.plus/docs/afl-fuzz_approach/#process-timing
            """
            )

# if no new paths are found after 2h and there are no pending testcases in queue, warning will be triggered
# Reference: https://aflplus.plus/docs/fuzzing_in_depth/#h-how-long-to-fuzz-a-target
if cycles_without_find > 1 and pending_total == 0 and minutes_without_find > 120:
    with st.container():
        st.warning("Fuzzer not seeing new action in awhile",
                   icon=":material/warning:")
        with st.expander("More Info"):
            st.markdown(
                """
                If no new paths are discovered for an extended period (e.g., a day or a week), it is likely that further fuzzing will yield diminishing returns.

                **Recommended Actions:**
                - Replace or rotate secondary fuzzers (e.g., try different custom mutator modules).
                - Synchronize with other fuzzers that use different strategies or seeds.
                - Review your fuzzing configuration and input corpus for diversity.

                **Example Commands:**
                - To sync with another fuzzer's output:
                  ```
                  afl-sync -i /path/to/other_fuzzer/out -o /path/to/your_fuzzer/out
                  ```
                - To use a custom mutator:
                  ```
                  AFL_CUSTOM_MUTATOR_LIBRARY=/path/to/custom_mutator.so afl-fuzz -i input_dir -o output_dir -- ./target_binary @@
                  ```

                Reference: https://aflplus.plus/docs/fuzzing_in_depth/#h-how-long-to-fuzz-a-target
                """
            )

# if average execution speed in last hour is low, warning will be triggered
# Reference:
# https://aflplus.plus/docs/afl-fuzz_approach/#stage-progress
# https://aflplus.plus/docs/best_practices/#improving-speed
if avg_execs_per_sec < 500:
    with st.container():
        st.warning(
            f"Average execution speed in past hour is lower than ideal",
            icon=":material/warning:"
        )
        with st.expander("More info"):
            st.markdown(
                """
                Fuzzing speed should be ideally over 500 execs/sec most of the time and if it stays below 100, the job will probably take very long. 

                **Tips to improve execs/sec:**
                - Use llvm_mode: `afl-clang-lto` (llvm >= 11) or `afl-clang-fast` (llvm >= 9 recommended).
                - Enable persistent mode (can yield x2-x20 speed increase).
                - Instrument only the code you care about (see `instrumentation/README.instrument_list.md`).
                - If not using shmem persistent mode, set `AFL_TMPDIR` to a tempfs location for input files.
                - Improve Linux kernel performance (see documentation for kernel flags; note this reduces system security).
                - Use an ext2 filesystem with `noatime` for faster I/O.
                - Utilize multiple CPU cores for fuzzing.

                **Example Commands:**
                - Build with llvm_mode:
                  ```
                  CC=afl-clang-fast CXX=afl-clang-fast++ ./configure && make
                  ```
                - Enable persistent mode in your target:
                  ```
                  int main(int argc, char **argv) {
                      while (__AFL_LOOP(10000)) {
                          // fuzzed code here
                      }
                  }
                  ```
                - Set AFL_TMPDIR to tmpfs:
                  ```
                  export AFL_TMPDIR=/dev/shm
                  ```
                - Run fuzzer with multiple cores:
                  ```
                  afl-fuzz -i input_dir -o output_dir -M fuzzer01 -- ./target_binary @@
                  afl-fuzz -i input_dir -o output_dir -S fuzzer02 -- ./target_binary @@
                  ```

                Reference:
                - https://aflplus.plus/docs/afl-fuzz_approach/#stage-progress
                - https://aflplus.plus/docs/best_practices/#improving-speed
                """
            )

# if program is unstable, trigger warning
# Reference: https://aflplus.plus/docs/afl-fuzz_approach/#path-geometry
if stability < 85 and var_byte_count > 40:
    with st.container():
        st.warning(
            "Low stability detected. This may indicate issues with target determinism or resource handling.",
            icon=":material/warning:"
        )
        with st.expander("More info"):
            st.markdown(
                """
                Most targets will show a 100% stability score. Lower figures can be caused by:

                - **Uninitialized memory**: May indicate a security bug, though usually harmless for AFL.
                - **Manipulation of persistent resources**: Leftover temp files or shared memory objects can cause instability. Ensure the program isn't exiting early due to resource exhaustion (disk space, SHM handles, etc).
                - **Intentional randomness**: Some code (e.g., `select random();` in sqlite) is designed to behave randomly.
                - **Multithreading**: Multiple threads running in semi-random order can reduce stability. If stability stays above 90%, it's usually fine. Otherwise, try:
                    - Use `afl-clang-fast` for instrumentation (thread-local tracking is less prone to concurrency issues).
                      ```
                      CC=afl-clang-fast CXX=afl-clang-fast++ ./configure && make
                      ```
                    - Compile or run the target without threads, if possible. Common options:
                      ```
                      ./configure --without-threads
                      ./configure --disable-pthreads
                      ./configure --disable-openmp
                      ```
                    - Replace pthreads with GNU Pth for deterministic scheduling:
                      https://www.gnu.org/software/pth/
                - **Persistent mode**: Minor drops in stability can be normal, but major dips may mean code inside `__AFL_LOOP()` isn't properly cleaned up or reinitialized between iterations.

                **Recommended Actions:**
                - Check for uninitialized memory or resource leaks.
                - Review multithreading usage and try to reduce thread count or use deterministic threading.
                - Ensure proper cleanup and reinitialization in persistent mode.

                Reference: https://aflplus.plus/docs/afl-fuzz_approach/#path-geometry
                """
            )


total_execs_fig = go.Figure()
total_execs_fig.update_xaxes(showgrid=True)
total_execs_fig.update_layout(title="total_execs")
total_execs_fig.add_trace(go.Scatter(
    x=plot_data['relative_time'] / 60,
    y=plot_data['total_execs'],
))

st.plotly_chart(total_execs_fig)

execs_per_sec_fig = go.Figure()
execs_per_sec_fig.update_xaxes(showgrid=True)
execs_per_sec_fig.update_layout(title="execs_per_sec")
execs_per_sec_fig.add_trace(go.Scatter(
    x=plot_data['relative_time'],
    y=plot_data['execs_per_sec'],
))
execs_per_sec_fig.add_hline(y=500, line=dict(color="green", dash="dot"),
                            annotation_text="optimal speed", annotation_position="top right")
st.plotly_chart(execs_per_sec_fig)

saved_crashes_fig = go.Figure()
saved_crashes_fig.update_xaxes(showgrid=True)
saved_crashes_fig.update_layout(title="saved_crashes")
saved_crashes_fig.add_trace(go.Scatter(
    x=plot_data['relative_time'],
    y=plot_data['saved_crashes'],
    name="saved_crashes",
    showlegend=True
))

st.plotly_chart(saved_crashes_fig)

st.button("Refresh")
