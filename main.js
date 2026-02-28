/**
 * 3DS Discord Lite - Core Logic
 * ユーザー名、リポジトリ名、Gist IDを自分のものに書き換えてデプロイしてください。
 */

// --- 接続設定 ---
var GH_USER = "SK0528JP";
var GH_REPO = "chat";
var GIST_ID = "a325011b0c2805409957d4579e1160bd";
var GIST_RAW = "https://gist.githubusercontent.com/" + GH_USER + "/" + GIST_ID + "/raw/rooms.json";

// --- グローバル状態 ---
var currentRoom = "lobby"; // 現在表示中のUUID
var updateTimer = null;

/**
 * 1. ルーム一覧の取得と描画
 */
function loadRoomList() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", GIST_RAW + "?t=" + new Date().getTime(), true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var db = JSON.parse(xhr.responseText);
            var html = "";
            for (var id in db) {
                if (id === "users") continue; // ユーザーデータは除外
                var room = db[id];
                html += '<div class="room-item">';
                html += '<strong>' + room.name + '</strong><br>';
                html += '<button onclick="openRoom(\'' + id + '\')">入室</button> ';
                html += '</div>';
            }
            document.getElementById('room-list').innerHTML = html || "ルームがありません。";
        }
    };
    xhr.send();
}

/**
 * 2. チャットログの取得と描画
 */
function loadChat() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", GIST_RAW + "?t=" + new Date().getTime(), true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var db = JSON.parse(xhr.responseText);
            var room = db[currentRoom];
            var logDiv = document.getElementById('log');
            
            if (!room) {
                logDiv.innerHTML = "部屋が存在しません。メッセージを送ると作成されます。";
                return;
            }

            var html = "";
            for (var i = 0; i < room.logs.length; i++) {
                var p = room.logs[i];
                var d = new Date(p.t);
                var timeStr = d.getHours() + ":" + ("0" + d.getMinutes()).slice(-2);
                html += '<div class="msg">';
                html += '<span class="time">[' + timeStr + ']</span> ';
                html += '<span class="user">' + p.u + '</span>: ';
                html += '<span>' + p.m + '</span>';
                html += '</div>';
            }
            logDiv.innerHTML = html;
            // 3DSのメモリ対策として、常に最新（下）へスクロール
            logDiv.scrollTop = logDiv.scrollHeight;
        }
    };
    xhr.send();
}

/**
 * 3. アクションの送信 (POST)
 * 投稿、フレンド追加、削除、退出すべてをこの関数経由でActionsへ飛ばします
 */
function sendAction(actionType, extraData) {
    var namePass = localStorage.getItem('chat_id');
    var token = localStorage.getItem('gh_token');
    
    if (!namePass || !token) {
        alert("「設定」タブでIDとGitHubトークンを保存してください。");
        return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "https://api.github.com/repos/" + GH_USER + "/" + GH_REPO + "/dispatches", true);
    xhr.setRequestHeader("Authorization", "token " + token);
    xhr.setRequestHeader("Accept", "application/vnd.github.v3+json");

    // 基本データ構造
    var payload = {
        "event_type": "chat_event",
        "client_payload": {
            "action": actionType,
            "name_pass": namePass,
            "room_uuid": currentRoom,
            "time": new Date().getTime()
        }
    };

    // 追加データのマージ (message, target_tripなど)
    for (var key in extraData) {
        payload.client_payload[key] = extraData[key];
    }

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 204) {
                alert("リクエスト送信完了。反映まで約30秒待機。");
                if (actionType === "post") document.getElementById('msg').value = "";
            } else {
                alert("エラー: " + xhr.status + "\nトークンの権限不足か、リポジトリ名が間違っています。");
            }
        }
    };
    xhr.send(JSON.stringify(payload));
}

/**
 * 4. 各ボタンから呼ばれるインターフェース
 */

// メッセージ送信
function send() {
    var msg = document.getElementById('msg').value;
    if (!msg) return;
    sendAction("post", { "message": msg });
}

// 部屋を開く
function openRoom(id) {
    currentRoom = id;
    switchTab('chat');
}

// フレンド追加
function addFriend() {
    var fid = document.getElementById('f-id').value; // Name#Trip の Trip部分
    if (!fid) return;
    sendAction("add_friend", { "target_trip": fid });
}

// 部屋削除 (オーナーのみ)
function deleteThisRoom() {
    if (confirm("この部屋を削除しますか？(オーナーのみ有効)")) {
        sendAction("delete_room", {});
    }
}

/**
 * 5. フレンドリストの描画 (Gistのusersから取得)
 */
function renderFriends() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", GIST_RAW + "?t=" + new Date().getTime(), true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var db = JSON.parse(xhr.responseText);
            var myId = localStorage.getItem('chat_id');
            // トリップ生成ロジックはJS側でも簡易的に再現が必要だが、
            // ここでは簡易的に「users」フィールドを表示
            var listDiv = document.getElementById('friend-list');
            listDiv.innerHTML = "フレンド機能は現在同期中...";
            // TODO: 自分のトリップをキーにしてdb.usersからリストを抽出
        }
    };
    xhr.send();
}

/**
 * 6. ユーティリティ
 */
function getQueryParam(n) {
    var r = new RegExp('[?&]' + n + '=([^&]*)');
    var m = window.location.search.match(r);
    return m ? m[1] : null;
}
