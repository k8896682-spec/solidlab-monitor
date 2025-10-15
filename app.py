# 2025-10-08 UI FIX TEST COMMENT
from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime, timezone
import logging
import os # osモジュールを追加

# ロギング設定を修正: ファイル名のみを指定し、絶対パスの使用を避ける
# Renderはカレントディレクトリ（/opt/render/project/src）にファイルを生成します。
LOG_FILE_PATH = os.path.join(os.getcwd(), 'app.log') 

logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

app = Flask(__name__)

# 機器番号とThingspeakの情報をマッピングする辞書
device_mapping = {
    "device_A1": {
        "channel_id": "2984916",
        "read_api_key": "H8F1OIM9U1NLQE3M"
    },
    "device_B2": {
        "channel_id": "2874643",
        "read_api_key": "3L8GCQ6QQRJD9R2R"
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    logging.info("Request received for get_data (COMMUNICATION TEST MODE).")
    device_id = request.args.get('device_id', '')

    if device_id not in device_mapping:
        logging.error(f"Invalid device ID received: {device_id}")
        return jsonify({"error": "Invalid device ID"}), 404

    device_info = device_mapping[device_id]
    channel_id = device_info["channel_id"]
    read_api_key = device_info["read_api_key"]

    try:
        logging.info(f"Starting request to ThingSpeak for channel {channel_id}.")
        url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results=20"
        
        logging.info(f"Fetching URL: {url}")
        
        # ThingSpeakに接続を試みる
        response = requests.get(url, timeout=10)
        
        # レスポンス受信直後にログを記録
        logging.info(f"Received response with status code: {response.status_code}")
        
        # HTTPステータスコードを直接返す (通信テスト結果)
        if response.status_code == 200:
            # 正常な通信が確認できた場合、データを処理
            data = response.json()
            feeds = data.get('feeds', [])
            
            # --- 処理ロジック (簡略化) ---
            if not feeds:
                status_text = "データなし (通信OK)"
            else:
                status_text = f"通信成功 (コード: 200) - データ数: {len(feeds)}"
                
            latest_feed = feeds[-1] if feeds else {}
            
            # グラフ用のデータ処理 (簡略化)
            graph_labels = [datetime.strptime(f['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M") for f in feeds if f.get('field1') is not None]
            graph_data = [float(f['field1']) for f in feeds if f.get('field1') is not None]

            return jsonify({
                "temperature": latest_feed.get('field1', 'N/A'),
                "status": status_text,
                "count": latest_feed.get('field3', 'N/A'),
                "graph_labels": graph_labels,
                "graph_data": graph_data
            })
        else:
            # 200以外のステータスコードが返された場合 (404, 403など)
            return jsonify({
                "temperature": "N/A",
                "status": f"通信失敗 (コード: {response.status_code})",
                "count": "N/A",
                "graph_labels": [],
                "graph_data": []
            })

    except requests.exceptions.Timeout as e:
        # タイムアウトエラー
        logging.error(f"Thingspeak API request timed out for device {device_id}: {e}")
        return jsonify({
            "error": "TIMEOUT - ThingSpeakからの応答なし",
            "temperature": "TIMEOUT",
            "status": "通信タイムアウト",
            "count": "N/A",
            "graph_labels": [],
            "graph_data": []
        })
    except requests.exceptions.RequestException as e:
        # その他のネットワークエラー
        logging.error(f"Failed to fetch data from ThingSpeak for device {device_id}: {e}")
        return jsonify({
            "error": f"NETWORK ERROR - {e}",
            "temperature": "NETWORK ERROR",
            "status": "ネットワークエラー",
            "count": "N/A",
            "graph_labels": [],
            "graph_data": []
        })

if __name__ == '__main__':
    # RenderではGunicornが起動するため、pass のままにしておく
    pass