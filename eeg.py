import streamlit as st
import mne
import tempfile
import os

# Configure the Streamlit page layout
st.set_page_config(page_title="EEG Analyzer", layout="wide")

st.title("🧠 EEG Data Viewer & Analyzer")
st.write("Upload your BrainVision files (`.vhdr`, `.vmrk`, `.eeg`) to visualize the signals and events.")

# Upload multiple files
uploaded_files = st.file_uploader("Upload all 3 BrainVision Files", accept_multiple_files=True)

if len(uploaded_files) == 3:
    # Create a temporary directory to store the files together
    with tempfile.TemporaryDirectory() as temp_dir:
        vhdr_path = ""
        
        # Save uploaded files into the temporary directory
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Identify the header file which MNE uses to load the dataset
            if uploaded_file.name.endswith('.vhdr'):
                vhdr_path = file_path
        
        if vhdr_path:
            st.success("Files successfully processed!")
            
            # 1. Load the raw EEG data
            raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
            
            # 2. Display basic metadata
            st.subheader("Dataset Information")
            col1, col2, col3 = st.columns(3)
            col1.metric("Channels", len(raw.ch_names))
            col2.metric("Sampling Rate", f"{raw.info['sfreq']} Hz")
            col3.metric("Duration", f"{raw.times[-1]:.2f} seconds")
            
            # 3. Plot Raw EEG Signal
            st.subheader("Raw EEG Signal")
            st.write("A 10-second snippet of the raw signal.")
            fig_raw = raw.plot(duration=10.0, show=False)
            st.pyplot(fig_raw)
            
            # 4. Plot Power Spectral Density (PSD)
            st.subheader("Power Spectral Density (PSD)")
            st.write("Frequency analysis of the brain waves.")
            fig_psd = raw.compute_psd(fmax=50).plot(show=False)
            st.pyplot(fig_psd)
            
            # 5. Extract and Plot Events (from your .vmrk file)
            st.subheader("Stimulus Events")
            events, event_dict = mne.events_from_annotations(raw)
            fig_events = mne.viz.plot_events(events, sfreq=raw.info['sfreq'], show=False)
            st.pyplot(fig_events)
            
        else:
            st.error("Missing `.vhdr` file. Please make sure you uploaded the header file.")
elif len(uploaded_files) > 0:
    st.warning("Please upload exactly 3 files: your .eeg, .vhdr, and .vmrk files.")
