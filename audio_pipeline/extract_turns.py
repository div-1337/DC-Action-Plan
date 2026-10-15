"""
DataCatalyst: Silero VAD Turn Slicer & Boundary Cataloguer
Detects speech turns, intra-speaker thinking pauses, ambient silence, and overlaps.
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

def load_silero_vad():
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        trust_repo=True
    )
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    return model, get_speech_timestamps

def resample_if_needed(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    if orig_sr % target_sr == 0:
        step = orig_sr // target_sr
        return audio[::step].copy()
    num_target_samples = int(len(audio) * target_sr / orig_sr)
    step = orig_sr / target_sr
    idx = (np.arange(num_target_samples) * step).astype(np.int64)
    idx = np.clip(idx, 0, len(audio) - 1)
    return audio[idx].copy()

def process_session(call_dir: Path, model, get_speech_timestamps, output_dir: Path, max_per_type=6) -> dict:
    call_id = call_dir.name[len("call_"):] if call_dir.name.startswith("call_") else call_dir.name
    combined_wavs = list(call_dir.glob("combined_*.wav"))
    spk_wavs = list(call_dir.glob("spk_*.wav"))

    if not spk_wavs:
        return {"call_id": call_id, "status": "SKIPPED_NO_SPK_WAVS"}

    hesitations_dir = output_dir / "hesitations"
    silence_dir = output_dir / "ambient_silence"
    overlap_dir = output_dir / "overlaps"

    for d in (hesitations_dir, silence_dir, overlap_dir):
        d.mkdir(parents=True, exist_ok=True)

    extracted = {"hesitations": [], "ambient_silence": [], "overlaps": []}

    # Load speaker tracks
    speaker_data = {}
    master_sr = 48000
    min_len = None

    for spk_p in spk_wavs:
        spk_id = spk_p.name.split("-")[0]
        data, sr = sf.read(str(spk_p), dtype='float32')
        if data.ndim > 1:
            data = data[:, 0]
        speaker_data[spk_id] = {"data": data, "sr": sr, "path": spk_p}
        master_sr = sr
        if min_len is None or len(data) < min_len:
            min_len = len(data)

    # 1. Run VAD per speaker
    speaker_timestamps = {}
    for spk_id, s_info in speaker_data.items():
        data_16k = resample_if_needed(s_info["data"], s_info["sr"], 16000)
        tensor_16k = torch.from_numpy(data_16k).float()
        
        # Get speech timestamps (samples at 16kHz)
        raw_ts = get_speech_timestamps(
            tensor_16k,
            model,
            sampling_rate=16000,
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100
        )
        # Convert to seconds
        ts_sec = [{"start": t["start"] / 16000.0, "end": t["end"] / 16000.0} for t in raw_ts]
        speaker_timestamps[spk_id] = ts_sec

    # 2. Extract Mid-Thought Pauses / Hesitations (200ms <= pause <= 800ms)
    for spk_id, ts_list in speaker_timestamps.items():
        spk_audio = speaker_data[spk_id]["data"]
        count = 0
        for i in range(len(ts_list) - 1):
            if count >= max_per_type:
                break
            t1 = ts_list[i]
            t2 = ts_list[i + 1]
            pause_sec = t2["start"] - t1["end"]
            
            # Check pause duration: 200ms to 800ms, and prior speech at least 1.5s
            if 0.20 <= pause_sec <= 0.80 and (t1["end"] - t1["start"]) >= 1.2:
                # Clip window: Last 2.5s of speech + the pause + 0.5s of continuation
                clip_start_sec = max(0.0, t1["end"] - 2.5)
                clip_end_sec = min(len(spk_audio) / master_sr, t2["start"] + 0.5)
                
                start_sample = int(clip_start_sec * master_sr)
                end_sample = int(clip_end_sec * master_sr)
                clip_wav = spk_audio[start_sample:end_sample]

                pause_duration_ms = int(pause_sec * 1000)
                clip_name = f"DC_HES_{call_id[:8]}_{spk_id}_p{pause_duration_ms}ms_{int(clip_start_sec)}s.wav"
                clip_path = hesitations_dir / clip_name
                sf.write(str(clip_path), clip_wav, master_sr)

                meta = {
                    "clip_name": clip_name,
                    "call_id": call_id,
                    "speaker_id": spk_id,
                    "pause_duration_ms": pause_duration_ms,
                    "pause_start_sec": round(t1["end"], 3),
                    "pause_end_sec": round(t2["start"], 3),
                    "clip_duration_sec": round(len(clip_wav) / master_sr, 2),
                    "file_path": str(clip_path)
                }
                extracted["hesitations"].append(meta)
                count += 1

    # 3. Extract Overlapping Speech (Crosstalk)
    spk_ids = list(speaker_timestamps.keys())
    if len(spk_ids) >= 2 and combined_wavs:
        comb_audio, c_sr = sf.read(str(combined_wavs[0]), dtype='float32')
        ts_a = speaker_timestamps[spk_ids[0]]
        ts_b = speaker_timestamps[spk_ids[1]]
        
        count = 0
        for ta in ts_a:
            if count >= max_per_type:
                break
            for tb in ts_b:
                overlap_start = max(ta["start"], tb["start"])
                overlap_end = min(ta["end"], tb["end"])
                overlap_dur = overlap_end - overlap_start
                
                if overlap_dur >= 0.40: # Overlap >= 400ms
                    # Extract 1.0s before overlap + overlap + 1.0s after
                    clip_start_sec = max(0.0, overlap_start - 1.0)
                    clip_end_sec = min(len(comb_audio) / c_sr, overlap_end + 1.0)
                    
                    s_idx = int(clip_start_sec * c_sr)
                    e_idx = int(clip_end_sec * c_sr)
                    clip_wav = comb_audio[s_idx:e_idx]

                    clip_name = f"DC_OVR_{call_id[:8]}_{int(overlap_dur*1000)}ms_{int(clip_start_sec)}s.wav"
                    clip_path = overlap_dir / clip_name
                    sf.write(str(clip_path), clip_wav, c_sr)

                    meta = {
                        "clip_name": clip_name,
                        "call_id": call_id,
                        "overlap_duration_ms": int(overlap_dur * 1000),
                        "overlap_start_sec": round(overlap_start, 3),
                        "overlap_end_sec": round(overlap_end, 3),
                        "clip_duration_sec": round(len(clip_wav) / c_sr, 2),
                        "file_path": str(clip_path)
                    }
                    extracted["overlaps"].append(meta)
                    count += 1
                    break

    # 4. Extract Ambient Room Silence / Breathing
    # Find intervals where neither speaker is speaking for >= 1.5s
    if combined_wavs and len(spk_ids) >= 2:
        comb_audio, c_sr = sf.read(str(combined_wavs[0]), dtype='float32')
        # Merge all speech timestamps
        all_speech = sorted(speaker_timestamps[spk_ids[0]] + speaker_timestamps[spk_ids[1]], key=lambda x: x["start"])
        
        count = 0
        cur_time = 0.0
        for seg in all_speech:
            if count >= max_per_type:
                break
            if seg["start"] - cur_time >= 1.8:
                # Silence window: between cur_time + 0.2 and seg['start'] - 0.2
                sil_start = cur_time + 0.2
                sil_end = min(cur_time + 4.5, seg["start"] - 0.2)
                if sil_end - sil_start >= 1.5:
                    s_idx = int(sil_start * c_sr)
                    e_idx = int(sil_end * c_sr)
                    clip_wav = comb_audio[s_idx:e_idx]

                    clip_name = f"DC_SIL_{call_id[:8]}_{int((sil_end - sil_start)*1000)}ms_{int(sil_start)}s.wav"
                    clip_path = silence_dir / clip_name
                    sf.write(str(clip_path), clip_wav, c_sr)

                    meta = {
                        "clip_name": clip_name,
                        "call_id": call_id,
                        "silence_duration_ms": int((sil_end - sil_start) * 1000),
                        "silence_start_sec": round(sil_start, 3),
                        "clip_duration_sec": round(len(clip_wav) / c_sr, 2),
                        "file_path": str(clip_path)
                    }
                    extracted["ambient_silence"].append(meta)
                    count += 1
            cur_time = max(cur_time, seg["end"])

    return {
        "call_id": call_id,
        "extracted_counts": {k: len(v) for k, v in extracted.items()},
        "clips": extracted
    }

def main():
    parser = argparse.ArgumentParser(description="DataCatalyst Silero VAD Slicer")
    parser.add_argument("--input-dir", type=str, default=r"C:\Users\manoj\OneDrive\Desktop\desktop old\hi-conversational audio")
    parser.add_argument("--output-dir", type=str, default="test_clips")
    parser.add_argument("--max-sessions", type=int, default=10, help="Number of sessions to process (default: 10 for fast extraction)")
    parser.add_argument("--output-manifest", type=str, default="manifests/turn_index.json")
    args = parser.parse_args()

    audio_root = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    call_dirs = [d for d in audio_root.iterdir() if d.is_dir() and d.name.startswith("call_")]
    call_dirs.sort(key=lambda d: d.name)

    if args.max_sessions > 0:
        call_dirs = call_dirs[:args.max_sessions]

    print("\n=======================================================")
    print(" DataCatalyst Silero VAD Turn Slicer & Edge-Case Extractor")
    print(f" Processing Sessions : {len(call_dirs)}")
    print(f" Output Directory    : {output_dir}")
    print("=======================================================\n")

    print("[1/3] Loading Silero VAD model into CPU memory...")
    t0 = time.time()
    model, get_speech_timestamps = load_silero_vad()
    print(f"      Model loaded in {round(time.time() - t0, 2)}s.")

    total_extracted = {"hesitations": 0, "ambient_silence": 0, "overlaps": 0}
    session_results = []

    print("\n[2/3] Extracting adversarial clips across sessions...")
    for idx, d in enumerate(call_dirs, 1):
        t_start = time.time()
        res = process_session(d, model, get_speech_timestamps, output_dir)
        session_results.append(res)
        counts = res.get("extracted_counts", {})
        for k in total_extracted:
            total_extracted[k] += counts.get(k, 0)
        
        t_el = round(time.time() - t_start, 2)
        print(f"  [{idx}/{len(call_dirs)}] {d.name} -> Hesitations: {counts.get('hesitations', 0)} | Silences: {counts.get('ambient_silence', 0)} | Overlaps: {counts.get('overlaps', 0)} ({t_el}s)", flush=True)

    # Save turn index manifest
    out_manifest = Path(args.output_manifest)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sessions_processed": len(call_dirs),
            "summary_counts": total_extracted,
            "sessions": session_results
        }, f, indent=2)

    print("\n-------------------------------------------------------")
    print(" SLICING & CATALOGING COMPLETE:")
    print(f" Mid-Thought Hesitations Extracted : {total_extracted['hesitations']} clips")
    print(f" Ambient Silence / Room Tone Extracted: {total_extracted['ambient_silence']} clips")
    print(f" Overlapping Speech Extracted      : {total_extracted['overlaps']} clips")
    print(f" Turn Index Manifest Saved To      : {out_manifest}")
    print("-------------------------------------------------------\n")

if __name__ == "__main__":
    main()
