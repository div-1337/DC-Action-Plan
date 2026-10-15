"""
DataCatalyst: Automated Acoustic Health & Channel Bleed Profiler
Usage:
    python scripts/acoustic_audit.py --input-dir <path_to_audio_folder>
    python scripts/acoustic_audit.py --input-file <path_to_single_wav>
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
import numpy as np
import soundfile as sf

def analyze_audio_file(file_path: Path) -> dict:
    start_time = time.time()
    try:
        info = sf.info(str(file_path))
    except Exception as e:
        return {"file": file_path.name, "error": f"Failed to read file info: {str(e)}", "status": "FAIL"}

    duration_sec = info.duration
    sample_rate = info.samplerate
    channels = info.channels

    # Read audio data as float32
    try:
        data, sr = sf.read(str(file_path), dtype='float32')
    except Exception as e:
        return {"file": file_path.name, "error": f"Failed to read audio data: {str(e)}", "status": "FAIL"}

    # Ensure 2D array [samples, channels]
    if data.ndim == 1:
        data = data[:, np.newaxis]

    channel_reports = []
    frame_len = int(sample_rate * 0.02) # 20ms frames
    
    for ch in range(channels):
        ch_data = data[:, ch]
        num_samples = len(ch_data)
        
        # Peak amplitude and clipping
        peak_linear = float(np.max(np.abs(ch_data))) if num_samples > 0 else 0.0
        peak_dbfs = 20 * np.log10(max(peak_linear, 1e-7))
        
        # Clipping: samples at or near 1.0 (>= 0.999)
        clip_count = int(np.sum(np.abs(ch_data) >= 0.999))
        clip_pct = (clip_count / max(num_samples, 1)) * 100.0
        
        # RMS Energy
        rms_val = np.sqrt(np.mean(ch_data**2)) if num_samples > 0 else 1e-7
        rms_dbfs = 20 * np.log10(max(rms_val, 1e-7))

        # Frame-level energy for SNR estimation
        if num_samples >= frame_len:
            num_frames = num_samples // frame_len
            frames = ch_data[:num_frames * frame_len].reshape(num_frames, frame_len)
            frame_rms = np.sqrt(np.mean(frames**2, axis=1))
            frame_db = 20 * np.log10(np.maximum(frame_rms, 1e-7))

            # 90th percentile = speech level, 10th percentile = noise floor level
            speech_level = float(np.percentile(frame_db, 90))
            noise_floor = float(np.percentile(frame_db, 10))
            estimated_snr = max(0.0, speech_level - noise_floor)
        else:
            speech_level = rms_dbfs
            noise_floor = -60.0
            estimated_snr = 20.0

        channel_reports.append({
            "channel_idx": ch,
            "peak_dbfs": round(peak_dbfs, 2),
            "clipping_pct": round(clip_pct, 4),
            "rms_dbfs": round(rms_dbfs, 2),
            "noise_floor_dbfs": round(noise_floor, 2),
            "speech_level_dbfs": round(speech_level, 2),
            "estimated_snr_db": round(estimated_snr, 2)
        })

    # Cross-channel bleed analysis (for dual-channel)
    bleed_score_db = None
    if channels == 2 and len(data) >= frame_len:
        ch0 = data[:, 0]
        ch1 = data[:, 1]
        num_frames = len(data) // frame_len
        f0 = np.sqrt(np.mean(ch0[:num_frames * frame_len].reshape(num_frames, frame_len)**2, axis=1))
        f1 = np.sqrt(np.mean(ch1[:num_frames * frame_len].reshape(num_frames, frame_len)**2, axis=1))
        
        # Active speech mask for Ch 0
        thresh0 = np.percentile(f0, 75)
        active0 = f0 > thresh0
        if np.any(active0):
            # Energy of Ch 1 when Ch 0 is active vs when both are silent
            bleed_on_ch1 = float(20 * np.log10(np.maximum(np.mean(f1[active0]), 1e-7)))
            speech_on_ch0 = float(20 * np.log10(np.maximum(np.mean(f0[active0]), 1e-7)))
            bleed_score_db = round(float(bleed_on_ch1 - speech_on_ch0), 2)

    # Determine status
    status = "PASS"
    flags = []
    
    for ch in channel_reports:
        if ch["clipping_pct"] > 0.05:
            status = "FAIL"
            flags.append(f"Ch{ch['channel_idx']}: Excessive clipping ({ch['clipping_pct']}%)")
        elif ch["estimated_snr_db"] < 15.0:
            status = "WARN" if status != "FAIL" else status
            flags.append(f"Ch{ch['channel_idx']}: Low SNR ({ch['estimated_snr_db']} dB)")

    if bleed_score_db is not None and bleed_score_db > -20.0:
        status = "WARN" if status != "FAIL" else status
        flags.append(f"High cross-channel bleed ({bleed_score_db} dB)")

    elapsed = time.time() - start_time

    return {
        "file": file_path.name,
        "path": str(file_path),
        "duration_sec": round(duration_sec, 2),
        "sample_rate": sample_rate,
        "channels": channels,
        "format": info.format,
        "subtype": info.subtype,
        "channel_reports": channel_reports,
        "bleed_score_db": bleed_score_db,
        "status": status,
        "flags": flags,
        "audit_time_sec": round(elapsed, 3)
    }

def main():
    parser = argparse.ArgumentParser(description="DataCatalyst Acoustic Health & Bleed Profiler")
    parser.add_argument("--input-dir", type=str, help="Directory containing audio files")
    parser.add_argument("--input-file", type=str, help="Single audio file to audit")
    parser.add_argument("--output", type=str, default="reports/acoustic_health_report.json", help="Path to save JSON report")
    parser.add_argument("--pattern", type=str, default="*.wav", help="File pattern to match, e.g. combined_*.wav or *.wav")
    parser.add_argument("--recursive", action="store_true", default=True, help="Scan directories recursively (default: True)")
    args = parser.parse_args()

    files = []
    if args.input_file:
        p = Path(args.input_file)
        if p.exists():
            files.append(p)
        else:
            print(f"Error: File not found: {args.input_file}")
            sys.exit(1)
    elif args.input_dir:
        d = Path(args.input_dir)
        if d.exists() and d.is_dir():
            scan_fn = d.rglob if args.recursive else d.glob
            files.extend(scan_fn(args.pattern))
            files = sorted(files)
        else:
            print(f"Error: Directory not found: {args.input_dir}")
            sys.exit(1)
    else:
        # Default fallback
        d = Path("./raw_audio")
        if d.exists():
            files.extend(d.rglob(args.pattern))
            files = sorted(files)
        else:
            print("Please specify --input-dir or --input-file")
            sys.exit(1)

    if not files:
        print("No audio files found to analyze.")
        sys.exit(0)

    print(f"\n=======================================================")
    print(f" DataCatalyst Acoustic Health & Channel Bleed Profiler")
    print(f" Total files to analyze: {len(files)}")
    print(f"=======================================================\n")

    results = []
    total_audio_sec = 0.0
    start_total = time.time()

    for idx, f in enumerate(files, 1):
        report = analyze_audio_file(f)
        results.append(report)
        dur = report.get("duration_sec", 0.0)
        total_audio_sec += dur
        
        status_color = "[PASS]" if report["status"] == "PASS" else ("[WARN]" if report["status"] == "WARN" else "[FAIL]")
        snr_vals = [f"{ch['estimated_snr_db']}dB" for ch in report.get("channel_reports", [])]
        snr_str = "/".join(snr_vals) if snr_vals else "N/A"
        clip_vals = [f"{ch['clipping_pct']}%" for ch in report.get("channel_reports", [])]
        clip_str = "/".join(clip_vals) if clip_vals else "0%"
        bleed_str = f"{report.get('bleed_score_db')}dB" if report.get('bleed_score_db') is not None else "N/A"

        print(f"[{idx}/{len(files)}] {status_color} {f.name} | Dur: {dur}s | SNR: {snr_str} | Clip: {clip_str} | Bleed: {bleed_str} ({report.get('audit_time_sec')}s)")
        if report.get("flags"):
            for flag in report["flags"]:
                print(f"       -> Issue: {flag}")

    total_elapsed = time.time() - start_total
    total_audio_hrs = total_audio_sec / 3600.0

    print(f"\n-------------------------------------------------------")
    print(f" AUDIT COMPLETE:")
    print(f" Total Audio Analyzed : {round(total_audio_hrs, 2)} hours ({round(total_audio_sec, 1)} seconds)")
    print(f" Processing Time Taken: {round(total_elapsed, 2)} seconds")
    print(f" Speed Multiplier     : {round(total_audio_sec / max(total_elapsed, 0.001), 1)}x real-time")
    print(f"-------------------------------------------------------")

    # Save JSON report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_files": len(files),
            "total_audio_hours": round(total_audio_hrs, 2),
            "processing_time_sec": round(total_elapsed, 2),
            "files": results
        }, f, indent=2, default=lambda o: float(o) if hasattr(o, '__float__') else str(o))

    print(f" Detailed report saved to: {out_path}\n")

if __name__ == "__main__":
    main()
