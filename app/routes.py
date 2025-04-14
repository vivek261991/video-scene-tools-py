# app/routes.py

from flask import Blueprint, request, jsonify
import json
import whisper 
import uuid
import os

product_bp = Blueprint("product", __name__)

# Load scene_products.json once at startup
with open("scene_products.json") as f:
    scene_products = json.load(f)

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
    if "audio" not in request.files:
        print("no audio")
        return jsonify({"error": "No audio file provided"}), 400

    audio = request.files["audio"]
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
