from flask import Flask, request, jsonify, send_file
from app.routes import product_bp


app = Flask(__name__)
app.register_blueprint(product_bp)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/Flight Risk.mp4")
def serve_flight_clip():
    return send_file("videos/Flight Risk.mp4")

@app.route("/Friends.mp4")
def serve_friends():
    return send_file("videos/Friends.mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)