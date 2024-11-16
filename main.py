import discord
import json
import numpy as np
import random
from discord.ext import commands

# 必要なintentsを有効化
intents = discord.Intents.default()
intents.messages = True  # メッセージ関連のイベントを有効化
intents.message_content = True

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Botのヘルプ", description="利用可能なコマンド一覧です。", color=0x00FF00)
        for cog, commands in mapping.items():
            filtered_commands = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered_commands]
            if command_signatures:
                cog_name = cog.qualified_name if cog else "その他"
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

# Botのインスタンスを作成
bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザーのレートを管理する辞書
user_data = {}

# 初期レートを設定
DEFAULT_RATING = 0.0

# ファイル名
data_file = "./user_data.json"

# データを読み込む関数
def load_data():
    global user_data
    try:
        with open(data_file, "r") as file:
            user_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}

# データを保存する関数
def save_data():
    with open(data_file, "w") as file:
        json.dump(user_data, file, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    load_data()  # Bot起動時にレートを読み込む
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.command(help="おみくじを引いて運勢を占います。")
async def omikuji(ctx):
    fortunes = [
        "大吉 - 今日はとってもラッキー！",
        "中吉 - まずまずの運勢！",
        "小吉 - 少し良いことがあるかも？",
        "吉 - 平穏な一日になりそう。",
        "末吉 - ちょっとした幸運に恵まれるかも。",
        "凶 - 気をつけて過ごしてね。",
        "大凶 - 今日は慎重に行動しよう。"
    ]

    result = random.choice(fortunes)
    await ctx.send(f"{ctx.author.mention}の運勢は… {result}")

@bot.command(help = "負けた人が勝った人を入力し、勝った人のレートを上昇させます。必ず負けた人が入力してください！")
async def win(ctx, winner: discord.Member):
    
    print(f'コマンド受信: {ctx.message.content}')
    # ここで受け取ったメンバー情報を確認
    print(f'勝者: {winner.display_name}')

    # Bot自身を指定できないようにする
    if winner.bot:
        await ctx.send('You cannot designate a bot as a winner!')
        return
    
    # コマンドを実行したユーザー自身を勝者に指定できないようにする
    if winner.id == ctx.author.id:
        await ctx.send('You cannot designate yourself as a winner!')
        return

    # 入力したユーザーと勝者のIDを取得
    winner_id = str(winner.id)
    user_id = str(ctx.author.id)

    # ユーザーと勝者のデータがなければ初期データを作成
    if user_id not in user_data:
        user_data[user_id] = {"rating": DEFAULT_RATING, "ban_stages": []}
    if winner_id not in user_data:
        user_data[winner_id] = {"rating": DEFAULT_RATING, "ban_stages": []}

    # レート上昇値を計算
    threshold = 1.0
    difference = user_data[user_id]["rating"] - user_data[winner_id]["rating"]
    if difference >= threshold:
        increase = np.sqrt(difference)
    else:
        increase = threshold

    increase = round(increase, 1)

    # 勝者のレートを更新
    user_data[winner_id]["rating"] += increase

    save_data()

    # 出力メッセージ
    await ctx.send(f'rating information\n player:{winner.display_name}\n rating:{user_data[winner_id]["rating"]} (+{increase})')

@bot.command(help = "プレイヤーを指定してレートと拒否ステージを確認できます。")
async def player(ctx, member: discord.Member = None):
    # 引数が指定されていない場合はコマンド発行者を対象にする
    if member is None:
        member = ctx.author

    # Botが指定された場合はメッセージを返して終了
    if member.bot:
        await ctx.send("Botを対象にすることはできません。")
        return

    user_id = str(member.id)

    if user_id not in user_data:
        user_data[user_id] = {"rating": DEFAULT_RATING, "ban_stages": []}
        save_data()  # 新しいユーザーなら保存
    
    # レートとperfを計算
    ban_stages = user_data[user_id]["ban_stages"]
    user_rating = user_data[user_id]["rating"]

    # 全てのユーザーのレートを`rating`を基にソート
    all_ratings = sorted(user_data.items(), key=lambda item: item[1]["rating"], reverse=True)

    # プレイヤーのランキングを計算（同率の場合は同じ順位を付ける）
    rank_dict = {}
    current_rank = 1
    for i, (uid, data) in enumerate(all_ratings):
        if i > 0 and data["rating"] != all_ratings[i - 1][1]["rating"]:
            current_rank = i + 1
        rank_dict[uid] = current_rank

    rank = rank_dict.get(user_id)
    total_players = len(all_ratings)

    # perfの計算
    perf = int(((total_players - rank) / (total_players - 1)) * 99 + 1) if total_players > 1 else 100
    
    # perfに応じてEmbedの色を設定
    color = 0xFFFF00 if perf >= 100 else 0xFFC0CB if perf >= 99 else 0xFFA500 if perf >= 95 else 0x800080 if perf >= 75 else 0x0000FF if perf >= 50 else 0x00FF00 if perf >= 25 else 0x808080
    
    embed = discord.Embed(
        title="player information",
        description = f"name: {member.display_name}\nrating: {user_rating}\nban stages: {', '.join(ban_stages) if ban_stages else 'no ban'}\nperf: {perf}",
        color=color
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def ban_stage(ctx, stage1: str = None, stage2: str = None):
    user_id = str(ctx.author.id)

    if user_id not in user_data:
        user_data[user_id] = {"rating": DEFAULT_RATING, "ban_stages": []}

    valid_stages = {"終点", "戦場", "ポケモンスタジアム2", "村と街", "小戦場", "ホロウバスティオン", "すま村"}

    if stage1 and stage1 not in valid_stages:
        await ctx.send(f"invalid stage: {stage1}")
        return
    if stage2 and stage2 not in valid_stages:
        await ctx.send(f"invalid stage: {stage2}")
        return

    if stage1 and stage2:
        user_data[user_id]["ban_stages"] = [stage1, stage2]
        await ctx.send(f'The rejection stages for {ctx.author.display_name} have been registered for {stage1} and {stage2}.')
    elif stage1:
        user_data[user_id]["ban_stages"] = [stage1]
        await ctx.send(f'The rejection stages for {ctx.author.display_name} have been registered for {stage1}')
    else:
        user_data[user_id]["ban_stages"] = []
        await ctx.send(f"{ctx.author.display_name} rejection stage has been removed.")

    save_data()

# Botのトークンを貼り付けて実行
bot.run(DISCORD_BOT_TOKEN)
