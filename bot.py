import discord
import datetime
from datetime import datetime, timezone, timedelta
from pytz import timezone
import requests
from discord.ext import commands
from bs4 import BeautifulSoup
import asyncio

#환경변수
TOKEN = open("Token", "r").readline()
GUILD_ID = 1115695314955931679
CHANNEL_ID = "notice"
MAPLESTORY_URL = "https://maplestory.nexon.com/News/Notice"
MAPLE_URL = "https://maplestory.nexon.com"
URS_START_HOUR = 4 #utc 기준
URS_START_HOUR_KST = 13
URS_END_HOUR = 13
RESET_ALTER_HOUR_CONTENT = 14
RESET_ALTER_HOUR_BOSS = 11
EMBED_ICON_URL = "https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Ft1.daumcdn.net%2Fcfile%2Ftistory%2F99718D3359C47D6233"


#알림텍스트 
URS_START = "우르스 2배 이벤트 시작"
URS_END = "우르스 2배이벤트 종료"
CONTENT_RESET_DAILY = "오후 11시입니다. 일일컨텐츠를 확인해 주세요\n1. 마일리지 적립\n2. 몬컬보상\n3. 기여도 보스\n4. 길드 출석\n5. 몬파\n6. 황금마차\n7. 일일퀘스트\n8. 이벤트퀘스트\n9. 무릉포인트수령"
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

    await channel.send(f"반갑습니다. 메이플스토리 알림봇입니다")

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

    #guild = bot.get_guild(GUILD_ID)
    #channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()

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
    
    last_noti = None
    while not bot.is_closed():
        try:
            response = requests.get(MAPLESTORY_URL)

            #예외처리. 링크 리다이렉션 체크
            # 리다이렉션이 아닌경우
            if response.url == MAPLE_URL:           
                response.encoding ='utf-8'
                html = response.text
                soup = BeautifulSoup(html, "html.parser")
                noticeBanner = soup.find('div', {'class' : 'news_board'})
                notices = noticeBanner.select('li')
                if notices:
                    latest_notice = notices[0]
                    if last_noti != latest_notice:
                        last_noti = latest_notice        
                        notice_title = latest_notice.span.text
                        href = latest_notice.a.attrs['href']
                        notice_link = f"{MAPLE_URL}{href}"

                        embed = discord.Embed(title="새로운 공지가 올라왔어!", description=f'{notice_title}',url = f'{notice_link}' ,color=discord.Color.green())
                        embed.set_thumbnail(url = EMBED_ICON_URL)
                        await channel.send(embed=embed)
                        
                    else :
                        print("업데이트된 공지 없음")

            else :
                print ("error! 링크가 리다이렉션됨!")
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
    
    #guild = bot.get_guild(GUILD_ID)
    #channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    #time = datetime.datetime.now()
   # await channel.send(f"탸임스탬프 {time}")
    #await channel.send(f"check : {CONTENT_RESET_DAILY}")
        
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
    
    #await channel.send("Task3 Timestamp")
    await channel.send(f"타임스탬프 시작{time.strftime('%Y-%m-%d %X')}")
    await timeStamp(3600)

async def timeStamp(time):
    await asyncio.sleep(time)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    t = datetime.utcnow().astimezone(KST)
    await channel.send(f"디버깅 타임스탬프 {t.strftime('%Y-%m-%d %X')}")
    await timeStamp(time)

#--------------------------------------
#             핑
#--------------------------------------
@bot.command() #test for Discord bot is online
async def 핑(ctx):
    await ctx.send("퐁!")

#--------------------------------------
#             도움말
#--------------------------------------    
@bot.command(aliases=['h']) #도움말 명령어
async def 도움말(ctx):
    help_message = "~우르스(ㅇㄽ,ㅇㄹㅅ) : 우르스 2배 이벤트 시작시간 또는 남은 시간을 알려줍니다. \n ~MVP효율(ㅇㅂㅍ) : MVP작 효율 계산기를 불러옵니다. \n ~재획(ㅈㅎ) : 재획 타이머를 시작합니다. \n ~보스분배(ㅂㅂㄱ) : 보스 수익금 분배 계산합니다."
    await ctx.send(help_message)


