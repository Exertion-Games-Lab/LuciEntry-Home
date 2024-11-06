from flask import Flask, jsonify
import random
import time
from threading import Thread

app = Flask(__name__)

# 模擬的 REM 狀態
rem_state = {"state": "Not_REM_PERIOD"}

def update_rem_state():
    # 每秒隨機更改 REM 狀態
    while True:
        rem_state["state"] = random.choice(["REM_PERIOD", "Not_REM_PERIOD"])
        print("Current REM state:", rem_state["state"])  # 在伺服器端顯示當前狀態
        time.sleep(1)

@app.route('/get_rem', methods=['GET'])
def get_rem():
    return jsonify(rem_state), 200

if __name__ == "__main__":
    # 啟動 Flask 伺服器
    thread = Thread(target=update_rem_state)
    thread.start()
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)
