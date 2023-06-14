import discord
import datetime
from datetime import datetime, timezone, timedelta
from pytz import timezone
import requests
from discord.ext import commands
from bs4 import BeautifulSoup
import asyncio

#환경변수
TOKEN = "MTExNTY5NDc0NDY4OTk3MTI5Mg.GQWWYg.Dl1789waz61VwLkY9VK-ieWkw9Y-fxHeTJnwg0"
GUILD_ID = 1115695314955931679
CHANNEL_ID = "notice"
MAPLESTORY_URL = "https://maplestory.nexon.com/News/Notice"
URS_START_HOUR = 4 #utc 기준
URS_END_HOUR = 13
player_records = {}

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True  # message_content intent 추가
bot = commands.Bot(command_prefix="~", intents=intents, case_insensitive=True)

#현재시간
KST = timezone('Asia/Seoul')
now = datetime.utcnow().astimezone(KST)


@bot.event
async def on_ready(): #봇 준비 명령어
    print("check")
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game("~도움말로 명령어를 알려드려요!"), status=discord.Status.dnd)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    await channel.send(f"Init! Bot is Started!")
    #await schedule_tasks()#스케줄 태스크 시작
    bot.loop.create_task(schedule_tasks())
    bot.loop.create_task(schedule_tasks2())
    bot.loop.create_task(schedule_tasks3())
    #bot.loop.create_task(maple_task())

#스케줄 시작
async def schedule_tasks():
    print("start")
    urs_start_time = datetime(now.year, now.month, now.day, URS_START_HOUR).astimezone(KST) #각종 변수 세팅
    urs_end_time = datetime(now.year, now.month, now.day, URS_END_HOUR).astimezone(KST)
    if now.hour >= URS_END_HOUR:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        urs_start_time += timedelta(days=1)
        urs_end_time += timedelta(days=1)
    time_until_urs_start = urs_start_time - now
    
    seconds_until_urs_start = int(time_until_urs_start.total_seconds())

    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
    stemp = f"{now.strftime('%Y-%m-%d %X')}"
    await channel.send(f"최초타임스탬프 {stemp}")
    await channel.send("Task1 Urs")
    await channel.send(f"우르스 시작시간 {urs_start_time.strftime('%Y-%m-%d %X')}")
    await channel.send(f"우르스 종료시간 {urs_end_time.strftime('%Y-%m-%d %X')}")
    await urs_start_task(seconds_until_urs_start)
    await urs_end_task()

#우르스 시작
async def urs_start_task(seconds_until_urs_start):

    await asyncio.sleep(seconds_until_urs_start)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
   # await channel.send(f"탸임스탬프 {time}")
    await channel.send(f"우르스 2배 이벤트 시작했어! 메소 벌러 가야지~")

    await urs_end_task()

async def urs_end_task():#우르스 끝나는 데스크
    urs_end_time = datetime(now.year, now.month, now.day, URS_END_HOUR)
    if now.hour >= URS_END_HOUR:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        urs_end_time += timedelta(days=1)
    time_until_urs_end = urs_end_time - now
    seconds_until_urs_end = int(time_until_urs_end.total_seconds())
    await asyncio.sleep(seconds_until_urs_end)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    await channel.send(f"우르스 2배 이벤트 끝났어.. 다음을 기약하자!")


async def schedule_tasks3():
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    time = datetime.utcnow().astimezone(KST)
    
    await channel.send("Task3 Timestamp")
    await channel.send(f"타임스탬프 시작{time.strftime('%Y-%m-%d %X')}")
    await timeStamp(3600)

async def timeStamp(time):
    await asyncio.sleep(time)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    t = datetime.utcnow().astimezone(KST)
    await channel.send(f"디버깅 타임스탬프 {t.strftime('%Y-%m-%d %X')}")
    await timeStamp(time)
async def schedule_tasks2():
    bot.loop.create_task(maple_task())

    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    await channel.send("Task2 Notice")
    next_urs_start_time = datetime(now.year, now.month, now.day, URS_START_HOUR).astimezone(KST)
    if now > next_urs_start_time:
        next_urs_start_time += timedelta(days=1)
    time_until_urs_start = next_urs_start_time - now
    seconds_until_urs_start = int(time_until_urs_start.total_seconds())

    await urs_start_task(seconds_until_urs_start)

async def maple_task(): #메이플 공지 알림
    await bot.wait_until_ready()

    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    await channel.send(f"공지체크")
    while not bot.is_closed():
        try:
            response = requests.get(MAPLESTORY_URL)
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, "html.parser")
                notices = soup.select(".list_board a")
                if notices:
                    latest_notice = notices[0]
                    notice_title = latest_notice.text
                    notice_link = latest_notice.get("href")

                    message = f"새로운 공지가 올라왔어!\n{notice_title}\n{notice_link}"
                    await channel.send(message)
        except Exception as e:
            print(f"An error occurred while checking for notices: {str(e)}")

        await asyncio.sleep(60)  # 60초(1분)마다 체크

bot.run(TOKEN)