#--------------------------------------
#             우르스 커맨드
#--------------------------------------
@bot.command(aliases=['ㅇㄽ','ㅇㄹㅅ']) #우르스 명령어
async def 우르스(ctx):
    current_time = datetime.utcnow().astimezone(KST)
    urs_start_time = datetime(current_time.year, current_time.month, current_time.day, URS_START_HOUR).astimezone(KST)
    time_until_urs_start = urs_start_time - current_time
    seconds_until_urs_start = int(time_until_urs_start.total_seconds())

    if current_time.hour < URS_START_HOUR_KST: #utc날짜차이 예외처리
        hours, remainder = divmod(time_until_urs_start.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f"우르스 2배 아직 시작 안했어! {URS_START_HOUR_KST} 시에 시작합니다. → {hours}시간 {minutes}분 {seconds}초")
    elif current_time.hour >= URS_END_HOUR:
        await ctx.send("우르스 2배 이미 끝났습니다.")
    else:
        urs_end_time = datetime(current_time.year, current_time.month, current_time.day, URS_END_HOUR).astimezone(KST)
        time_until_urs_end = urs_end_time - current_time
        hours, remainder = divmod(time_until_urs_end.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f"우르스 2배 진행 중 입니다.. → {hours}시간 {minutes}분 {seconds}초")
#------------------
# 테스트
#---------------------
@bot.command(aliases=['ㄱㅈ'])
async def 공지테스트(ctx):
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    try:
            response = requests.get(MAPLESTORY_URL)

            #예외처리. 링크 리다이렉션 체크
            # 리다이렉션이 아닌경우
            if response.url == MAPLE_URL:           
                response.encoding ='utf-8'
                html = response.text
                soup = BeautifulSoup(html, "html.parser")
                noticeBanner = soup.find('div', {'class' : 'news_board'})
                notices = noticeBanner.select('li')
                if notices:
                    latest_notice = notices[0]
                    if last_noti != latest_notice:
                        last_noti = latest_notice        
                        notice_title = latest_notice.span.text
                        href = latest_notice.a.attrs['href']
                        notice_link = f"{MAPLE_URL}{href}"

                        embed = discord.Embed(title="새로운 공지가 올라왔어!", description=f'{notice_title}',url = f'{notice_link}' ,color=discord.Color.green())
                        embed.set_thumbnail(url = EMBED_ICON_URL)
                        await channel.send(embed=embed)
                        
                    else :
                        await channel.send(f"업데이트된 공지가 없습니다.")

            else :
                await channel.send(f"홈페이지가 점검중입니다.")

    except Exception as e:
        print(f"An error occurred while checking for notices: {str(e)}")



