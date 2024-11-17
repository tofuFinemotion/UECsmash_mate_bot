import json

# ファイル名
user_data_file = "user_data.json"

# JSONファイルを読み込む
try:
    with open(user_data_file, "r") as file:
        user_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}

# 各ユーザーに "current_opponent" を追加
for user_id, data in user_data.items():
    if "current_opponent" not in data:
        data["current_opponent"] = None  # 初期値として None を設定

# JSONファイルに保存
with open(user_data_file, "w") as file:
    json.dump(user_data, file, ensure_ascii=False, indent=4)

print(f"{user_data_file} に 'current_opponent' 項目が追加されました。")
