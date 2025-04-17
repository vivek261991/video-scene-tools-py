# app/routes.py

from flask import Blueprint, request, jsonify
import json
import whisper 
import uuid
import os
import numpy as np

product_bp = Blueprint("product", __name__)

# Load scene_products.json and scene manifest once at startup
with open("scene_products.json") as f:
    scene_products = json.load(f)

with open("scene_manifest.json") as f:
    scene_manifest = json.load(f)

def cosine_similarity(vec1, vec2):
    a = np.array(vec1).flatten()
    b = np.array(vec2).flatten()
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot / (norm_a * norm_b + 1e-9)  # had to include esilon else the code runs into divide-by-zero error

def flatten_rgb_grid(rgb_grid):
    return [component for cell in sorted(rgb_grid.keys()) for component in rgb_grid[cell]]

AUDIO_UPLOAD_DIR = "uploads"
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)

whisper_model = whisper.load_model("base")

def timestamp_in_range(start, end, timestamp):
    """Check if timestamp falls within [start, end] range."""
    return start <= timestamp <= end


@product_bp.route("/api/search/product", methods=["POST"])
def search_products_for_time_range():
    data = request.get_json()
    start = float(data.get("start", 0))
    end = float(data.get("end", 0))

    matching_groups = []

    for scene in scene_products["scenes"]:
        for group in scene.get("groups", []):
            group_time = float(group["timestamp"])

            # app sends a start and end timestamp (based on transcript chunks retrieved from Milvus)
            if timestamp_in_range(start, end, group_time):
                matching_groups.append({
                    "scene_timestamp": scene["timestamp"],
                    "group_timestamp": group_time,
                    "frame": group.get("frame"),
                    "products": group.get("products", [])
                })

    if matching_groups:
        return jsonify({"results": matching_groups})
    else:
        return jsonify({"message": "No matching products found for the given time range."}), 404

@product_bp.route("/api/search/audio", methods=["POST"])
def search_by_audio():
    if "file" not in request.files:
        print("no audio")
        return jsonify({"error": "No audio file provided"}), 400

    audio = request.files["file"]
    filename = f"{uuid.uuid4()}.webm"
    filepath = os.path.join(AUDIO_UPLOAD_DIR, filename)
    audio.save(filepath)

    try:
        result = whisper_model.transcribe(filepath)
        extracted_text = result["text"]
        print(extracted_text)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        print("processing complete")
        #os.remove(filepath)

    return jsonify({"transcript": extracted_text})


@product_bp.route("/api/search/frame", methods=["POST"])
def match_frame_rgb():
    try:
        data = request.get_json()
        input_rgb = data.get("rgb_grid")
        if not input_rgb:
            return jsonify({"error": "Missing RGB data"}), 400

        best_match = None
        highest_similarity = -1

        for scene in scene_manifest["scenes"]:
            for frame in scene.get("frames", []):
                if "rgb_grid" not in frame:
                    continue
                flattened_frame_rgb = flatten_rgb_grid(frame["rgb_grid"])
                flattened_input_rgb = flatten_rgb_grid(input_rgb)

                similarity = cosine_similarity(flattened_input_rgb, flattened_frame_rgb)

                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = {
                        "movie_name": frame.get("movie_name", "Unknown"),
                        "scene_timestamp": scene.get("timestamp"),
                        "frame_timestamp": frame.get("timestamp"),
                        "frame": frame.get("frame"),
                        "similarity": similarity
                    }

        if best_match:
            return jsonify(best_match)
        else:
            return jsonify({"message": "No matching frame found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
