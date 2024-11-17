import discord
import json
import numpy as np
import random
from discord.ext import commands

# 必要なintentsを有効化
intents = discord.Intents.default()
intents.messages = True  # メッセージ関連のイベントを有効化
intents.message_content = True
intents.members = True

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

# user_dataがない人のuser_dataを作成する関数
def ensure_user_data(user_id, default_rating=DEFAULT_RATING):
    """
    指定されたユーザーIDがuser_dataに存在しない場合、初期データを作成する。
    
    Args:
        user_id (str): 確認するユーザーID。
        user_data (dict): ユーザーデータの辞書。
        default_rating (int, optional): 初期レート。
    """
    
    if user_id not in user_data:
        user_data[user_id] = {
            "rating": default_rating,
            "ban_stages": [],
            "current_opponent": None  # current_opponentの初期値も追加
        }
        save_data()

# matching_roomの相手を見つけ出す関数
def get_opponent(user_id, room_data):
    # ユーザーが含まれるマッチを検索し、見つからなかった場合はNoneを返す
    match_info = next((match for match in room_data.values() if user_id in match["players"]), None)
    if match_info:
        opponent = match_info["players"][1] if match_info["players"][0] == user_id else match_info["players"][0]
        print(f"User ID: {user_id}, Opponent found: {opponent}")
        return opponent
    print(f"User ID: {user_id} has no match found.")
    return None

# マッチングルームを消す関数
def delete_matching_room(room_data, user_id):
    # ユーザーが参加しているマッチを見つける
    match_id = next((match_id for match_id, match in room_data.items() if user_id in match["players"]), None)
    
    # マッチが見つかった場合は削除
    if match_id is not None:
        del room_data[match_id]
        with open("matching_room.json", "w") as file:
            json.dump(room_data, file, ensure_ascii=False, indent=4)
        print(f"マッチングルーム {match_id} が削除されました。")
    else:
        print(f"ユーザー {user_id} が参加しているマッチングルームは見つかりませんでした。")


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
    ensure_user_data(user_id)
    ensure_user_data(winner_id)

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

    # 直近の対戦相手に設定（連戦回避のため）
    user_data[user_id]["current_opponent"] = winner_id
    user_data[winner_id]["current_opponent"] = user_id

    save_data()

    with open("matching_room.json", "r") as file:
        room_data = json.load(file)
    
    delete_matching_room(room_data, user_id)

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

    ensure_user_data(user_id)
    
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

@bot.command(help="拒否ステージを2つまで設定します。新しく設定すると、前の設定を上書きします。")
async def ban_stage(ctx, stage1: str = None, stage2: str = None):
    user_id = str(ctx.author.id)

    ensure_user_data(user_id)

    valid_stages = {"終点", "戦場", "ポケモンスタジアム2", "村と街", "小戦場", "ホロウバスティオン", "すま村"}

    if stage1 and stage1 not in valid_stages:
        await ctx.send(f"invalid stage: {stage1}")
        return
    if stage2 and stage2 not in valid_stages:
        await ctx.send(f"invalid stage: {stage2}")
        return

    if stage1 and stage2:
        user_data[user_id]["ban_stages"] = [stage1, stage2]
        await ctx.send(f'The rejection stages for {ctx.author.display_name} : **{stage1}** and **{stage2}**')
    elif stage1:
        user_data[user_id]["ban_stages"] = [stage1]
        await ctx.send(f'The rejection stages for {ctx.author.display_name} : **{stage1}**')
    else:
        user_data[user_id]["ban_stages"] = []
        await ctx.send(f"{ctx.author.display_name} rejection stage has been removed.")

    save_data()

