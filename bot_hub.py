import discord
from discord.ext import commands
import sqlite3
import asyncio

# ===== 봇 기본 설정 =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SQLite 연결 =====
conn = sqlite3.connect("raid.db", check_same_thread=False)
cursor = conn.cursor()

# ===== DB 초기화 =====
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raid_info (
        id INTEGER PRIMARY KEY,
        schedule TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        user_id INTEGER PRIMARY KEY,
        name TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS standby (
        user_id INTEGER PRIMARY KEY,
        name TEXT
    )
    """)
    conn.commit()

# ===== 유틸 함수 =====
def get_schedule():
    cursor.execute("SELECT schedule FROM raid_info")
    row = cursor.fetchone()
    return row[0] if row else None

def get_participants():
    cursor.execute("SELECT name FROM participants")
    return [r[0] for r in cursor.fetchall()]

def get_standby():
    cursor.execute("SELECT name FROM standby")
    return [r[0] for r in cursor.fetchall()]

def is_raid_complete():
    return get_schedule() is not None and len(get_participants()) == 8

# ===== 이벤트 =====
@bot.event
async def on_ready():
    init_db()
    print(f"봇 로그인 완료: {bot.user}")

# ===== 일정 =====
@bot.command()
@commands.has_permissions(administrator=True)
async def 일정추가(ctx, *, text):
    cursor.execute("DELETE FROM raid_info")
    cursor.execute("INSERT INTO raid_info (schedule) VALUES (?)", (text,))
    conn.commit()
    await ctx.send("📅 레이드 일정이 등록되었습니다.")

@bot.command()
async def 일정(ctx):
    schedule = get_schedule()
    await ctx.send(f"📅 레이드 일정: {schedule}" if schedule else "등록된 일정이 없습니다.")

@bot.command()
@commands.has_permissions(administrator=True)
async def 일정삭제(ctx):
    cursor.execute("DELETE FROM raid_info")
    conn.commit()
    await ctx.send("📅 레이드 일정이 삭제되었습니다.")

# ===== 참가 =====
@bot.command()
async def 참가(ctx):
    user_id = ctx.author.id
    name = ctx.author.display_name

    cursor.execute("SELECT COUNT(*) FROM participants")
    count = cursor.fetchone()[0]

    if count < 8:
        cursor.execute("INSERT OR IGNORE INTO participants VALUES (?, ?)", (user_id, name))
        conn.commit()
        await ctx.send(f"✅ {name} 참가 완료!")
    else:
        await ctx.send("❌ 확정 인원이 모두 찼습니다. 예비참가를 이용하세요.")

    if is_raid_complete():
        await ctx.send("📢 **레이드 인원 8명 확정 & 일정 등록 완료!**")

@bot.command()
async def 예비참가(ctx):
    user_id = ctx.author.id
    name = ctx.author.display_name

    cursor.execute("SELECT COUNT(*) FROM standby")
    count = cursor.fetchone()[0]

    if count < 2:
        cursor.execute("INSERT OR IGNORE INTO standby VALUES (?, ?)", (user_id, name))
        conn.commit()
        await ctx.send(f"🕒 {name} 예비 참가 완료!")
    else:
        await ctx.send("❌ 예비 인원이 모두 찼습니다.")

@bot.command()
async def 참가취소(ctx):
    user_id = ctx.author.id
    cursor.execute("DELETE FROM participants WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM standby WHERE user_id = ?", (user_id,))
    conn.commit()
    await ctx.send("❌ 참가/예비 참가가 취소되었습니다.")

@bot.command()
async def 인원(ctx):
    p = get_participants()
    s = get_standby()

    msg = "**✅ 참가자**\n"
    msg += "\n".join(p) if p else "없음"
    msg += "\n\n**🕒 예비 인원**\n"
    msg += "\n".join(s) if s else "없음"

    await ctx.send(msg)

# ===== 레이드 요약 =====
@bot.command()
async def 레이드(ctx):
    schedule = get_schedule()
    p = get_participants()
    s = get_standby()

    msg = "**📌 레이드 정보 요약**\n"
    msg += f"📅 일정: {schedule if schedule else '없음'}\n\n"
    msg += "**✅ 참가자**\n"
    msg += "\n".join(p) if p else "없음"
    msg += "\n\n**🕒 예비 인원**\n"
    msg += "\n".join(s) if s else "없음"

    await ctx.send(msg)

# ===== 리셋 =====
@bot.command()
@commands.has_permissions(administrator=True)
async def 리셋(ctx):
    cursor.execute("DELETE FROM raid_info")
    cursor.execute("DELETE FROM participants")
    cursor.execute("DELETE FROM standby")
    conn.commit()
    await ctx.send("♻️ 모든 레이드 데이터가 초기화되었습니다.")

# ===== 청소 =====
@bot.command()
@commands.has_permissions(manage_messages=True)
async def 청소(ctx):
    await ctx.channel.purge(limit=20)
    await ctx.send("🧹 최근 메시지 20개 삭제 완료", delete_after=3)

# ===== 링크 =====
@bot.command()
async def 디시(ctx):
    await ctx.send("📌 디시인사이드 아이온2 갤러리\n👉 https://gall.dcinside.com/mgallery/board/lists/?id=aion2")

@bot.command()
async def 아툴(ctx):
    await ctx.send("🛠 AION2 Tool\n👉 https://aion2.tool.com")

# ===== 도움말 =====
@bot.command()
async def 도움말(ctx):
    await ctx.send(
        "**📖 레이드 봇 명령어 안내**\n\n"
        "!일정추가 (관리자) - 레이드 일정 등록\n"
        "!일정 - 일정 확인\n"
        "!일정삭제 (관리자) - 일정 삭제\n"
        "!참가 - 레이드 참가\n"
        "!예비참가 - 예비 인원 등록\n"
        "!참가취소 - 참가 취소\n"
        "!인원 - 참가자 목록\n"
        "!레이드 - 레이드 전체 요약\n"
        "!리셋 (관리자) - 전체 초기화\n"
        "!청소 - 최근 20개 메시지 삭제\n"
        "!디시 - 아이온2 갤러리\n"
        "!아툴 - AION2 툴 사이트"
    )

# ===== 봇 실행 =====
bot.run("YOUR_DISCORD_BOT_TOKEN")
