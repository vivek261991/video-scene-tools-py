from flask import Flask, request, jsonify, send_file
from app.routes import product_bp


app = Flask(__name__)
app.register_blueprint(product_bp)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/clip.mp4")
def serve_clip():
    return send_file("clip.mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)