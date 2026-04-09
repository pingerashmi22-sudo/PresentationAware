import base64
import tempfile
import numpy as np
import librosa
import re

def compute_emphasis_score(audio_b64, words_data, sample_rate=16000):
    """
    Detect emphasized words from audio using pitch, volume, and duration.
    
    Args:
        audio_b64 (str): Base64-encoded audio (WebM or similar)
        words_data (list): List of Whisper word objects with .word, .start, .end attributes
        sample_rate (int): Target sample rate for analysis
    
    Returns:
        list: Emphasized words (strings) sorted by emphasis strength
    """
    if not audio_b64 or not words_data:
        return []
    
    # Decode and save audio to temporary file
    if "," in audio_b64:
        audio_b64 = audio_b64.split(",")[1]
    try:
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Load audio with librosa
        y, sr = librosa.load(tmp_path, sr=sample_rate, mono=True)
        
        # Compute RMS energy (volume) per frame
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        times_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
        
        # Compute pitch (F0) using pYIN algorithm
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=80, fmax=400, sr=sr, hop_length=hop_length)
        times_f0 = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
        
        # Prepare arrays for word-level features
        word_features = []  # (word, duration, volume, pitch)
        
        for w in words_data:
            word = w.word.strip().lower()
            # Skip very short words or common stopwords
            if len(word) <= 2 or word in {"the","and","this","that","with","for","from","are","was","were","been"}:
                continue
            
            start = w.start
            end = w.end
            duration = end - start
            
            # Extract volume over word interval
            mask_vol = (times_rms >= start) & (times_rms <= end)
            if np.any(mask_vol):
                word_vol = np.mean(rms[mask_vol])
            else:
                word_vol = 0.0
            
            # Extract pitch over word interval (ignore unvoiced frames)
            mask_pitch = (times_f0 >= start) & (times_f0 <= end) & voiced_flag
            if np.any(mask_pitch):
                word_pitch = np.mean(f0[mask_pitch])
            else:
                word_pitch = 0.0
            
            word_features.append((word, duration, word_vol, word_pitch))
        
        os.remove(tmp_path)
        
        if not word_features:
            return []
        
        # Normalize features across words
        durations = np.array([f[1] for f in word_features])
        volumes = np.array([f[2] for f in word_features])
        pitches = np.array([f[3] for f in word_features])
        
        # Avoid division by zero when all values are identical
        def safe_norm(arr):
            if np.max(arr) - np.min(arr) < 1e-6:
                return np.zeros_like(arr)
            return (arr - np.min(arr)) / (np.max(arr) - np.min(arr))
        
        norm_dur = safe_norm(durations)
        norm_vol = safe_norm(volumes)
        norm_pitch = safe_norm(pitches)
        
        # Emphasis score: weighted sum (pitch 0.4, volume 0.4, duration 0.2)
        scores = 0.4 * norm_pitch + 0.4 * norm_vol + 0.2 * norm_dur
        
        # Pair words with scores
        scored_words = [(word_features[i][0], scores[i]) for i in range(len(word_features))]
        scored_words.sort(key=lambda x: x[1], reverse=True)
        
        # Return top emphasized words (limit to 3)
        threshold = np.mean(scores) + 0.5 * np.std(scores) if len(scores) > 1 else 0.5
        emphasized = [w for w, s in scored_words if s >= threshold][:3]
        return emphasized
        
    except Exception as e:
        print(f"Emphasis detection failed: {e}")
        return []