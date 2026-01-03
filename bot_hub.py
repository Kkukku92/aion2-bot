
import discord
from discord.ext import commands
import datetime
import random
import hashlib
import json
import os
from discord.ui import View, Button
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


# ======================
# 기본 설정
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "raid_data.json"

MAX_PARTICIPANTS = 8
MAX_RESERVE = 2

# ======================
# 데이터 불러오기 / 저장
# ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "participants": [],
            "reserve": [],
            "schedule": None,
            "announced": False
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ======================
# 자동 공지 체크
# ======================
async def check_and_announce(ctx):
    if (
        len(data["participants"]) == MAX_PARTICIPANTS
        and data["schedule"] is not None
        and not data["announced"]
    ):
        msg = "📢 **레이드 확정 공지**\n\n"
        msg += f"📅 **일정**\n{data['schedule']}\n\n"
        msg += "🗡 **확정 인원**\n"

        for i, name in enumerate(data["participants"], 1):
            msg += f"{i}. {name}\n"

        await ctx.send(msg)

        data["announced"] = True
        save_data()

# ======================
# 봇 준비 완료
# ======================
@bot.event
async def on_ready():
    print(f"봇 로그인 성공: {bot.user}")

# ======================
# !참가
# ======================
@bot.command()
async def 참가(ctx):
    name = ctx.author.display_name

    if name in data["participants"] or name in data["reserve"]:
        await ctx.send("이미 참가 또는 예비로 등록되어 있습니다.")
        return

    if len(data["participants"]) < MAX_PARTICIPANTS:
        data["participants"].append(name)
        save_data()
        await ctx.send(f"✅ {name} 님이 레이드에 참가했습니다.")
        await check_and_announce(ctx)
    else:
        await ctx.send("참가 인원이 가득 찼습니다. 예비참가를 이용해주세요.")

# ======================
# !예비참가
# ======================
@bot.command()
async def 예비참가(ctx):
    name = ctx.author.display_name

    if name in data["participants"] or name in data["reserve"]:
        await ctx.send("이미 참가 또는 예비로 등록되어 있습니다.")
        return

    if len(data["reserve"]) < MAX_RESERVE:
        data["reserve"].append(name)
        save_data()
        await ctx.send(f"🕒 {name} 님이 예비 인원으로 등록되었습니다.")
    else:
        await ctx.send("예비 인원이 가득 찼습니다.")

# ======================
# !참가취소
# ======================
@bot.command()
async def 참가취소(ctx):
    name = ctx.author.display_name

    if name in data["participants"]:
        data["participants"].remove(name)

        if data["reserve"]:
            promoted = data["reserve"].pop(0)
            data["participants"].append(promoted)
            await ctx.send(
                f"{name} 님 참가 취소\n➡ {promoted} 님이 예비에서 참가로 이동했습니다."
            )
        else:
            await ctx.send(f"{name} 님 참가가 취소되었습니다.")

    elif name in data["reserve"]:
        data["reserve"].remove(name)
        await ctx.send(f"{name} 님의 예비 참가가 취소되었습니다.")
    else:
        await ctx.send("참가자 또는 예비 명단에 없습니다.")

    save_data()

# ======================
# !인원
# ======================
@bot.command()
async def 인원(ctx):
    msg = "**🗡 레이드 참가자**\n"
    msg += "\n".join(
        f"{i}. {name}" for i, name in enumerate(data["participants"], 1)
    ) if data["participants"] else "없음"

    msg += "\n\n**🕒 예비 인원**\n"
    msg += "\n".join(
        f"{i}. {name}" for i, name in enumerate(data["reserve"], 1)
    ) if data["reserve"] else "없음"

    await ctx.send(msg)

# ======================
# !일정
# ======================
@bot.command()
async def 일정(ctx):
    await ctx.send(data["schedule"] if data["schedule"] else "등록된 일정이 없습니다.")

# ======================
# !일정추가 (관리자)
# ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def 일정추가(ctx, *, schedule):
    data["schedule"] = schedule
    data["announced"] = False
    save_data()
    await ctx.send("📅 레이드 일정이 등록되었습니다.")
    await check_and_announce(ctx)

# ======================
# !일정삭제 (관리자)
# ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def 일정삭제(ctx):
    data["schedule"] = None
    data["announced"] = False
    save_data()
    await ctx.send("📅 레이드 일정이 삭제되었습니다.")

