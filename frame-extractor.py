import os
import subprocess
import argparse
from pathlib import Path
from datetime import timedelta

def extract_frames(
    input_file,
    output_dir=None,
    fps=1.0,
    width=512,
    height=288,
    quality_percent=80
):
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_file}")

    output_dir = Path(output_dir) if output_dir else input_path.with_suffix("")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert JPEG quality to ffmpeg q:v scale (2=best, 31=worst)
    qvalue = round(((100 - quality_percent) / 100.0 * 29) + 2)
    temp_pattern = output_dir / "frame_%04d.jpg"

    # Run ffmpeg to extract frames
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-vf", f"fps={fps},scale={width}:{height}",
        "-q:v", str(qvalue),
        str(temp_pattern)
    ]

    print("▶️ Extracting frames with command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    rename_extracted_frames(output_dir, fps)


def rename_extracted_frames(output_dir, fps):
    files = sorted(output_dir.glob("frame_*.jpg"))
    for i, file in enumerate(files, start=1):
        seconds = (i - 1) / fps
        ts = timedelta(seconds=seconds)
        new_name = "{:02}_{:02}_{:02}_{:03}.jpg".format(
            int(ts.total_seconds() // 3600),
            int(ts.total_seconds() % 3600 // 60),
            int(ts.total_seconds() % 60),
            int(ts.microseconds / 1000)
        )
        new_path = output_dir / new_name
        file.rename(new_path)
        print(f"✅ Renamed {file.name} -> {new_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and rename video frames")
    parser.add_argument("input_file", help="Path to the input video file")
    parser.add_argument("-d", "--output-dir", help="Output directory for frames")
    parser.add_argument("-f", "--fps", type=float, default=1.0, help="Frames per second")
    parser.add_argument("--width", type=int, default=512, help="Resize width")
    parser.add_argument("--height", type=int, default=288, help="Resize height")
    parser.add_argument("-q", "--quality", type=int, default=80, help="JPEG quality (0-100)")

    args = parser.parse_args()
    extract_frames(
        args.input_file,
        args.output_dir,
        args.fps,
        args.width,
        args.height,
        args.quality
    )
