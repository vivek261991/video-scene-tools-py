from typing import List, Tuple
import os
import json
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import imagehash

# Configuration
FRAME_ROOT_DIR = "./output_frames"
OUTPUT_MANIFEST = "scene_manifest.json"
GRID_SIZE = 5
PHASH_THRESHOLD = 8
RGB_THRESHOLD = 1000
GROUPING_STRATEGY = "rgb"  # or "phash"

def compute_phash(image_path: str) -> str:
    return str(imagehash.phash(Image.open(image_path)))

def compute_rgb_grid(image_path: str, grid_size: int = GRID_SIZE):
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    grid = {}
    dh, dw = h // grid_size, w // grid_size
    for i in range(grid_size):
        for j in range(grid_size):
            cell = img[i*dh:(i+1)*dh, j*dw:(j+1)*dw]
            mean_color = tuple(map(int, np.mean(cell.reshape(-1, 3), axis=0)))
            grid[f"{i},{j}"] = mean_color
    return grid

def rgb_distance(grid1: dict, grid2: dict) -> float:
    dist = 0
    for key in grid1:
        r1, g1, b1 = grid1[key]
        r2, g2, b2 = grid2[key]
        dist += (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
    return dist

def hamming_distance(hash1: str, hash2: str) -> int:
    return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')

def parse_timestamp(filename: str) -> float:
    parts = filename.replace(".jpg", "").split("_")
    h, m, s, ms = map(int, parts)
    return h * 3600 + m * 60 + s + ms / 1000

def group_frames(frame_dir: str, strategy: str):
    frame_files = sorted(f for f in os.listdir(frame_dir) if f.endswith(".jpg"))
    groups = []
    current_group = []
    last_feature = None

    for f in tqdm(frame_files, desc=f"Grouping frames in {frame_dir} using {strategy}"):
        path = os.path.join(frame_dir, f)

        if strategy == "phash":
            feature = compute_phash(path)
            distance_fn = hamming_distance
            threshold = PHASH_THRESHOLD
        elif strategy == "rgb":
            feature = compute_rgb_grid(path)
            distance_fn = rgb_distance
            threshold = RGB_THRESHOLD
        else:
            raise ValueError("Unsupported strategy")

        if last_feature is None:
            current_group = [(f, feature)]
        else:
            dist = distance_fn(feature, last_feature)
            if dist <= threshold:
                current_group.append((f, feature))
            else:
                groups.append(current_group)
                current_group = [(f, feature)]

        last_feature = feature

    if current_group:
        groups.append(current_group)

    return groups

def build_scene_manifest():
    manifest = {"scenes": []}

    for movie_folder in sorted(os.listdir(FRAME_ROOT_DIR)):
        frame_dir = os.path.join(FRAME_ROOT_DIR, movie_folder)
        if not os.path.isdir(frame_dir):
            continue

        print(f"\n🎞️ Processing: {movie_folder}")
        groups = group_frames(frame_dir, GROUPING_STRATEGY)

        for group in groups:
            frames = []
            for f, feature in group:
                frame_info = {
                    "frame": f,
                    "timestamp": parse_timestamp(f),
                    "movie_name": movie_folder
                }
                if GROUPING_STRATEGY == "phash":
                    frame_info["phash"] = feature
                elif GROUPING_STRATEGY == "rgb":
                    frame_info["rgb_grid"] = {k: list(v) for k, v in feature.items()}

                frames.append(frame_info)

            manifest["scenes"].append({
                "timestamp": frames[0]["timestamp"],
                "movie_name": movie_folder,
                "frames": frames
            })

    with open(OUTPUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n✅ Saved manifest with {len(manifest['scenes'])} total scenes to {OUTPUT_MANIFEST}")

if __name__ == "__main__":
    build_scene_manifest()