@bot.command(help="マッチング待機リストに参加し、条件が合えばマッチングを行います。")
async def match(ctx):
    user_id = str(ctx.author.id)
    ensure_user_data(user_id)

    # JSONファイルを読み込む
    with open("matching_standby.json", "r") as file:
        standby_data = json.load(file)

    with open("matching_room.json", "r") as file:
        room_data = json.load(file)

    with open("user_data.json", "r") as file:
        user_data = json.load(file)

    # マッチング中であるか確認
    if any(user_id in match["players"] for match in room_data.values()):
        match_info = next(match for match in room_data.values() if user_id in match["players"])
        await ctx.send(f"あなたは既にマッチング中です!")
        opponent_id = get_opponent(user_id, room_data)
        await ctx.send(f"matching info\n<@{user_id}>: rating: {user_data[user_id]['rating']}, ban stages: {', '.join(user_data[user_id]['ban_stages'])}\n<@{opponent_id}>: rating: {user_data[opponent_id]['rating']}, ban stages: {', '.join(user_data[opponent_id]['ban_stages'])}")
        return

    # マッチング待機リストに追加
    if user_id not in standby_data:
        standby_data.append(user_id)
        with open("matching_standby.json", "w") as file:
            json.dump(standby_data, file)
        await ctx.send("マッチング待機リストに追加されました。")

    # 他の待機中ユーザーを探す
    for opponent_id in standby_data:
        if opponent_id != user_id and user_data[opponent_id]["current_opponent"] != user_id:
            # マッチング作成
            match_id = f"{user_id}_{opponent_id}"
            room_data[match_id] = {"players": [user_id, opponent_id]}

            # JSONファイルに保存
            with open("matching_room.json", "w") as file:
                json.dump(room_data, file)
            with open("user_data.json", "w") as file:
                json.dump(user_data, file)
            
            # 待機リストから削除
            standby_data.remove(user_id)
            standby_data.remove(opponent_id)
            with open("matching_standby.json", "w") as file:
                json.dump(standby_data, file)

            await ctx.send(f"<@{user_id}>と<@{opponent_id}>がマッチングしました！")
            await ctx.send(f"レート情報:\n<@{user_id}>: {user_data[user_id]['rating']}, 拒否ステージ: {', '.join(user_data[user_id]['ban_stages'])}\n<@{opponent_id}>: {user_data[opponent_id]['rating']}, 拒否ステージ: {', '.join(user_data[opponent_id]['ban_stages'])}")
            return

    await ctx.send("相手がいないか連戦になるため、マッチングできません。しばらくお待ちください。")
    role_id = 1306836218956480572
    
    await ctx.send(f"<@&{role_id}> <@{user_id}> が募集を開始しました!")

@bot.command(help="マッチングをキャンセルします。")
async def match_cancel(ctx):
    user_id = str(ctx.author.id)

    # JSONファイルを読み込む
    with open("matching_standby.json", "r") as file:
        standby_data = json.load(file)

    with open("matching_room.json", "r") as file:
        room_data = json.load(file)

    if user_id in standby_data:
        # 待機リストから削除
        standby_data.remove(user_id)
        with open("matching_standby.json", "w") as file:
            json.dump(standby_data, file)
        await ctx.send("マッチング待機リストから削除されました。")
        return

    if any(user_id in match["players"] for match in room_data.values()):
        # マッチング解消の提案
        match_id = next(match_id for match_id, match in room_data.items() if user_id in match["players"])
        if "cancel_proposals" not in room_data[match_id]:
            room_data[match_id]["cancel_proposals"] = []

        # すでに提案しているか確認
        if user_id in room_data[match_id]["cancel_proposals"]:
            opponent_id = get_opponent(user_id, room_data)
            opponent = ctx.guild.get_member(int(opponent_id))

            if opponent is not None:
                await ctx.send(f"既にマッチング解消を提案しています。 {opponent.mention} の同意をお待ちください。")
            else:
                await ctx.send(f"既にマッチング解消を提案していますが、対戦相手のユーザー情報を取得できませんでした。")
            return

        room_data[match_id]["cancel_proposals"].append(user_id)

        # 両者が提案していればマッチング解消
        if len(room_data[match_id]["cancel_proposals"]) == 2:
            opponent_id = get_opponent(user_id, room_data)
            opponent = ctx.guild.get_member(int(opponent_id))
            del room_data[match_id]
            with open("matching_room.json", "w") as file:
                json.dump(room_data, file)
            if opponent is not None:
                await ctx.send(f"<@{user_id}> と {opponent.mention} のマッチングが解消されました。")
            else:
                await ctx.send(f"<@{user_id}> のマッチングが解消されましたが、対戦相手のユーザー情報を取得できませんでした。")
        else:
            opponent_id = get_opponent(user_id, room_data)
            opponent = ctx.guild.get_member(int(opponent_id))
            with open("matching_room.json", "w") as file:
                json.dump(room_data, file)
            if opponent is not None:
                await ctx.send(f"マッチング解消の提案がされました。 {opponent.mention} の同意が必要です。")
            else:
                await ctx.send(f"マッチング解消の提案がされましたが、対戦相手のユーザー情報を取得できませんでした。")
        return

    await ctx.send("あなたは現在マッチング待機リストにもマッチングにも参加していません。")

@bot.command(help="部屋IDを登録します。マッチング待機リストで使用してください。")
async def register_room(ctx, room_id: str):
    user_id = str(ctx.author.id)

    # JSONファイルを読み込む
    with open("matching_standby.json", "r") as file:
        standby_data = json.load(file)

    # プレイヤーが待機中であるか確認
    if user_id not in standby_data:
        await ctx.send("あなたは現在マッチング待機リストにいません。")
        return

    # 部屋IDを登録または更新
    standby_data[user_id]["room_id"] = room_id
    with open("matching_standby.json", "w") as file:
        json.dump(standby_data, file, ensure_ascii=False, indent=4)

    await ctx.send(f"部屋ID「{room_id}」を登録しました。")

# Botのトークンを貼り付けて実行
bot.run('MTMwNjU5NjI2Mjc5OTM0Nzc1NA.GddhUx.c8tIlb42xdI90LpAuqUpm6GeoWzdeLLzO4SsBg')
