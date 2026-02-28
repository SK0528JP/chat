// 設定
var GIST_RAW_URL = "https://gist.githubusercontent.com/[あなたのユーザー名]/" + GIST_ID + "/raw/rooms.json";
var REPO_API_URL = "https://api.github.com/repos/[あなたのユーザー名]/[リポジトリ名]/dispatches";
var UPDATE_INTERVAL = 10000; // 10秒

// 1. チャット受信 (GET)
function loadChat(room_uuid) {
    var xhr = new XMLHttpRequest();
    // キャッシュ回避のためにタイムスタンプを付与
    xhr.open("GET", GIST_RAW_URL + "?t=" + new Date().getTime(), true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var data = JSON.parse(xhr.responseText);
            renderMessages(data[room_uuid]);
        }
    };
    xhr.send();
}

// 2. メッセージ送信 (POST via GitHub API)
function sendMessage() {
    var namePass = document.getElementById('u').value; // Name#Pass
    var msg = document.getElementById('m').value;
    var room = getQueryParam('rm') || 'default-room';

    if(!namePass || !msg) { alert("入力が足りません"); return; }

    var xhr = new XMLHttpRequest();
    xhr.open("POST", REPO_API_URL, true);
    xhr.setRequestHeader("Authorization", "token [ここにトークンを入れるのは危険なのでActionsで処理しますが、テスト用なら一時的に...] ");
    xhr.setRequestHeader("Accept", "application/vnd.github.v3+json");

    var payload = JSON.stringify({
        "event_type": "chat_event",
        "client_payload": {
            "action": "post",
            "room_uuid": room,
            "name_pass": namePass,
            "message": msg,
            "time": new Date().getTime()
        }
    });

    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 204) {
                document.getElementById('m').value = ""; // 送信成功で入力欄クリア
                alert("送信中...反映まで30秒ほど待ってください");
            } else {
                alert("エラー: " + xhr.status);
            }
        }
    };
    xhr.send(payload);
}

// 3. 描画処理
function renderMessages(roomData) {
    var logDiv = document.getElementById('log');
    if (!roomData || !roomData.logs) {
        logDiv.innerHTML = "部屋が存在しません。最初の投稿で作成されます。";
        return;
    }
    var html = "";
    for (var i = 0; i < roomData.logs.length; i++) {
        var post = roomData.logs[i];
        var date = new Date(post.t);
        var timeStr = date.getHours() + ":" + ("0" + date.getMinutes()).slice(-2);
        html += "<div><small>[" + timeStr + "]</small> <b>" + post.u + "</b>: " + post.m + "</div>";
    }
    logDiv.innerHTML = html;
}

// URLパラメータ取得用
function getQueryParam(name) {
    var reg = new RegExp('[?&]' + name + '=([^&]*)');
    var res = window.location.search.match(reg);
    return res ? res[1] : null;
}
