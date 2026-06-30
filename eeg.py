if vhdr_path:
            st.success("Files successfully processed!")
            
            # Load data
            raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
            
            # --- FIX: Set channel types and apply standard montage ---
            # 1. Map non-EEG channels so MNE ignores them for scalp plots
            chan_types = {}
            if 'VEOG' in raw.ch_names: chan_types['VEOG'] = 'eog'
            if 'EKG' in raw.ch_names: chan_types['EKG'] = 'ecg'
            if chan_types:
                raw.set_channel_types(chan_types)
                
            # 2. Apply the standard 10-05 electrode placement system
            montage = mne.channels.make_standard_montage('standard_1005')
            raw.set_montage(montage, on_missing='ignore')
            # ---------------------------------------------------------
            
            max_time = float(raw.times[-1])
            
            # Adjust max values for raw plot sliders dynamically based on the uploaded data
            if start_time + duration > max_time:
                start_time = max_time - duration
