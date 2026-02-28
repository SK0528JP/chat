import os
import json
import hashlib
import requests
from datetime import datetime

# 環境変数
GH_TOKEN = os.getenv('GH_TOKEN')
GIST_ID = os.getenv('GIST_ID')
SALT = os.getenv('SECRET_SALT')
# Actionsから渡されるJSONデータ
PAYLOAD = json.loads(os.getenv('PAYLOAD'))

HEADERS = {"Authorization": f"token {GH_TOKEN}"}

def generate_trip(name_pass):
    if '#' in name_pass:
        name, password = name_pass.split('#', 1)
    else:
        name, password = name_pass, ""
    
    # トリップ生成
    trip_key = (password + SALT).encode()
    trip = "◆" + hashlib.sha256(trip_key).hexdigest()[:8]
    return name, trip

def get_gist_content():
    url = f"https://api.github.com/gists/{GIST_ID}"
    res = requests.get(url, headers=HEADERS).json()
    # rooms.json というファイル名で管理していると仮定
    content = res['files']['rooms.json']['content']
    return json.loads(content)

def update_gist_content(data):
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "rooms.json": {
                "content": json.dumps(data, ensure_ascii=False, indent=2)
            }
        }
    }
    requests.patch(url, headers=HEADERS, json=payload)

def main():
    action = PAYLOAD.get('action')
    room_uuid = PAYLOAD.get('room_uuid')
    name_pass = PAYLOAD.get('name_pass')
    message = PAYLOAD.get('message', '')
    client_time = PAYLOAD.get('time')

    name, trip = generate_trip(name_pass)
    full_user = f"{name} {trip}"
    
    db = get_gist_content()

    # 1. 投稿 & ルーム生成
    if action == "post":
        if room_uuid not in db:
            # 新規ルーム作成（最初の投稿者がオーナー）
            db[room_uuid] = {
                "name": f"Room {room_uuid[:4]}",
                "owner": trip,
                "logs": []
            }
        
        # ログ追加（最大30件）
        new_post = {"t": client_time, "u": full_user, "m": message[:100]}
        db[room_uuid]["logs"].append(new_post)
        db[room_uuid]["logs"] = db[room_uuid]["logs"][-30:]

    # 2. ルーム削除（オーナーのみ）
    elif action == "delete_room":
        if room_uuid in db and db[room_uuid]["owner"] == trip:
            del db[room_uuid]

    update_gist_content(db)

if __name__ == "__main__":
    main()
