import os
import json
import hashlib
import requests

# 環境変数の読み込み
GH_TOKEN = os.getenv('GH_TOKEN')
GIST_ID = os.getenv('GIST_ID')
SALT = os.getenv('SECRET_SALT')
PAYLOAD = json.loads(os.getenv('PAYLOAD'))

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def generate_trip(raw_name_pass):
    # "Name#Pass" を分割。パスワードがなければ空文字
    parts = raw_name_pass.split('#')
    name = parts[0]
    password = parts[1] if len(parts) > 1 else ""
    
    # トリップ生成 (SHA-256)
    trip_hash = hashlib.sha256((password + SALT).encode()).hexdigest()
    trip = f"◆{trip_hash[:8]}"
    return name, trip

def get_gist():
    url = f"https://api.github.com/gists/{GIST_ID}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

def update_gist(files):
    url = f"https://api.github.com/gists/{GIST_ID}"
    data = {"files": files}
    requests.patch(url, headers=HEADERS, json=data)

def main():
    action = PAYLOAD.get('action')
    name_pass = PAYLOAD.get('name_pass', 'Guest#')
    name, trip = generate_trip(name_pass)
    
    # Gistから現在のデータを取得
    gist_data = get_gist()
    # 簡易的なファイル取得ロジック (例: rooms.json)
    # 実際にはここに action ごとの分岐（post, delete_friend, leave_group等）を書く
    
    print(f"Action: {action} by {name} {trip}")
    
    # 例: メッセージ投稿時の処理 (仮)
    if action == "post":
        # ここにロジックを実装していく
        pass

if __name__ == "__main__":
    main()
