# UECsmash_mate_bot
## 概要
- discordサーバー内で運用できるスマブラ対戦用レーティングシステムです
- 現状ではローカル環境での運用を想定しています
## ディレクトリ構造
```
.
├── README.md
├── data
│   ├── matching_room.json
│   ├── matching_standby.json
│   └── user_data.json
└── src
    ├── add_current_opponent.py
    ├── bot_test.py
    ├── initialize.py
    └── main.py

3 directories, 8 files
```
## 主なコマンド
### !win (プレイヤー名)
- プレイヤー名で指定された人のレートを上昇させます
- 必ず負けた人が書き込んでください
- 上昇量は対戦した2人のレートに依存します
- 今のところ、負けてもレートが減ることはありません
### !player (プレイヤー名)
- プレイヤー名で指定された人のレートと拒否ステージ、perfを確認します
- perfはランキングを1〜100の数字に変換したものです
### !ban_stage (ステージ1、ステージ2)
- 自分の拒否ステージを2つまで登録します
- すでに登録されている場合、上書きします
- 1つだけ登録、または登録しないことも可能です
- ステージ名は正確に記入してください
### !match
- マッチングに参加します
- 連戦になる場合はマッチングされません
- 既にマッチングしている場合は情報を表示します
### !match_cancel
- マッチングへの参加をとり止めます
- マッチングしている場合、マッチングの解消を提案します（両者の提案が揃えばマッチングは解消されます）
### !room (部屋ID)
- 専用部屋を建てて部屋IDを入力します
- `!match`使用後に使用できます
- マッチング待機リストで使用すると、マッチングしたときに部屋IDが表示されます
- マッチング成立後に使用すると、部屋IDを含めたマッチングの情報が再表示されます
