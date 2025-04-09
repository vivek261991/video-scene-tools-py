import base64
from openai import OpenAI
from PIL import Image
from io import BytesIO
import yaml

# Load OpenAI API key from config.yml
def load_api_key_from_config(config_path="config.yml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("OPENAI_API_KEY")

# Load system prompt from file
def load_prompt(prompt_path="system_prompt.txt"):
    with open(prompt_path, "r") as f:
        return f.read().strip()

# Convert image to base64 for OpenAI vision API
def encode_image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Function retained for backward compatibility
def detect_products_in_image(image_path, prompt=None, api_key=None):
    if not prompt:
        prompt = load_prompt()
    if not api_key:
        api_key = load_api_key_from_config()

    client = OpenAI(api_key=api_key)
    base64_image = encode_image_to_base64(image_path)
    #print(prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return {"error": str(e)}
