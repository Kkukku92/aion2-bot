import discord
from discord.ext import commands
import json
import os
from discord.ui import View, Button

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

@bot.command()
async def 아툴(ctx):
    await ctx.send("🛠 AION2 Tool\n👉 https://aion2.tool.com")

# ======================
# !투표
# ======================

class VoteView(View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.votes = {opt: [] for opt in options}

        for opt in options:
            self.add_item(VoteButton(opt, self))

class VoteButton(Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        # 중복 투표 방지
        for voters in self.view_ref.votes.values():
            if user.id in voters:
                await interaction.response.send_message(
                    "이미 투표했습니다.", ephemeral=True
                )
                return

        self.view_ref.votes[self.label].append(user.id)

        result = "\n".join(
            f"{k}: {len(v)}표" for k, v in self.view_ref.votes.items()
        )

        await interaction.response.edit_message(
            content=f"📊 **투표 진행 중**\n\n{result}",
            view=self.view_ref
        )

@bot.command()
async def 투표(ctx, question, *options):
    if len(options) < 2:
        await ctx.send("선택지는 최소 2개 이상이어야 합니다.")
        return

    view = VoteView(options)
    result = "\n".join(f"{opt}: 0표" for opt in options)

    await ctx.send(
        f"📊 **투표: {question}**\n\n{result}",
        view=view
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
!아툴 - AION2 툴 사이트

※ 확정 8명 + 일정 등록 시 자동 공지됩니다.
""")

# ======================
# 봇 실행
# ======================
bot.run(os.getenv("DISCORD_TOKEN"))
