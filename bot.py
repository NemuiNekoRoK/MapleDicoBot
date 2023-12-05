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
GUILD_ID = 1117818963020230841
CHANNEL_ID = "test"

#로컬라이즈 이전 utc 기준시간 상수
URS_START_HOUR = 4
URS_END_HOUR = 13
RESET_ALTER_HOUR_CONTENT = 15
RESET_ALTER_HOUR_BOSS = 11
RESET_ALTER_HOUR_GUILD = 13

#로컬라이즈 후 비교용 kst 기준시간 상수
URS_START_HOUR_KST = 13
URS_END_HOUR_KST = 22
RESET_ALTER_HOUR_CONTENT_KST = 23
RESET_ALTER_HOUR_BOSS_KST = 20
RESET_ALTER_HOUR_GUILD_KST = 22

#URL
EMBED_ICON_URL = "https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Ft1.daumcdn.net%2Fcfile%2Ftistory%2F99718D3359C47D6233"
MAPLESTORY_URL = "https://maplestory.nexon.com/News/Notice"
MAPLE_URL = "https://maplestory.nexon.com"

#알림텍스트 
URS_START = "우르스 2배 이벤트 시작"
URS_END = "우르스 2배이벤트 종료"
CONTENT_RESET_DAILY = "오후 11시입니다. 일일컨텐츠를 확인해 주세요\n1. 마일리지 적립\n2. 몬컬보상\n3. 기여도 보스\n4. 길드 출석\n5. 몬파\n6. 황금마차\n7. 일일퀘스트\n8. 이벤트퀘스트\n9. 무릉포인트수령"
CONTENT_RESET_WEEKLY = "일요일 오후 11시입니다. 주간 컨텐츠를 확인해 주세요"
BOSS_RESET = "수요일 오후 8시입니다. 초기화 전 주간보스를 확인해 주세요"
NEW_ALTER = "새로운 공지가 올라왔습니다."
GUILD_CONTENT_ALTER = "길드 컨텐츠 마감이 임박하였습니다. 수로, 플래그 체크 부탁드립니다."
player_records = {}

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True  # message_content intent 추가

last_noti = None

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
    bot.loop.create_task(task_urs_start())
    bot.loop.create_task(task_urs_end())
    bot.loop.create_task(noticeTask())
    bot.loop.create_task(task_daily_content())
    bot.loop.create_task(task_weekly_content())
    bot.loop.create_task(task_guild_content())
    bot.loop.create_task(debugTask())
    #bot.loop.create_task(maple_task())

#----------------------------------------
#               우르스 알림
#----------------------------------------
async def task_urs_start():
    print("start")
    start_time = datetime(now.year, now.month, now.day, URS_START_HOUR).astimezone(KST) #각종 변수 세팅
    if now.hour >= URS_START_HOUR:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
    
    await urs_start_task(start_time)

async def urs_start_task(start_time):
    while True:
        now = datetime.utcnow().astimezone(KST)
        
        if now >= start_time:
            guild = bot.get_guild(GUILD_ID)
            channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
            await channel.send(f"{URS_START}")
        
            start_time += timedelta(days=1)
            #targetTime = datetime.combine(tomorrow.date(), start_time)
            #delta = targetTime - datetime.utcnow().astimezone(KST)
            #await asyncio.sleep(delta.seconds)

        await asyncio.sleep(60)
        print("urs start check")
#------------------------------------------------
#                  우르스 끝
#------------------------------------------------    
async def task_urs_end():
    print("start")
    start_time = datetime(now.year, now.month, now.day, URS_END_HOUR).astimezone(KST) #각종 변수 세팅
    if now.hour >= URS_END_HOUR:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
    
    await urs_end_task(start_time)

async def urs_end_task(start_time):
    while True:
        now = datetime.utcnow().astimezone(KST)

        if now >= start_time:
            guild = bot.get_guild(GUILD_ID)
            channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
            await channel.send(f"{URS_END}")
        
            start_time += timedelta(days=1)
            #targetTime = datetime.combine(tomorrow.date(), start_time)
            #delta = targetTime - datetime.utcnow().astimezone(KST)
            #await asyncio.sleep(delta.seconds)
        await asyncio.sleep(60)
        print("urs end check")
