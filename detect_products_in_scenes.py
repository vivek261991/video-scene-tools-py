import os
import json
from tqdm import tqdm
from product_detector import detect_products_in_image

SCENE_MANIFEST_PATH = "scene_manifest.json"
FRAME_DIR = "output_frames"  # where your frames are located
OUTPUT_PATH = "scene_products.json"

def load_scene_manifest(path: str):
    with open(path, "r") as f:
        return json.load(f)

def get_representative_frame(frames: list[str]) -> str:
    # Pick middle frame as representative
    if not frames:
        return None
    return frames[len(frames) // 2]

def detect_products_for_manifest():
    manifest = load_scene_manifest(SCENE_MANIFEST_PATH)
    enriched_manifest = {"scenes": []}

    for scene in tqdm(manifest["scenes"], desc="Processing scenes"):
        enriched_scene = {"timestamp": scene["timestamp"], "groups": []}

        for group in scene["groups"]:
            frame_files = group["frames"]
            representative = get_representative_frame(frame_files)
            full_path = os.path.join(FRAME_DIR, representative)

            if os.path.exists(full_path):
                try:
                    result = detect_products_in_image(full_path)
                    print(full_path)
                    print(result)
                    # print(result)

                    # If it's a string, try parsing JSON
                    if isinstance(result, str):
                        try:
                            parsed_result = json.loads(result)
                        except json.JSONDecodeError:
                            parsed_result = {"error": "Invalid JSON in model response"}
                    else:
                        parsed_result = result  # It's already a dict (e.g. {"error": ...})

                except Exception as e:
                    print("inside exception..")
                    parsed_result = {"error": str(e)}

                enriched_scene["groups"].append({
                    "timestamp": group["timestamp"],
                    "frame": representative,
                    "products": parsed_result
            })

        enriched_manifest["scenes"].append(enriched_scene)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(enriched_manifest, f, indent=2)

    print(f"\n Output saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    detect_products_for_manifest()
