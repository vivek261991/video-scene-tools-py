from flask import Flask
from app.routes import product_bp

app = Flask(__name__)
app.register_blueprint(product_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)