#------------------------------------------------
#                  공지 알림
#------------------------------------------------
# 정상작동 pass
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
            if response.url == MAPLESTORY_URL:           
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
                        print("새 공지!")
                        
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
    if now.hour >= RESET_ALTER_HOUR_CONTENT_KST:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)


    await daily_start_task(start_time)

async def daily_start_task(start_time):
    while True:
        now = datetime.utcnow().astimezone(KST)

        if now >= start_time:
            guild = bot.get_guild(GUILD_ID)
            channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
            await channel.send(f"{CONTENT_RESET_DAILY}")
        
            start_time += timedelta(days=1)
            #targetTime = datetime.combine(tomorrow.date(), start_time)
            #delta = targetTime - datetime.utcnow().astimezone(KST)
            #await asyncio.sleep(delta.seconds)
        await asyncio.sleep(60)
        print("daily check")


    
#-------------------------------------
#             주간보스
#-------------------------------------
async def task_weekly_content():
    print("start")
    start_time = datetime(now.year, now.month, now.day, RESET_ALTER_HOUR_BOSS).astimezone(KST) #각종 변수 세팅
    if now.hour >= RESET_ALTER_HOUR_BOSS:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
    
    await weekly_start_task(start_time)

async def weekly_start_task(start_time):
    while True:
        now = datetime.utcnow().astimezone(KST)

        if now >= start_time:
            if now.weekday() == 3: #weekday기준 수요일
                guild = bot.get_guild(GUILD_ID)
                channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
                await channel.send(f"{BOSS_RESET}")
                
            start_time += timedelta(days=1)
            #targetTime = datetime.combine(tomorrow.date(), start_time)
            #delta = targetTime - datetime.utcnow().astimezone(KST)
            #await asyncio.sleep(delta.seconds)
        await asyncio.sleep(60)
        print("weekly check")
        
#-------------------------------------
#             길컨
#-------------------------------------
async def task_guild_content():
    print("start")
    start_time = datetime(now.year, now.month, now.day, RESET_ALTER_HOUR_GUILD).astimezone(KST) #각종 변수 세팅
    if now.hour >= RESET_ALTER_HOUR_GUILD:  # 현재 시간이 URS_END_HOUR 이후라면 다음 날로 설정
        start_time += timedelta(days=1)
    
    await guild_start_task(start_time)

async def guild_start_task(start_time):
    while True:
        now = datetime.utcnow().astimezone(KST)

        if now >= start_time:
            if now.weekday() == 6 or now.weekday() == 7: #weekday기준 토, 일요일
                guild = bot.get_guild(GUILD_ID)
                channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
                await channel.send(f"{GUILD_CONTENT_ALTER}")
                
            start_time += timedelta(days=1)
            #targetTime = datetime.combine(tomorrow.date(), start_time)
            #delta = targetTime - datetime.utcnow().astimezone(KST)
            #await asyncio.sleep(delta.seconds)
        await asyncio.sleep(60)
        print("guild check")        
        
#--------------------------------------
#             디버거
#--------------------------------------
async def debugTask():
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    time = datetime.utcnow().astimezone(KST)
    
    #await channel.send("Task3 Timestamp")
    #await channel.send(f"타임스탬프 시작{time.strftime('%Y-%m-%d %X')}")
    print(f"타임스탬프 시작{time.strftime('%Y-%m-%d %X')}")
    await timeStamp(60)

async def timeStamp(time):
    await asyncio.sleep(time)
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.channels, name=CHANNEL_ID)
    t = datetime.utcnow().astimezone(KST)
    #await channel.send(f"디버깅 타임스탬프 {t.strftime('%Y-%m-%d %X')}")
    print(f"디버깅 타임스탬프 {t.strftime('%Y-%m-%d %X')}")
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
    help_message = "~MVP효율(ㅇㅂㅍ) : MVP작 효율 계산기를 불러옵니다. \n ~재획(ㅈㅎ) : 재획 타이머를 시작합니다. \n ~보스분배(ㅂㅂㄱ) : 보스 수익금 분배 계산합니다. \n ~공지(ㄱㅈ) : 새로운 공지가 있는지 ㅅ수동으로 확인합니다."
    await ctx.send(help_message)

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
            if response.url == MAPLESTORY_URL:           
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
#test