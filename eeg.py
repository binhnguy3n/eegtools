import streamlit as st
import mne
import tempfile
import os

# Configure the Streamlit page layout
st.set_page_config(page_title="EEG Analyzer", layout="wide")

st.title("🧠 EEG Data Viewer & Analyzer")
st.write("Upload your BrainVision files (`.vhdr`, `.vmrk`, `.eeg`) to visualize the signals, events, and ERPs.")

# --- Sidebar Controls ---
st.sidebar.header("Raw Plot Controls")
st.sidebar.write("Adjust these sliders to pan, zoom, and scale the raw EEG data.")
start_time = st.sidebar.slider("Start Time (s)", min_value=0.0, max_value=300.0, value=0.0, step=0.5, key="start")
duration = st.sidebar.slider("Window Size (Zoom X)", min_value=0.5, max_value=30.0, value=10.0, step=0.5)
scaling_factor = st.sidebar.slider("EEG Scaling (µV)", min_value=1.0, max_value=100.0, value=20.0, step=1.0)
n_channels = st.sidebar.slider("Channels to Display", min_value=1, max_value=65, value=20)

st.sidebar.markdown("---")
st.sidebar.header("ERP / Epoch Controls")
st.sidebar.write("Define the time window around each stimulus marker.")
tmin = st.sidebar.number_input("Pre-stimulus time (s)", min_value=-2.0, max_value=0.0, value=-0.2, step=0.1)
tmax = st.sidebar.number_input("Post-stimulus time (s)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

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
            
            # Load the raw EEG data
            raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
            
            # --- FIX: Set channel types and apply standard montage ---
            # Map non-EEG channels so MNE ignores them for scalp plots
            chan_types = {}
            if 'VEOG' in raw.ch_names: chan_types['VEOG'] = 'eog'
            if 'EKG' in raw.ch_names: chan_types['EKG'] = 'ecg'
            if chan_types:
                raw.set_channel_types(chan_types)
                
            # Apply the standard 10-05 electrode placement system
            montage = mne.channels.make_standard_montage('standard_1005')
            raw.set_montage(montage, on_missing='ignore')
            # ---------------------------------------------------------
            
            max_time = float(raw.times[-1])
            
            # Prevent the viewing window from exceeding the maximum time of the recording
            if start_time + duration > max_time:
                start_time = max_time - duration

            # --- 1. Raw EEG Plot ---
            st.subheader("Interactive Raw EEG Signal")
            fig_raw = raw.plot(
                start=start_time, 
                duration=duration, 
                n_channels=n_channels,
                scalings=dict(eeg=scaling_factor * 1e-6),
                show=False
            )
            st.pyplot(fig_raw)
            
            # --- 2. Event Extraction & ERPs ---
            events, event_dict = mne.events_from_annotations(raw)
            
            st.markdown("---")
            st.subheader("Event-Related Potentials (ERPs)")
            
            # Create a multiselect box populated dynamically by the markers
            selected_events = st.multiselect(
                "Select Stimulus Markers to Average", 
                options=list(event_dict.keys()), 
                default=list(event_dict.keys())
            )
            
            if selected_events:
                # Filter the event dictionary based on user selection
                selected_event_dict = {k: event_dict[k] for k in selected_events}
                
                # Create Epochs
                epochs = mne.Epochs(
                    raw, 
                    events, 
                    event_id=selected_event_dict, 
                    tmin=tmin, 
                    tmax=tmax, 
                    preload=True,
                    baseline=(None, 0) # Baseline correction using the pre-stimulus window
                )
                
                # Average the epochs to create the Evoked (ERP) object
                evoked = epochs.average()
                
                # Plot the ERP
                st.write(f"Averaged over **{len(epochs)}** selected epochs.")
                fig_erp = evoked.plot(spatial_colors=True, show=False)
                st.pyplot(fig_erp)
                
                # Plot ERP Topography at specific peak times
                st.write("Topographical Voltage Map")
                fig_topo = evoked.plot_topomap(times='auto', show=False)
                st.pyplot(fig_topo)
                
            else:
                st.info("Please select at least one event marker to generate the ERP.")
            
            # --- 3. PSD Plot ---
            st.markdown("---")
            st.subheader("Power Spectral Density (PSD)")
            fig_psd = raw.compute_psd(fmax=50).plot(show=False)
            st.pyplot(fig_psd)
            
        else:
            st.error("Missing `.vhdr` file. Please ensure the header file was uploaded.")
elif len(uploaded_files) > 0:
    st.warning("Please upload exactly 3 files: your .eeg, .vhdr, and .vmrk files.")
