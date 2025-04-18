from flask import Flask, jsonify
from logic.checker import check_new_posts

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"message": "PTT Info API is running."})

@app.route("/check")
def check():
    result = check_new_posts()
    return jsonify({"status": "done", "new_posts": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