# ======================
# !레이드
# ======================
@bot.command()
async def 레이드(ctx):
    msg = "🛡 **레이드 정보 요약**\n\n"
    msg += f"📅 일정\n{data['schedule'] if data['schedule'] else '미등록'}\n\n"
    msg += f"🗡 참가 인원 ({len(data['participants'])}/{MAX_PARTICIPANTS})\n"
    msg += "\n".join(
        f"{i}. {name}" for i, name in enumerate(data["participants"], 1)
    ) if data["participants"] else "없음"

    msg += f"\n\n🕒 예비 인원 ({len(data['reserve'])}/{MAX_RESERVE})\n"
    msg += "\n".join(
        f"{i}. {name}" for i, name in enumerate(data["reserve"], 1)
    ) if data["reserve"] else "없음"

    await ctx.send(msg)

# ======================
# !청소 (관리자)
# ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def 청소(ctx):
    await ctx.channel.purge(limit=21)
    msg = await ctx.send("🧹 최근 메시지 20개를 삭제했습니다.")
    await msg.delete(delay=3)

# ======================
# !리셋 (관리자)
# ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def 리셋(ctx):
    data["participants"] = []
    data["reserve"] = []
    data["schedule"] = None
    data["announced"] = False
    save_data()
    await ctx.send("♻ 모든 레이드 데이터가 초기화되었습니다.")

# ===== 링크 =====
@bot.command()
async def 디시(ctx):
    await ctx.send("📌 디시인사이드 아이온2 갤러리\n👉 https://gall.dcinside.com/mgallery/board/lists/?id=aion2")

# ===== 아툴 =====
def get_aion2_combat_power(nickname: str):
    url = "https://aion2tool.com/api/character/search"

    payload = {
        "race": 1,
        "server_id": 1005,
        "keyword": nickname
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers, timeout=10)

    if res.status_code != 200:
        return None

    data = res.json()
    if not data.get("success"):
        return None

    return data["data"]

@bot.command()
async def 아툴(ctx, nickname: str):
    char = get_aion2_combat_power(nickname)

    if not char:
        await ctx.send("❌ 캐릭터 정보를 찾을 수 없습니다.")
        return

    embed = build_aion_embed(char)
    await ctx.send(embed=embed)

# ===== 갱신

def is_old_data(updated_at: str) -> bool:
    updated_time = datetime.fromisoformat(
        updated_at.replace("Z", "+00:00")
    )
    return datetime.utcnow() - updated_time > timedelta(hours=6)

def build_aion_embed(char: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"⚔ {char['nickname']}",
        color=0xA78BFA
    )

    embed.set_thumbnail(url=char["avatar_url"])

    embed.add_field(
        name="🔥 전투력",
        value=(
            f"**{int(char['combat_score']):,} / "
            f"{int(char['combat_score_max']):,}**"
        ),
        inline=False
    )

    embed.add_field(
        name="직업 / 서버",
        value=f"{char['job']} / {char['server']}",
        inline=True
    )

    updated_at = char["score_updated_at"]

    embed.add_field(
        name="데이터 갱신 시각",
        value=updated_at.replace("T", " ").replace("Z", ""),
        inline=False
    )

    if is_old_data(updated_at):
        embed.add_field(
            name="⚠ 주의",
            value="전투력 데이터가 오래되었을 수 있습니다.\n(Aion2Tool 기준)",
            inline=False
        )

    embed.set_footer(text="Data from aion2tool.com")

    return embed


# ======================
# !투표
# ======================

class VoteView(View):
    def __init__(self, options, author_id):
        super().__init__(timeout=None)

        self.author_id = author_id      # 투표 만든 사람
        self.closed = False             # 종료 여부

        # {옵션: {user_id: 닉네임}}
        self.votes = {opt: {} for opt in options}

        for opt in options:
            self.add_item(VoteButton(opt, self))

        # 종료 버튼 추가
        self.add_item(EndVoteButton(self))


