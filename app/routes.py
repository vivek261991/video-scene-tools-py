# app/routes.py

from flask import Blueprint, request, jsonify
import json

product_bp = Blueprint("product", __name__)

# Load scene_products.json once at startup
with open("scene_products.json") as f:
    scene_products = json.load(f)


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
