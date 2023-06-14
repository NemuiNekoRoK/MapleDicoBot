import discord
import datetime
from datetime import datetime, timezone, timedelta
from pytz import timezone
import requests
from discord.ext import commands
from bs4 import BeautifulSoup
import asyncio

#환경변수
TOKEN = open("DiscordToken.txt", "r").readline()
GUILD_ID = 1115695314955931679
CHANNEL_ID = "notice"
MAPLESTORY_URL = "https://maplestory.nexon.com/News/Notice"
URS_START_HOUR = 4 #utc 기준
URS_END_HOUR = 13
RESET_ALTER_HOUR_CONTENT = 14
RESET_ALTER_HOUR_BOSS = 11

#알림텍스트 
URS_START = "우르스 2배 이벤트 시작"
URS_END = "우르스 2배이벤트 종료"
CONTENT_RESET_DAILY = "오후 11시입니다. 일일컨텐츠를 확인해 주세요\n1. 마일리지 적립\n2. 몬컬보상\n3. 기여도 보스\n4. 길드 출석\n5. 몬파\n6. 황금마차\n7. 일일퀘스트\n8. 이벤트퀘스트\n9.무릉포인트수령"
CONTENT_RESET_WEEKLY = "일요일 오후 11시입니다. 주간 컨텐츠를 확인해 주세요"
BOSS_RESET = "수요일 오후 8시입니다. 초기화 전 주간보스를 확인해 주세요"
NEW_ALTER = "새로운 공지가 올라왔습니다."


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
    print(f"토큰체크{TOKEN}")
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game("~도움말로 명령어를 알려드려요!"), status=discord.Status.dnd)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    await channel.send(f"Init! Bot is Started!")
    #await schedule_tasks()#스케줄 태스크 시작
    bot.loop.create_task(task_urs())
    bot.loop.create_task(noticeTask())
    bot.loop.create_task(task_daily_content())
    bot.loop.create_task(task_weekly_content())
    bot.loop.create_task(debugTask())
    #bot.loop.create_task(maple_task())

#----------------------------------------
#               우르스 알림
#----------------------------------------
async def task_urs():
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
    await channel.send(f"{URS_START}")

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
    await channel.send(f"{URS_END}")
    
#------------------------------------------------
#                  공지 알림
#------------------------------------------------
async def noticeTask():
    bot.loop.create_task(maple_task())

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

#-------------------------------------
#             일일컨텐츠
#-------------------------------------
async def task_daily_content():
    start_time = datetime(now.year, now.month, now.day, RESET_ALTER_HOUR_CONTENT).astimezone(KST) #각종 변수 세팅
    if now.hour >= RESET_ALTER_HOUR_CONTENT:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
    
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
   # await channel.send(f"탸임스탬프 {time}")
    await channel.send(f"check : {CONTENT_RESET_DAILY}")
        
    time_until_start = start_time - now
    
    seconds_until_start = int(time_until_start.total_seconds())
    await daily_start_task(seconds_until_start)

async def daily_start_task(seconds_until_start):

    await asyncio.sleep(seconds_until_start)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
   # await channel.send(f"탸임스탬프 {time}")
    await channel.send(f"{CONTENT_RESET_DAILY}")

    
#-------------------------------------
#             주간보스
#-------------------------------------
async def task_weekly_content():
    start_time = datetime(now.year, now.month, now.day, RESET_ALTER_HOUR_BOSS).astimezone(KST) #각종 변수 세팅
    if now.hour >= RESET_ALTER_HOUR_BOSS:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
        
    time_until_start = start_time - now
    
    seconds_until_start = int(time_until_start.total_seconds())
    await weekly_start_task(seconds_until_start)

async def weekly_start_task(seconds_until_start):
    await asyncio.sleep(seconds_until_start)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
   # await channel.send(f"탸임스탬프 {time}")
    if now.weekday() == 3: #weekday기준 수요일
        await channel.send(f"{BOSS_RESET}")

#--------------------------------------
#             디버거
#--------------------------------------
async def debugTask():
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


bot.run(TOKEN)
