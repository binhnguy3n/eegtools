import streamlit as st
import mne
import tempfile
import os

st.set_page_config(page_title="EEG Analyzer", layout="wide")

st.title("🧠 EEG Data Viewer & Analyzer")
st.write("Upload your BrainVision files (`.vhdr`, `.vmrk`, `.eeg`) to visualize the signals and events.")

# Create an interactive sidebar for our controls
st.sidebar.header("Plot Controls")
st.sidebar.write("Adjust these sliders to pan, zoom, and scale the EEG data.")

uploaded_files = st.file_uploader("Upload all 3 BrainVision Files", accept_multiple_files=True)

if len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as temp_dir:
        vhdr_path = ""
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if uploaded_file.name.endswith('.vhdr'):
                vhdr_path = file_path
        
        if vhdr_path:
            st.success("Files successfully processed!")
            
            # Load data
            raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
            max_time = float(raw.times[-1])
            
            # --- Dynamic UI Sliders ---
            # Pan through the data
            start_time = st.sidebar.slider("Start Time (s)", min_value=0.0, max_value=max_time, value=0.0, step=0.5)
            
            # Window Size acts as your X-axis zoom (narrower window = zoomed in)
            duration = st.sidebar.slider("Window Size (Zoom X)", min_value=0.5, max_value=max_time, value=10.0, step=0.5)
            
            # Scaling acts as your Y-axis zoom. MNE's default EEG scale is 20 µV.
            scaling_factor = st.sidebar.slider("EEG Scaling (µV)", min_value=1.0, max_value=100.0, value=20.0, step=1.0)
            
            # Control how many channels render at once to prevent vertical crowding
            n_channels = st.sidebar.slider("Channels to Display", min_value=1, max_value=len(raw.ch_names), value=20)
            
            # Prevent the viewing window from exceeding the maximum time of the recording
            if start_time + duration > max_time:
                start_time = max_time - duration

            # --- Plotting ---
            st.subheader("Interactive Raw EEG Signal")
            
            # Pass the Streamlit UI values directly into MNE's plotting function
            fig_raw = raw.plot(
                start=start_time, 
                duration=duration, 
                n_channels=n_channels,
                scalings=dict(eeg=scaling_factor * 1e-6),
                show=False
            )
            st.pyplot(fig_raw)
            
            st.subheader("Power Spectral Density (PSD)")
            fig_psd = raw.compute_psd(fmax=50).plot(show=False)
            st.pyplot(fig_psd)
            
            st.subheader("Stimulus Events")
            events, event_dict = mne.events_from_annotations(raw)
            fig_events = mne.viz.plot_events(events, sfreq=raw.info['sfreq'], show=False)
            st.pyplot(fig_events)
            
        else:
            st.error("Missing `.vhdr` file. Please ensure the header file was uploaded.")
elif len(uploaded_files) > 0:
    st.warning("Please upload exactly 3 files.")