class VoteButton(Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.closed:
            await interaction.response.send_message(
                "이미 종료된 투표입니다.",
                ephemeral=True
            )
            return

        user = interaction.user
        nickname = user.display_name

        total_votes = sum(
            user.id in voters for voters in self.view_ref.votes.values()
        )

        if total_votes >= 2:
            await interaction.response.send_message(
                "최대 2개까지만 투표할 수 있습니다.",
                ephemeral=True
            )
            return

        if user.id in self.view_ref.votes[self.label]:
            await interaction.response.send_message(
                "이 항목에는 이미 투표했습니다.",
                ephemeral=True
            )
            return

        self.view_ref.votes[self.label][user.id] = nickname

        await interaction.response.edit_message(
            content=self.make_result_text(),
            view=self.view_ref
        )

    def make_result_text(self):
        lines = []
        for opt, voters in self.view_ref.votes.items():
            if voters:
                names = ", ".join(voters.values())
                lines.append(f"**{opt}** : {len(voters)}표\n└ {names}")
            else:
                lines.append(f"**{opt}** : 0표")
        return "📊 **투표 진행 중**\n\n" + "\n".join(lines)

class EndVoteButton(Button):
    def __init__(self, view):
        super().__init__(
            label="투표 종료",
            style=discord.ButtonStyle.danger
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.author_id:
            await interaction.response.send_message(
                "투표를 만든 사람만 종료할 수 있습니다.",
                ephemeral=True
            )
            return

        self.view_ref.closed = True

        # 모든 버튼 비활성화
        for item in self.view_ref.children:
            item.disabled = True

        await interaction.response.edit_message(
            content=self.make_final_result(),
            view=self.view_ref
        )

    def make_final_result(self):
        lines = []
        for opt, voters in self.view_ref.votes.items():
            if voters:
                names = ", ".join(voters.values())
                lines.append(
                    f"**{opt}** : {len(voters)}표\n└ {names}"
                )
            else:
                lines.append(f"**{opt}** : 0표")

        return "🛑 **투표 종료! 최종 결과**\n\n" + "\n".join(lines)


@bot.command()
async def 투표(ctx, question, *options):
    if len(options) < 2:
        await ctx.send("선택지는 최소 2개 이상이어야 합니다.")
        return

    view = VoteView(options, ctx.author.id)

    result = "\n".join(f"**{opt}** : 0표" for opt in options)

    await ctx.send(
        f"📊 **투표: {question}**\n\n{result}",
        view=view
    )

# ======================
# !운세
# ======================
# ✅ 반드시 함수보다 위에
FORTUNES = [
    "오늘은 쓸모없는 곳에 키나를 소모할 예정",
    "오늘은 제작이 좆망할 예정",
    "오늘은 인던 보상이 좋을 예정",
    "오늘은 인던 보상이 안 좋을 예정",
    "오늘은 잠이나 자는 게 나을 예정",
    "오늘은 갑자기 기분이 상할 예정",
    "오늘은 운세 굳이 알려줘야 하나?",
    "오늘은 무시받을 예정",
    "오늘은 억까받을 예정",
    "오늘은 쉬었음 당할 예정",
    "오늘은 빛날 예정",
    "오늘은 카드가 잘 뜰 예정",
    "오늘은 축하받을 예정",
    "오늘은 .. 흠.....",
    "오늘은 뜻밖의 행운이 찾아올 예정",
    "오늘은 예상대로 안 흘러갈 예정",
    "오늘은 어비스 포인트 많이 받을 예정",
    "오늘은 공팟 운이 안 좋을 예정",
    "오늘은 공팟 운이 좋을 예정",
]

def get_today_fortune(user_id: int):
    today = datetime.date.today().isoformat()

    seed_str = f"{user_id}-{today}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)

    random.seed(seed)

    fortune = random.choice(FORTUNES)
    return fortune

@bot.command()
async def 운세(ctx):
    fortune = get_today_fortune(ctx.author.id)

    await ctx.send(
        f"🔮 **{ctx.author.display_name}님의 오늘의 운세**\n\n"
        f"✨ {fortune}"
    )


# ======================
# !도움말
# ======================
@bot.command()
async def 도움말(ctx):
    await ctx.send("""
📖 **레이드 봇 명령어 안내**

!레이드 - 레이드 전체 정보 요약

[참가]
!참가 - 레이드 참가
!예비참가 - 참가가 확실치 않을때 예비 인원 등록
!참가취소 - 참가 / 예비 취소
!인원 - 참가자 목록 확인

[일정]
!일정 - 레이드 일정 확인
!일정추가 [내용] - 일정 등록 (관리자)
!일정삭제 - 일정 삭제 (관리자)

[관리]
!청소 - 채팅 삭제 (관리자)

[유틸]
!디시 - 아이온2 갤러리
!아툴 닉네임 - 자신의 아툴 전투력 검색 (현재유스티엘서버만가능)
!운세 - 운세

※ 확정 8명 + 일정 등록 시 자동 공지됩니다.
""")

# ======================
# 봇 실행
# ======================
bot.run(os.getenv("DISCORD_TOKEN"))