#--------------------------------------
#             mvp
#--------------------------------------
@bot.command(aliases=['ㅇㅂㅍ']) #MVP작 명령어
async def mvp효율(ctx):
    await ctx.send("물통 한 병에 얼마인가요? 예시 : 2000")
    response = await bot.wait_for("message")
    MT = int(response.content)
    def calculate_efficiency(Bcp, Rcp, Gcp, ry, Trcp=None, Tbcp=None, Tgcp=None):
        
        bcc = 18150
        rcc = 9900
        gcc = 19800
        rsc = 22000
        trcc = 27000
        tbcc = 49500
        tgcc = 54000

        b = Bcp * (20 / 19) * 100 / (bcc * 100000000 / MT)
        r = Rcp * (20 / 19) * 100 / (rcc * 100000000 / MT) 
        g = Gcp * (20 / 19) * 100 / (gcc * 100000000 / MT) 
        rs = ry * (20 / 19) * 100 / (rsc * 100000000 / MT) 
        
        efficiency = {
            "블랙큐브": b,
            "레드큐브": r,
            "에디셔널큐브": g,
            "로얄스타일": rs,
        }

        if Trcp is not None and Tbcp is not None and Tgcp is not None:
            tr = Trcp * (20 / 19) * 100 / (trcc * 100000000 / MT)
            tb = Tbcp * (20 / 19) * 100 / (tbcc * 100000000 / MT) 
            tg = Tgcp * (20 / 19) * 100 / (tgcc * 100000000 / MT) 
            
            efficiency["명절 레드큐브 팩"] = tr
            efficiency["명절 블랙큐브 팩"] = tb
            efficiency["명절 에디큐브 팩"] = tg

        max_item = max(efficiency, key=efficiency.get)
        max_efficiency = efficiency[max_item]

        return max_item, max_efficiency

    await ctx.send("명절 큐브팩 있나요? (Y,N)")
    response = await bot.wait_for("message")
    nycp = response.content

    if nycp.lower() == "y":
        await ctx.send("경매장 블랙큐브 최저가격 (11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Bcp = int(response.content)

        await ctx.send("경매장 레드큐브 최저가격 (11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Rcp = int(response.content)

        await ctx.send("경매장 에디큐브 최저가격 (11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Gcp = int(response.content)

        await ctx.send("경매장 로얄스타일 최저가격 (10개, 팔지 않을 경우 0 입력 해주세요!) 예시 : 100000000")
        response = await bot.wait_for("message")
        ry = int(response.content)

        await ctx.send("경매장 명절 레드큐브팩 최저가격 (30개, 에픽 잠재 100% 가격 포함!) 예시 : 100000000")
        response = await bot.wait_for("message")
        Trcp = int(response.content)

        await ctx.send("경매장 명절 블랙큐브팩 최저가격 (30개, 유니크 잠재 30% 가격 포함!) 예시 : 100000000 ")
        response = await bot.wait_for("message")
        Tbcp = int(response.content)

        await ctx.send("경매장 명절 에디큐브팩 최저가격 (30개, 에디 에픽 잠재 30% 가격 포함!) 예시 : 100000000 ")
        response = await bot.wait_for("message")
        Tgcp = int(response.content)

        max_item, max_efficiency = calculate_efficiency(Bcp, Rcp, Gcp, ry, Trcp, Tbcp, Tgcp)

        await ctx.send(f"{max_item}의 효율이 {max_efficiency:.2f}% 로, 가장 높습니다.!")
        await ctx.send("단, 효율도 x라 하면, X < 100% 일 경우 완전 회수 불가")
        await ctx.send("X = 100% 일 경우 회수 가능")
        await ctx.send("X > 100% 일 경우 회수 + @")
    else :

        await ctx.send("경매장 블랙큐브 최저가격(11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Bcp = int(response.content)

        await ctx.send("경매장 레드큐브 최저가격(11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Rcp = int(response.content)

        await ctx.send("경매장 에디큐브 최저가격(11개) 예시 : 100000000")
        response = await bot.wait_for("message")
        Gcp = int(response.content)

        await ctx.send("경매장 로얄스타일 최저가격(10개, 팔지 않을 경우 0 입력) 예시 : 100000000")
        response = await bot.wait_for("message")
        ry = int(response.content)

        max_item, max_efficiency = calculate_efficiency(Bcp, Rcp, Gcp, ry)

        await ctx.send(f"{max_item}의 효율이 {max_efficiency:.2f}% 로, 가장 높습니다.")
        await ctx.send("효율도 x라 하면, X < 100% 일 경우 완전 회수 불가")
        await ctx.send("X = 100% 일 경우 회수 가능")
        await ctx.send("X > 100% 일 경우 회수 + @")


#--------------------------------------
#             재획
#--------------------------------------
#재획 시작 명령어 처리하는 코드
@bot.command(aliases=['ㅈㅎ'])
async def 재획(ctx):
    player_name = ctx.author

    if player_name in player_records:
        player_records[player_name] += 1
    else :
        player_records[player_name] = 1
    await ctx.send(f"{player_name}님, 재획을 시작했습니다.")
    #재획을 시작할때
    for i in range(3):
        await asyncio.sleep(1800) #경쿠 알림 30분마다 3번 전송하는 코드
        await nec(player_name)
        i #경고 개거슬려서 넣음
    #재획이 끝날때
    await asyncio.sleep(1800) #30분 대기
    if player_name in player_records:
        record = player_records[player_name]
    else :
        record = 0
    await ctx.send(f"{player_name}님! 재획이 끝났습니다. 현재 재획비를 {record}번 마셨습니다.")
    
    #재획 알리미 (2시간짜리) > ~재획 @name 
async def nec(player_name):
    player = await bot.fetch_user(player_name)
    if player:
        await player.send(f"{player_name}님, 경험치 쿠폰(30분)이 끝났습니다.")

#--------------------------------------
#             노래
#--------------------------------------
@bot.command(aliases=['ㄴㄹ'])
async def 개발자추천노래(ctx):
    await ctx.send("https://www.youtube.com/watch?v=yK8HfzDlOD4")

#--------------------------------------
#             분배기
#--------------------------------------
@bot.command(aliases=['ㅂㅂㄱ'])
async def 보스분배(ctx):
    await ctx.send("분배 할 금액 (예시 : 244342444)")
    charge_message = await bot.wait_for("message")
    charge = float(charge_message.content)

    await ctx.send("분배 받는 인원 (본인 포함, 최대 6명) 예시 : 6")
    party_message = await bot.wait_for("message")
    party = int(party_message.content)

    calculate = charge / party

    await ctx.send(f"{party}명이 분배 받을 금액은 {calculate:.1f} 메소입니다.")
    #환산기 사이트 구현해보자

bot.run(TOKEN)
