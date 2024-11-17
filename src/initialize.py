import json
import os

# 初期化するファイルのリストと初期データ
files_and_data = {
    "matching_standby.json": [],
    "matching_room.json": {},
    # "user_data.json": {}
}

# ファイルを初期化
for filename, initial_data in files_and_data.items():
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            json.dump(initial_data, file, ensure_ascii=False, indent=4)
        print(f"{filename} を初期化しました。")
    else:
        print(f"{filename} は既に存在します。")

print("JSONファイルの初期化が完了しました。")
