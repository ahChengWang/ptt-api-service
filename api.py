from flask import Flask, jsonify
from logic.checker import checker
# from logic.airTicketBot import airTicketBot


app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "PTT Info API is running."})


# @app.route("/menu")
# def check():
#     print("📜功能列表")
#     check = checker()
#     result = check.check_new_posts()
#     return jsonify({"status": "done", "new_posts": result})


@app.route("/check")
def check():
    print("⏱ 查詢最新省錢版文章 ")
    check = checker()
    result = check.check_new_posts()
    return jsonify({"status": "done", "new_posts": result})


# @app.route("/loc")
# def locations():
#     print("取得出發地")
#     tb = airTicketBot()
#     result = tb.start_loc()
#     return jsonify({"status": "sent", "result": result.json()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
