# app.py
from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime, timezone

app = Flask(__name__)

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
    device_id = request.args.get('device_id', '')

    if device_id not in device_mapping:
        return jsonify({"error": "Invalid device ID"}), 404

    device_info = device_mapping[device_id]
    channel_id = device_info["channel_id"]
    read_api_key = device_info["read_api_key"]

    try:
        # 過去20件のデータを取得するように変更
        url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results=20"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        feeds = data.get('feeds', [])
        
        # データが空の場合
        if not feeds:
            return jsonify({
                "temperature": "N/A",
                "status": "0", # データなしとして停止中と見なす
                "count": "N/A",
                "graph_labels": [],
                "graph_data": []
            })

        latest_feed = feeds[-1] # 最新のデータ
        
        # タイムスタンプをチェック
        last_entry_time_str = latest_feed.get('created_at')
        if last_entry_time_str:
            last_entry_time = datetime.strptime(last_entry_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_difference_seconds = (current_time - last_entry_time).total_seconds()
            
            # 最後の更新から1分（60秒）以上経過していたら、ステータスを停止中と判断
            if time_difference_seconds > 60: 
                return jsonify({
                    "temperature": "N/A",
                    "status": "0", # 停止中を示すために"0"を返す
                    "count": latest_feed.get('field3', 'N/A'),
                    "graph_labels": [],
                    "graph_data": []
                })

        # グラフ用のデータ抽出
        graph_labels = []
        graph_temperature_data = []
        
        for feed in feeds:
            timestamp = datetime.strptime(feed['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M") # 時刻のみ抽出
            temp = feed.get('field1')
            if temp is not None:
                graph_labels.append(timestamp)
                graph_temperature_data.append(float(temp))

        field1_temp = latest_feed.get('field1', 'N/A')
        field2_status = latest_feed.get('field2', 'N/A')
        field3_count = latest_feed.get('field3', 'N/A')

        return jsonify({
            "temperature": field1_temp,
            "status": field2_status,
            "count": field3_count,
            "graph_labels": graph_labels,
            "graph_data": graph_temperature_data
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Thingspeak API error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)