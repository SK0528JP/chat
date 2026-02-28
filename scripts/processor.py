import os
import json
import hashlib
import requests
import sys

# --- 環境設定 ---
GH_TOKEN = os.getenv('GH_TOKEN')
GIST_ID = os.getenv('GIST_ID')
SALT = os.getenv('SECRET_SALT', 'default_salt_8192')
PAYLOAD_RAW = os.getenv('PAYLOAD')

if not PAYLOAD_RAW:
    print("No payload found.")
    sys.exit(0)

PAYLOAD = json.loads(PAYLOAD_RAW)
HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- ユーティリティ関数 ---
def generate_trip(name_pass):
    """名前#パスワードからトリップを生成する"""
    if '#' in name_pass:
        name, password = name_pass.split('#', 1)
    else:
        name, password = name_pass, ""
    
    # 半角英数字のみに制限（3DS互換性のため）
    name = "".join(filter(str.isalnum, name))[:15]
    trip_hash = hashlib.sha256((password + SALT).encode()).hexdigest()
    return name, f"◆{trip_hash[:8]}"

def get_db():
    """Gistから全データを取得"""
    url = f"https://api.github.com/gists/{GIST_ID}"
    res = requests.get(url, headers=HEADERS).json()
    content = res['files']['rooms.json']['content']
    return json.loads(content)

def save_db(db):
    """Gistへデータを保存"""
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "rooms.json": {
                "content": json.dumps(db, ensure_ascii=False)
            }
        }
    }
    requests.patch(url, headers=HEADERS, json=payload)

# --- メインロジック ---
def main():
    db = get_db()
    
    action = PAYLOAD.get('action')
    room_uuid = PAYLOAD.get('room_uuid')
    name_pass = PAYLOAD.get('name_pass', 'Guest#')
    message = PAYLOAD.get('message', '')
    client_time = PAYLOAD.get('time')
    target_trip = PAYLOAD.get('target_trip') # フレンド操作用

    name, trip = generate_trip(name_pass)
    user_full = f"{name} {trip}"

    # 1. メッセージ投稿 & ルーム自動生成
    if action == "post":
        if room_uuid not in db:
            # 新規作成（最初の投稿者がオーナー）
            db[room_uuid] = {
                "name": f"Room-{room_uuid[:4]}",
                "owner": trip,
                "type": "group",
                "logs": []
            }
        
        # 投稿追加（最大20件に制限して3DSのメモリを保護）
        new_post = {"t": client_time, "u": user_full, "m": message[:100]}
        db[room_uuid]["logs"].append(new_post)
        db[room_uuid].setdefault("members", [])
        if trip not in db[room_uuid]["members"]:
            db[room_uuid]["members"].append(trip)
        
        db[room_uuid]["logs"] = db[room_uuid]["logs"][-20:]

    # 2. ルーム削除（オーナーのみ）
    elif action == "delete_room":
        if room_uuid in db and db[room_uuid].get("owner") == trip:
            del db[room_uuid]

    # 3. グループ退出
    elif action == "leave_room":
        if room_uuid in db and "members" in db[room_uuid]:
            if trip in db[room_uuid]["members"]:
                db[room_uuid]["members"].remove(trip)
            # オーナーが抜ける場合は部屋を消すか、次のメンバーに譲渡（ここでは簡易的に保持）

    # 4. フレンド機能（ユーザー個別データ）
    # db["users"] = { "trip": {"friends": ["name ◆trip"] } }
    if "users" not in db: db["users"] = {}
    if trip not in db["users"]: db["users"][trip] = {"friends": []}

    if action == "add_friend":
        if target_trip and target_trip not in db["users"][trip]["friends"]:
            db["users"][trip]["friends"].append(target_trip)

    elif action == "delete_friend":
        if target_trip in db["users"][trip]["friends"]:
            db["users"][trip]["friends"].remove(target_trip)

    save_db(db)
    print(f"Success: {action} by {user_full}")

if __name__ == "__main__":
    main()
