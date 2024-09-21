import discord
import os
import asyncio
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import random


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

user_data = {}
boss_table = {
    '치와와': {
        '레벨': 5,
        '지역': '엘드리히02',
        '주기': 2,
    },
    '베나투스': {
        '레벨': 60,
        '지역': '오염된 강줄기',
        '주기': 240,        # 4 시간
    },
    '비오렌트': {
        '레벨': 65,
        '지역': '아가미 개울',
        '주기': 240,        # 4 시간
    },
    '레이디달리아': {
        '레벨': 85,
        '지역': '핏빛 그늘',
        '주기': 600,        # 10 시간
    },
    '달리아': {
        '레벨': 85,
        '지역': '핏빛 그늘',
        '주기': 600,        # 10 시간
    },
    '에고': {
        '레벨': 70,
        '지역': '탈환 집결지',
        '주기': 720,        # 12 시간
    },
    '리베라': {
        '레벨': 75,
        '지역': '검은 폭풍 반도',
        '주기': 840,        # 14 시간
    },
    '언두미엘': {
        '레벨': 80,
        '지역': '실험체 연구실',
        '주기': 840,        # 14 시간
    },
    '가레스': {
        '레벨': 98,
        '지역': '죽은 자의 대지 1구역',
        '주기': 1200,        # 20 시간
    },
    '아멘티스': {
        '레벨': 88,
        '지역': '석회암 곶',
        '주기': 1080,        # 18 시간
    },
    '브라우드모어': {
        '레벨': 88,
        '지역': '장미 덩굴 다리',
        '주기': 1200,        # 20 시간
    },
    '남작': {
        '레벨': 88,
        '지역': '장미 덩굴 다리',
        '주기': 1200,        # 20 시간
    },
    '아라네오': {
        '레벨': 75,
        '지역': '티리오사 무덤 지하 1층',
        '주기': 840,        # 14 시간
    },
    '아쿨레우스': {
        '레벨': 85,
        '지역': '티리오사 무덤 지하 2층',
        '주기': 1080,        # 18 시간
    },
    '장군': {
        '레벨': 85,
        '지역': '티리오사 무덤 지하 2층',
        '주기': 1080,        # 18 시간
    },
    '티토르': {
        '레벨': 98,
        '지역': '죽은 자의 대지 2구역',
        '주기': 1440,        # 24 시간
    },
    '와니타스': {
        '레벨': 93,
        '지역': '올가미 수렁',
        '주기': 1800,        # 30 시간
    },
    '메투스': {
        '레벨': 93,
        '지역': '추종자 벌판',
        '주기': 1800,        # 30 시간
    },
    '카테나': {
        '레벨': 100,
        '지역': '죽은 자의 대지 2구역',
        '주기': 1200,        # 20시간
    },
    '슈라이어': {
        '레벨': 95,
        '지역': '사냥개의 가면극',
        '주기': 1200,        # 20 시간
    },
    '라르바': {
        '레벨': 98,
        '지역': '가르바나 간척지',
        '주기': 1200,  # 20 시간
    },
    '듀플리칸': {
        '레벨': 93,
        '지역': '눈 뜬 꼭두각시의 옥좌',
        '주기': 1800,        # 30 시간
    },
    '세크레타': {
        '레벨': 100,
        '지역': '칼리온의 무덤',
        '주기': 2400,        # 40 시간
    },
    '오르도': {
        '레벨': 100,
        '지역': '후계자의 낙원',
        '주기': 2400,        # 40 시간
    },
    '아스타': {
        '레벨': 100,
        '지역': '황금피 평원',
        '주기': 2400,        # 40 시간
    },
    '수포르': {
        '레벨': 100,
        '지역': '황금피 평원',
        '주기': 2400,        # 40시간
    },
}
boss_schedule = {}
notification_tasks = {}  # 알림 작업을 관리할 딕셔너리


distribution_item_table = {}
distribution_tasks = {}  # 알림 작업을 관리할 딕셔너리

auction_item_table = {}
auction_tasks = {}  # 알림 작업을 관리할 딕셔너리
alarm_hz = [30, 10, 5, 1, 0]

boss_kill_history = []

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!보스킬'):
        await boss_kill_update(message)

    elif message.content.startswith('!보스젠'):
        await show_boss_schedule(message)
    
    elif message.content.startswith('!보스정보'):
        await show_boss_infos(message)

    elif message.content.startswith('!백업'):
        if boss_kill_history:
            try:
                with open('boss_kill_history.txt', 'w', encoding='utf-8') as f:
                    for history in boss_kill_history:
                        f.write(history + '\n')
                await message.channel.send(file=discord.File('boss_kill_history.txt'))
            except Exception as e:
                await message.channel.send(f'파일 저장 중 오류 발생: {str(e)}')
            finally:
                if os.path.exists('boss_kill_history.txt'):
                    os.remove('boss_kill_history.txt')

    elif message.content.startswith('!복원'):
        if message.attachments:
            history_message = ''
            for attachment in message.attachments:
                if attachment.filename.endswith('.txt'):
                    file_path = os.path.join("downloads", attachment.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    await attachment.save(file_path)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            await boss_kill_update(message, line)
                            history_message += line + '\n'
                    os.remove(file_path)

    
    if message.content.startswith('!사다리'):
        distribution_parts = message.content.split(" /")
        if '복수등록' in distribution_parts[1]:
            await register_multiple_distribution_item(message)

        elif '등록' in distribution_parts[1]:
            await register_distribution_item(message)

        elif '현황' in distribution_parts[1]:
            await show_distribution_status(message)
        
        elif '복수참여' in distribution_parts[1]:
            await register_multiple_participant(message)

        elif '참여' in distribution_parts[1]:
            await register_participant(message)

    if message.content.startswith('!경매'):
        auction_parts = message.content.split(" /")
        if '등록' in auction_parts[1]:
            await register_auction_item(message)

        elif '현황' in auction_parts[1]:
            await show_auction_status(message)
        
        elif '참여' in auction_parts[1]:
            await register_auction_participant(message)

    elif message.content.startswith('!도움말'):
        await show_help_message(message)

    elif message.content.startswith('!업데이트노트'):
        await show_update_node(message)

async def boss_kill_update(message_with_channel, message=False):
    print("!보스킬 명령어 수신됨")  # 명령어 수신 확인
    if message:
        boss_parts = message.split(" /")
    else:
        boss_parts = message_with_channel.content.split(" /")
    specific_time = None
    if len(boss_parts) > 2:
        specific_time = True
    if len(boss_parts) < 2:
        if message_with_channel:
            await message_with_channel.channel.send('명령어 형식이 올바르지 않습니다.\n올바른 형식: !보스킬 /[이름] /[시간: MMDDHHMM](선택사항)')
        return
    boss_name = boss_parts[1]

    kst = pytz.timezone('Asia/Seoul')
    if specific_time is not None:
        kill_time_str = boss_parts[2]
        current_year = datetime.now().year
        kill_time = datetime.strptime(f"{current_year}{kill_time_str}", "%Y%m%d%H%M")
        kill_time = kst.localize(kill_time)
    else:
        now_utc = datetime.now(pytz.utc)
        kill_time = now_utc.astimezone(kst)
    print(f'Kill time for {boss_name}: {kill_time}')  # 디버깅: kill_time 확인
    try:
        if boss_name in boss_table or "★" + boss_name + "★" in boss_table:
            for boss_table_name in boss_table.keys():
                if boss_name in boss_table_name:
                    boss_name = boss_table_name
            respawn_time = kill_time + timedelta(minutes=boss_table[boss_name]['주기'])

            boss_schedule[boss_name] = {
                'kill_time': kill_time,
                'respawn_time': respawn_time
            }
            boss_kill_message = f'- 보스 "{boss_name}"의 다음 젠 시간이 등록되었습니다: {respawn_time.strftime('%m월 %d일 %H시 %M분')}\n'
            for history in boss_kill_history:
                if boss_name in history:
                    boss_kill_history.remove(history)
            if specific_time is None:
                formatted_time = kill_time.strftime('%m%d%H%M')
                boss_kill_history.append(message_with_channel.content + f' /{formatted_time}')
            else:
                if message:
                    boss_kill_history.append(message)
                else:
                    boss_kill_history.append(message_with_channel.content)
            notify_times = []
            for minutes in alarm_hz:
                notify_times.append(respawn_time - timedelta(minutes=minutes))

            # 알림 설정 부분 확인
            try:
                boss_kill_message += '- 자동 알림이 등록되었습니다: ('
                for idx, notify_time in enumerate(notify_times):
                    minutes = alarm_hz[idx]
                    notify_key = f"{boss_name}_{minutes}"
                    if notify_key in notification_tasks:
                        print(f'Notification task for {notify_key} exists. Checking if done...')  # 디버깅: task 존재 확인
                        if not notification_tasks[notify_key].done():
                            print(f'Task for {notify_key} not done. Cancelling...')  # 디버깅: task 상태 확인
                            notification_tasks[notify_key].cancel()
                        else:
                            print(f'Task for {notify_key} already completed.')  # 디버깅: task 완료 확인

                    print(f'Creating task for {notify_key} notification')  # 태스크 생성 확인
                    notification_tasks[notify_key] = asyncio.create_task(schedule_boss_notification(boss_name, notify_time, message_with_channel.channel, minutes))

                    if minutes != 0:
                        boss_kill_message += f"{minutes} 분 후, "
                    else:
                        boss_kill_message += "젠 시간)"

                    print(f'Task created for {boss_name}')  # 태스크 생성 확인 메시지
                boss_kill_message += '\n\n'
                if message_with_channel:
                    await message_with_channel.channel.send(boss_kill_message)
                else:
                    print(boss_kill_message)
            except Exception as e:
                if message_with_channel:
                    await message_with_channel.channel.send(f'태스크 생성 오류 발생: {str(e)}')
                else:
                    print(f'Task creation error for {boss_name}: {str(e)}')  # 서버 로그에서 확인용

        else:
            if message_with_channel:
                await message.channel.send(f'알 수 없는 보스 이름입니다: {boss_name}')
            else:
                print('알 수 없는 보스 이름입니다.')  # 서버 로그에서 확인용

    except Exception as e:
        if message_with_channel:
            await message.channel.send(f'오류 발생: {str(e)}')
        else:
            print(f'Exception in !보스킬: {str(e)}')  # 서버 로그에서 확인용
        return
    
async def show_update_node(message):
    update_message = ''
    update_message += '업데이트 노트:\n\n'
    update_message += '- 삭제된 보스 복원:\n'
    update_message += ' - 지난 업데이트에서 삭제됐던 베나투스, 비오렌트 보스 정보를 복원하였습니다.\n'
    update_message += ' - 추후 자유롭게 보스 정보를 추가할 수 있는 기능을 구현하였습니다.\n'
    update_message += ' - 보스 관련 업데이트 기능은 "!도움말 /보스" 명령어를 통해 확인하세요.\n\n'
    update_message += '- 사다리 복수등록 기능 개선:\n'
    update_message += ' - 사다리 복수등록 시 반복되어 출력되던 메시지를 제거하였습니다.\n'
    update_message += ' - 사다리 관련 업데이트 기능은 "!도움말 /사다리" 명령어를 통해 확인하세요.\n'
    await message.channel.send(update_message)

    
async def show_help_message(message):
    help_parts = message.content.split(" /")
    help_message = ''
    if len(help_parts) == 1:
        help_message += '도움말 옵션을 함께 입력해주세요\n'
        help_message += '- !도움말 /보스 : 보스 관련 도움말 출력\n'
        help_message += '- !도움말 /경매 : 경매 관련 도움말 출력\n'
        help_message += '- !도움말 /사다리 : 사다리 관련 도움말 출력 (준비중)\n'
        await message.channel.send(help_message)
    elif '보스' in help_parts[1]:
        help_message += f"보스 알림 기능은 다음을 참고하여 사용해주세요!\n"
        help_message += f"- 보스 킬 시간 등록 및 젠 시간 자동 계산:\n"
        help_message += f" - !보스킬 /[보스이름]                    -> 현재 시간으로 킬 시간 등록\n"
        help_message += f" - !보스킬 /[보스이름] /[시간(MMDDHHMM)]  -> 특정 시간으로 킬 시간 등록\n"
        help_message += f" - (ex) !보스킬 /에고 /08031120\n\n"
        help_message += f"- 보스 젠 시간 확인:\n"
        help_message += f" - !보스젠                    -> 등록된 모든 보스 젠 시간 출력\n"
        help_message += f" - !보스젠 /[보스이름]          -> 원하는 보스를 특정하여 젠 시간 출력\n"
        help_message += f" - (ex) !보스젠 /에고\n\n"
        help_message += f"- 보스 정보(젠 주기, 레벨, 지역) 확인 확인:\n"
        help_message += f" - !보스정보                    -> 등록된 모든 보스 정보 출력\n\n"
        help_message += f" - !보스정보 /변경 /[보스이름] /[변경 젠 주기(시간 단위)]          -> 보스 젠 시간이 변경되면 정보 변경 가능\n"
        help_message += f" - (ex) !보스정보 /변경 /에고 /10\n\n"
        help_message += f" - !보스정보 /추가 /[보스이름] /[젠 주기(시간 단위)] /[레벨] /[젠위치]          -> 새로운 보스 추가 시 데이터 추가 가능\n"
        help_message += f" - (ex) !보스정보 /추가 /치와와와 /10 /5 /엘드리히\n\n"
        help_message += f" - !보스정보 /제거 /[보스이름(중복 입력 원할 시 띄어쓰기로 구분)]       -> 보스 정보에서 제거하고 싶은 보스 제거\n"
        help_message += f" - (ex) !보스정보 /제거 /치와와 치와와와\n\n"
        await message.channel.send(help_message)
    elif '경매' in help_parts[1]:
        help_message += f"경매 기능은 다음을 참고하여 사용해주세요!\n"
        help_message += f"- 경매 물품 등록:\n"
        help_message += f" - !경매 /등록 /[아이템명(띄어쓰기x)] /[최소금액] /[경매 진행시간(분)] /[판매자]        -> 아이템명(띄어쓰기x), 최소금액, 경매 진행시간 설정\n"
        help_message += f" - (ex) !경매 /등록 /아잠히산모자 /1000 /30 /존서프       -> 해당 아이템에 고유 상품번호가 발행됩니다\n\n"
        help_message += f"- 경매 물품 확인:\n"
        help_message += f" - !경매 /현황            -> 현재 경매중인 아이템 현황을 상품번호, 참여자 정보와 함께 출력합니다\n\n"
        help_message += f"- 경매 참여:\n"
        help_message += f" - !경매 /참여 /[상품번호] /[희망금액] /[구매자]        -> 경매 물품 리스트를 확인한 후 원하는 상품 번호를 입력합니다\n"
        help_message += f" - (ex) !경매 /참여 /1 /1500 /존서프\n\n"
        await message.channel.send(help_message)
    elif '사다리' in help_parts[1]:
        help_message += f"사다리 기능은 다음을 참고하여 사용해주세요!\n"
        help_message += f"- 사다리 물품 등록:\n"
        help_message += f" - !사다리 /등록 /[아이템명(띄어쓰기x)] /[사다리 진행시간(분)] /[등록자]        -> 아이템명(띄어쓰기x), 사다리 진행시간, 등록자 설정\n"
        help_message += f" - (ex) !사다리 /등록 /아잠히산모자 /30       -> 해당 아이템에 고유 상품번호가 발행됩니다\n\n"
        help_message += f"- 사다리 복수등록:\n"
        help_message += f" - !사다리 /복수등록 /[아이템명 리스트(띄어쓰기로 구분)] /[등록자]        -> 복수 아이템은 띄어쓰기로 구분(한 아이템에는 띄어쓰기x), 등록자 설정, 진행시간은 5분으로 고정\n"
        help_message += f" - (ex) !사다리 /복수등록 /아잠히산모자 타락한신념의목걸이 /존서프       -> 해당 아이템 리스트를 순회하며 각각의 고유 상품번호가 발행됩니다\n\n"
        help_message += f"- 사다리 물품 확인:\n"
        help_message += f" - !사다리 /현황            -> 현재 사다리타기중인 아이템 현황을 상품번호, 참여자 정보와 함께 출력합니다\n\n"
        help_message += f"- 사다리 참여:\n"
        help_message += f" - !사다리 /참여 /[상품번호] /[신청자]        -> 사다리타기 물품 리스트를 확인한 후 원하는 상품 번호를 입력합니다\n"
        help_message += f" - (ex) !사다리 /참여 /1 /존서프\n\n"
        help_message += f"- 사다리 복수참여:\n"
        help_message += f" - !사다리 /복수참여 /[상품번호] /[신청자(스페이스바로 구분)]        -> 참여자를 여러 명 등록할 수 있습니다\n"
        help_message += f" - (ex) !사다리 /복수참여 /1 /존서프 쭌야 케이 PANG\n\n"
        await message.channel.send(help_message)
    
async def show_boss_infos(message):
    boss_show_parts = message.content.split(" /")
    if len(boss_show_parts) > 1:
        if '변경' in boss_show_parts[1]:
            if len(boss_show_parts) < 4:
                warning_message = '명령어 형식이 올바르지 않습니다.\n올바른 형식: !보스정보 /변경 /[보스이름] /[변경 젠 주기(시간 단위)]\n'
                await message.channel.send(warning_message)
            boss_name = boss_show_parts[2]
            if '언두미엘' in boss_name:
                boss_name = '★언두미엘★'
            boss_respawn_cycle = int(boss_show_parts[3])
            if boss_name in boss_table.keys():
                past_cycle = boss_table[boss_name]['주기'] // 60
                boss_table[boss_name]['주기'] = boss_respawn_cycle * 60
                boss_show_message = ''
                boss_show_message += f'"{boss_name}" 젠 사이클 정보가 업데이트 되었습니다. \n'
                boss_show_message += f'- 변경 전: {past_cycle} 시간\n'
                boss_show_message += f'- 변경 후: {boss_respawn_cycle} 시간\n\n'
                kill_time = boss_schedule[boss_name]['kill_time']
                formatted_time = None
                if kill_time is not None:
                    formatted_time = kill_time.strftime('%m%d%H%M')
                message.channel.send(boss_show_message)
                if formatted_time is not None:
                    await boss_kill_update(message, f'!보스킬 /{boss_name} /{formatted_time}')
            else:
                message.channel.send('등록되지 않은 보스입니다.\n')

        elif '추가' in boss_show_parts[1]:
            if len(boss_show_parts) < 6:
                warning_message = '명령어 형식이 올바르지 않습니다.\n올바른 형식: !보스정보 /추가 /[보스이름] /[젠 주기(시간 단위)] /[레벨] /[젠위치]\n'
                await message.channel.send(warning_message)
            boss_name = boss_show_parts[2]
            boss_respawn_cycle = int(boss_show_parts[3])
            boss_level = int(boss_show_parts[4])
            boss_location = boss_show_parts[5]
            if boss_name not in boss_table.keys():
                boss_table[boss_name] = {
                    '레벨': boss_level,
                    '지역': boss_location,
                    '주기': boss_respawn_cycle * 60
                }
                boss_schedule[boss_name] = {
                    'kill_time': None,
                    'respawn_time': None
                }
                add_message = f'보스 정보가 추가되었습니다.\n이름: {boss_name}, 레벨: {boss_level}, 젠 사이클: {boss_respawn_cycle} 시간, 젠 위치: {boss_location}\n\n'
                await message.channel.send(add_message)
            else:
                await message.channel.send('이미 등록된 보스입니다.\n')

        elif '제거' in boss_show_parts[1]:
            if len(boss_show_parts) < 3:
                warning_message = '명령어 형식이 올바르지 않습니다.\n올바른 형식: !보스정보 /제거 /[보스이름(중복 입력 원할 시 띄어쓰기로 구분)]\n'
                await message.channel.send(warning_message)
            boss_names = boss_show_parts[2]
            boss_names_list = boss_names.split(" ")
            delete_message = ''
            for boss_name in boss_names_list:
                if boss_name in boss_table or "★" + boss_name + "★" in boss_table:
                    del boss_table[boss_name]
                    if boss_name in boss_schedule:
                        del boss_schedule[boss_name]
                    delete_message += f'"{boss_name}" 데이터가 제거되었습니다.\n'
            if len(delete_message) == 0:
                delete_message = '이미 제거된 보스 입니다.\n'
            await message.channel.send(delete_message)

    else:
        boss_names = boss_table.keys()
        boss_show_message = ''
        for boss_name in boss_names:
            if boss_name in boss_table:
                boss_show_message += f'"{boss_name}": \n'
                boss_show_message += f'- 주기: {boss_table[boss_name]['주기'] // 60} 시간, '
                boss_show_message += f' 레벨: {boss_table[boss_name]['레벨']}, '
                boss_show_message += f' 지역: {boss_table[boss_name]['지역']}'
                boss_show_message += '\n\n'
    await message.channel.send(boss_show_message)


async def show_boss_schedule(message):
    boss_show_parts = message.content.split(" /")
    if len(boss_show_parts) > 1:
        boss_names = boss_show_parts[1:]
    else:
        boss_names = boss_schedule.keys()

    boss_show_message = ''
    boss_data_list = []

    for boss_name in boss_names:
        if boss_name in boss_schedule:
            boss_data = boss_schedule[boss_name]
            boss_data_list.append((boss_name, boss_data))

    boss_data_list.sort(key=lambda x: x[1]['respawn_time'])

    for boss_name, boss_data in boss_data_list:
        if boss_name == '치와와':
            continue
        boss_show_message += f'"{boss_name}"\n'
        boss_show_message += f'- 킬 시간: {boss_data["kill_time"].strftime("%m월 %d일 %H시 %M분")}\n'
        boss_show_message += f'- 예상 젠 시간: {boss_data["respawn_time"].strftime("%m월 %d일 %H시 %M분")}\n'
        boss_show_message += '\n\n'

    if boss_show_message:
        await message.channel.send(boss_show_message)
    else:
        await message.channel.send("등록된 보스 젠 정보가 없습니다.")

async def schedule_boss_notification(boss_name, notify_time, channel, minutes):
    try:
        kst = pytz.timezone('Asia/Seoul')
        now_utc = datetime.now(pytz.utc)
        now_kst = now_utc.astimezone(kst)
        delay = (notify_time - now_kst).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
            if minutes == 0:
                await channel.send(f'"{boss_name}" 보스가 젠 됐습니다!')
            else:
                await channel.send(f'"{boss_name}" 보스가 {minutes} 분 후에 젠됩니다!')
        else:
            if minutes == 0:
                await channel.send(f'"{boss_name}" 보스의 젠 알림 시간을 놓쳤습니다. 시간을 다시 등록해주세요. (delay: {delay})')
    except Exception as e:
        await channel.send(f'알림 설정 오류: {str(e)}')
        print(f'Exception in schedule_boss_notification for {boss_name}: {str(e)}')  # 서버 로그에서 확인용


async def register_distribution_item(message):
    distribution_parts = message.content.split(" /")
    if len(distribution_parts) < 5:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !사다리 /등록 /[아이템명(띄어쓰기x)] /[사다리 진행시간(분)] /[등록자]\n'
        await message.channel.send(warning_message)
        return
    item_name = distribution_parts[2]
    item_distribution_time = distribution_parts[3]
    register = distribution_parts[4]
    registered_number_count = 1
    while (registered_number_count in distribution_item_table.keys()):
        registered_number_count += 1
    price_number = registered_number_count

    kst = pytz.timezone('Asia/Seoul')
    now_utc = datetime.now(pytz.utc)
    registered_time = now_utc.astimezone(kst)
    end_time = registered_time + timedelta(minutes=int(item_distribution_time))

    distribution_item_table[price_number] = {
        '아이템명': item_name,
        '사다리 시작 시간': registered_time,
        '사다리 종료 시간': end_time,
        '등록자': register,
        '신청자': [],
        '당첨자': None
    }
    distribution_message = '사다리 상품이 등록되었습니다\n'
    distribution_message += '상품 정보:\n'
    distribution_message += f'- 상품번호: {price_number}\n'
    distribution_message += f'- 아이템명: {item_name}\n'
    distribution_message += f'- 등록자: {register}\n'
    distribution_message += f'- 사다리 시작 시간: {registered_time.strftime('%m월 %d일 %H시 %M분')}\n'
    distribution_message += f'- 사다리 종료 시간: {end_time.strftime('%m월 %d일 %H시 %M분')}\n'
    if price_number in distribution_tasks:
        print(f'distribution task for {price_number} exists. Checking if done...')  # 디버깅: task 존재 확인
        if not distribution_tasks[price_number].done():
            print(f'Task for {price_number} not done. Cancelling...')  # 디버깅: task 상태 확인
            distribution_tasks[price_number].cancel()
        else:
            print(f'Task for {price_number} already completed.')  # 디버깅: task 완료 확인

    print(f'Creating task for {price_number} distribution')  # 태스크 생성 확인
    distribution_tasks[price_number] = asyncio.create_task(schedule_distribution(price_number, message, end_time))
    await message.channel.send(f'{distribution_message}')

async def register_multiple_distribution_item(message):
    distribution_parts = message.content.split(" /")
    if len(distribution_parts) < 4:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !사다리 /복수등록 /[아이템명 리스트(띄어쓰기로 구분)] /[등록자]\n'
        await message.channel.send(warning_message)
        return
    items = distribution_parts[2]
    items_list = items.split(" ")
    register = distribution_parts[3]
    
    kst = pytz.timezone('Asia/Seoul')

    price_number = 1
    distribution_message = ''
    for i in range(len(items_list)):
        while (price_number in distribution_item_table.keys()):
            price_number += 1
        
        now_utc = datetime.now(pytz.utc)
        registered_time = now_utc.astimezone(kst) + timedelta(seconds=i * 5)
        end_time = registered_time + timedelta(minutes=5)

        distribution_item_table[price_number] = {
            '아이템명': items_list[i],
            '사다리 시작 시간': registered_time,
            '사다리 종료 시간': end_time,
            '등록자': register,
            '신청자': [],
            '당첨자': None
        }
        distribution_message += '사다리 상품이 등록되었습니다\n'
        distribution_message += '상품 정보:\n'
        distribution_message += f'- 상품번호: {price_number}\n'
        distribution_message += f'- 아이템명: {items_list[i]}\n'
        distribution_message += f'- 등록자: {register}\n'
        distribution_message += f'- 사다리 시작 시간: {registered_time.strftime('%m월 %d일 %H시 %M분')}\n'
        distribution_message += f'- 사다리 종료 시간: {end_time.strftime('%m월 %d일 %H시 %M분')}\n\n'
        if price_number in distribution_tasks:
            print(f'distribution task for {price_number} exists. Checking if done...')  # 디버깅: task 존재 확인
            if not distribution_tasks[price_number].done():
                print(f'Task for {price_number} not done. Cancelling...')  # 디버깅: task 상태 확인
                distribution_tasks[price_number].cancel()
            else:
                print(f'Task for {price_number} already completed.')  # 디버깅: task 완료 확인

        print(f'Creating task for {price_number} distribution')  # 태스크 생성 확인
        distribution_tasks[price_number] = asyncio.create_task(schedule_distribution(price_number, message, end_time))
    await message.channel.send(f'{distribution_message}')

async def schedule_distribution(price_number, message, end_time):
    try:
        kst = pytz.timezone('Asia/Seoul')
        now_utc = datetime.now(pytz.utc)
        now_kst = now_utc.astimezone(kst)
        delay = (end_time - now_kst).total_seconds()
        target_info = distribution_item_table[price_number]
        players = target_info['신청자']

        if delay > 0:
            await asyncio.sleep(delay)
            if len(players) == 0:
                await message.channel.send('참여자가 없어 사다리게임을 진행하지 않습니다. 다시 등록해주세요\n')
                del distribution_item_table[price_number]
                return
            elif len(players) == 1:
                ladder_message = f'"{players[0]}" 님께서 당첨되셨습니다! 축하합니다\n'
                ladder_message += '상품 정보:\n'
                ladder_message += f'- 상품번호: {price_number}\n'
                ladder_message += f'- 아이템명: {target_info['아이템명']}\n'
                ladder_message += f'- 등록자: {target_info['등록자']}\n'
                await message.channel.send(ladder_message)
                del distribution_item_table[price_number]
                return
            else:
                players = distribution_item_table[price_number]['신청자']
                ladder_message = '사다리 게임을 시작합니다\n'
                ladder_message += '상품 정보:\n'
                ladder_message += f'- 상품번호: {price_number}\n'
                ladder_message += f'- 아이템명: {target_info['아이템명']}\n'
                ladder_message += f'- 등록자: {target_info['등록자']}\n\n'
                ladder_message += f'신청자 정보: [ID, 닉네임]\n'
                for idx, player in enumerate(target_info['신청자']):
                    ladder_message += f'[{idx}, {player}]'
                    if idx < len(target_info['신청자']) - 1:
                        ladder_message += ', '
                    else:
                        ladder_message += '\n\n'
                await message.channel.send(ladder_message)
                await play_ladder_game(message, players, price_number)
                del distribution_item_table[price_number]

        else:
            await message.channel.send('잘못 된 시간 등록입니다')
    except Exception as e:
        await message.channel.send(f'사다리 알림 설정 오류: {str(e)}')

async def show_distribution_status(message):
    distribution_message = '현재 사다리 현황:\n'
    for price_number, infos in distribution_item_table.items():
        distribution_message += '\n상품 정보:\n'
        distribution_message += f'- 상품번호: {price_number}\n'
        distribution_message += f'- 아이템명: {infos['아이템명']}\n'
        distribution_message += f'- 등록자: {infos['등록자']}\n'
        if len(infos['신청자']) == 0:
            distribution_message += '- 신청자: 없음\n'
        else:
            distribution_message += f'- 신청자: ['
            for idx, player in enumerate(infos['신청자']):
                distribution_message += f'{player}'
                if idx < len(infos['신청자']) - 1:
                    distribution_message += ', '
                else:
                    distribution_message += ']\n'
        distribution_message += f'- 사다리 시작 시간: {infos['사다리 시작 시간'].strftime("%m월 %d일 %H시 %M분")}\n'
        distribution_message += f'- 사다리 종료 시간: {infos['사다리 종료 시간'].strftime("%m월 %d일 %H시 %M분")}\n'
        kst = pytz.timezone('Asia/Seoul')
        now_utc = datetime.now(pytz.utc)
        registered_time = now_utc.astimezone(kst)
        remain_time = infos['사다리 종료 시간'] - registered_time
        total_seconds = remain_time.total_seconds()

        total_seconds = abs(total_seconds)

        minutes, seconds = divmod(total_seconds, 60)
        distribution_message += f'- 남은 사다리 시간: {int(minutes)}분 {int(seconds)}초\n\n'

    await message.channel.send(f'{distribution_message}')

async def register_participant(message):
    distribution_parts = message.content.split(" /")
    if len(distribution_parts) < 4:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !사다리 /참여 /[상품번호] /[신청자]\n'
        warning_message += '상품 번호를 모르신다면 [!사다리 /현황] 명령어를 통해 확인해주세요\n'
        await message.channel.send(warning_message)
        return
    price_number = int(distribution_parts[2])
    participant = distribution_parts[3]

    kst = pytz.timezone('Asia/Seoul')
    now_utc = datetime.now(pytz.utc)
    registered_time = now_utc.astimezone(kst)
    remain_time = distribution_item_table[price_number]['사다리 종료 시간'] - registered_time
    time_diff = (remain_time).total_seconds()
    
    if time_diff < 0:
        await message.channel.send('사다리타기 종료된 상품입니다!')
        return
    
    if participant not in distribution_item_table[price_number]['신청자']:
        distribution_item_table[price_number]['신청자'].append(participant)
    register_message = '사다리타기 신청이 완료되었습니다!:\n\n'
    register_message += '상품 정보:\n'
    register_message += f'- 상품번호: {price_number}\n'
    register_message += f'- 아이템명: {distribution_item_table[price_number]['아이템명']}\n'
    register_message += f'- 등록자: {distribution_item_table[price_number]['등록자']}\n'
    register_message += f'- 참가 신청자: {distribution_item_table[price_number]['신청자']}\n\n'
    await message.channel.send(register_message)

async def register_multiple_participant(message):
    distribution_parts = message.content.split(" /")
    if len(distribution_parts) < 4:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !사다리 /복수참여 /[상품번호] /[신청자(스페이스바로 구분)]\n'
        warning_message += '상품 번호를 모르신다면 [!사다리 /현황] 명령어를 통해 확인해주세요\n'
        await message.channel.send(warning_message)
        return
    price_number = int(distribution_parts[2])
    participants = distribution_parts[3]
    participants_list = participants.split(" ")
    
    for participant in participants_list:
        if participant not in distribution_item_table[price_number]['신청자']:
            distribution_item_table[price_number]['신청자'].append(participant)
    register_message = '사다리타기 복수 참여자 신청이 완료되었습니다!:\n\n'
    register_message += '상품 정보:\n'
    register_message += f'- 상품번호: {price_number}\n'
    register_message += f'- 아이템명: {distribution_item_table[price_number]['아이템명']}\n'
    register_message += f'- 등록자: {distribution_item_table[price_number]['등록자']}\n'
    register_message += f'- 참가 신청자: {distribution_item_table[price_number]['신청자']}\n\n'
    await message.channel.send(register_message)

async def play_ladder_game(message, players, price_number):
    num_players = len(players)
    min_lines = num_players * 3
    max_lines = num_players * 5
    num_lines = random.randint(min_lines, max_lines)

    horizontal_counts = [0] * (num_players - 1)
    max_per_column = (min_lines + max_lines) // 4

    ladder = [[0] * (num_players - 1) for _ in range(num_lines)]
    for i in range(1, num_lines - 1):
        available_positions = []
        for j in range(num_players - 1):
            if ladder[i][j] == 0 and (j == 0 or ladder[i][j-1] == 0) and horizontal_counts[j] < max_per_column:
                available_positions.append(j)

        if available_positions:
            chosen_position = random.choice(available_positions)
            ladder[i][chosen_position] = 1
            horizontal_counts[chosen_position] += 1

    result = ['O'] + ['X'] * (num_players - 1)
    random.shuffle(result)

    start_position = result.index('O')
    position = start_position
    winning_path = []

    for row in range(num_lines):
        if position > 0 and ladder[row][position - 1] == 1:
            winning_path.append((row, position - 1, position))
            position -= 1
        elif position < num_players - 1 and ladder[row][position] == 1:
            winning_path.append((row, position, position + 1))
            position += 1
        winning_path.append((row, position, position))

    plt.figure(figsize=(8, 6))
    plt.title("RESULT")

    for i in range(num_players):
        for row in range(num_lines):
            color = 'red' if (row, i, i) in winning_path else 'black'
            linewidth = 4 if color == 'red' else 2
            next_row = row + 1 if row < num_lines - 1 else num_lines
            plt.plot([i, i], [num_lines - row, num_lines - next_row], color=color, linewidth=linewidth)

    for row, start, end in winning_path:
        if start != end:
            plt.plot([start, end], [num_lines - row, num_lines - row], color='red', linewidth=4)
    for row in range(num_lines):
        for col in range(num_players - 1):
            if ladder[row][col] == 1 and (row, col, col + 1) not in [(r, s, e) for r, s, e in winning_path]:
                plt.plot([col, col + 1], [num_lines - row, num_lines - row], color='black', linewidth=2)

    player_labels = list(range(0, len(players)))
    plt.gca().set_xticks(range(num_players))
    plt.gca().set_xticklabels(player_labels, rotation=0)
    plt.gca().tick_params(axis='x', which='both', bottom=False, top=True, labelbottom=False, labeltop=True)

    for i in range(num_players):
        plt.text(i, num_lines + 1, result[i], horizontalalignment='center', verticalalignment='center')

    plt.yticks([])
    plt.gca().invert_yaxis()
    image_path = f"ladder_{price_number}.png"
    plt.savefig(image_path)

    winner_message = "사다리 타기 결과:\n"
    winner_message += f'- 우승자: "{players[position]}" 축하합니다! \n'
    
    await message.channel.send(winner_message)
    await message.channel.send(file=discord.File(image_path))
    os.remove(image_path)

async def register_auction_item(message):
    auction_parts = message.content.split(" /")
    if len(auction_parts) < 5:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !경매 /등록 /[아이템명(띄어쓰기x)] '
        warning_message += '/[최소금액] /[경매 진행시간(분)] /[판매자]'
        await message.channel.send(warning_message)
        return
    item_name = auction_parts[2]
    item_price = auction_parts[3]
    item_auction_time = auction_parts[4]
    seller = auction_parts[5]
    registered_number_count = 1
    while (registered_number_count in auction_item_table.keys()):
        registered_number_count += 1
    price_number = registered_number_count

    kst = pytz.timezone('Asia/Seoul')
    now_utc = datetime.now(pytz.utc)
    registered_time = now_utc.astimezone(kst)
    end_time = registered_time + timedelta(minutes=int(item_auction_time))

    auction_item_table[price_number] = {
        '아이템명': item_name,
        '최고 금액': item_price,
        '경매 시작 시간': registered_time,
        '경매 종료 시간': end_time,
        '판매자': seller,
        '입찰자': None
    }
    auction_message = '경매 상품이 등록되었습니다\n'
    auction_message += '상품 정보:\n'
    auction_message += f'- 상품번호: {price_number}\n'
    auction_message += f'- 아이템명: {item_name}\n'
    auction_message += f'- 판매자: {item_name}\n'
    auction_message += f'- 시작 금액: {item_price}\n'
    auction_message += f'- 경매 시작 시간: {registered_time.strftime('%m월 %d일 %H시 %M분')}\n'
    auction_message += f'- 경매 종료 시간: {end_time.strftime('%m월 %d일 %H시 %M분')}\n'
    if price_number in auction_tasks:
        print(f'Auction task for {price_number} exists. Checking if done...')  # 디버깅: task 존재 확인
        if not auction_tasks[price_number].done():
            print(f'Task for {price_number} not done. Cancelling...')  # 디버깅: task 상태 확인
            auction_tasks[price_number].cancel()
        else:
            print(f'Task for {price_number} already completed.')  # 디버깅: task 완료 확인

    print(f'Creating task for {price_number} auction')  # 태스크 생성 확인
    auction_tasks[price_number] = asyncio.create_task(schedule_auction(price_number, message, end_time))
    await message.channel.send(f'{auction_message}')

async def schedule_auction(price_number, message, end_time):
    try:
        kst = pytz.timezone('Asia/Seoul')
        now_utc = datetime.now(pytz.utc)
        now_kst = now_utc.astimezone(kst)
        delay = (end_time - now_kst).total_seconds()
        target_info = auction_item_table[price_number]
        if delay > 0:
            await asyncio.sleep(delay)
            if target_info['입찰자']:
                auction_result_message = '경매가 종료되었습니다! 입찰에 성공하신분 축하합니다!\n'
                auction_result_message += f'- 상품번호: {price_number}\n'
                auction_result_message += f'- 아이템명: {target_info['아이템명']}\n'
                auction_result_message += f'- 판매자: {target_info['판매자']}\n'
                auction_result_message += f'- 구매자: {target_info['입찰자']}\n'
                auction_result_message += f'- 입찰 금액: {target_info['최고 금액']}\n'
                auction_result_message += f'- 경매 종료 시간: {target_info['경매 종료 시간'].strftime('%m월 %d일 %H시 %M분')}\n'
                del auction_item_table[price_number]
                await message.channel.send(auction_result_message)
            else:
                auction_result_message = '입찰자가 등록되지 않아 판매에 실패했습니다! 다시 등록해주세요\n'
                auction_result_message += f'- 상품번호: {price_number}\n'
                auction_result_message += f'- 아이템명: {target_info['아이템명']}\n'
                auction_result_message += f'- 판매자: {target_info['판매자']}\n'
                auction_result_message += f'- 입찰 금액: {target_info['최고 금액']}\n'
                auction_result_message += f'- 경매 종료 시간: {target_info['경매 종료 시간'].strftime('%m월 %d일 %H시 %M분')}\n'
                del auction_item_table[price_number]
                await message.channel.send(auction_result_message)

        else:
            await message.channel.send('잘못 된 시간 등록입니다')
    except Exception as e:
        await message.channel.send(f'경매 알림 설정 오류: {str(e)}')

async def show_auction_status(message):
    auction_message = '현재 경매 현황:\n'
    for price_number, infos in auction_item_table.items():
        auction_message += '상품 정보:\n'
        auction_message += f'- 상품번호: {price_number}\n'
        auction_message += f'- 아이템명: {infos['아이템명']}\n'
        auction_message += f'- 판매자: {infos['판매자']}\n'
        auction_message += f'- 입찰자: {infos['입찰자']}\n'
        auction_message += f'- 최고 금액: {infos['최고 금액']}\n'
        auction_message += f'- 경매 시작 시간: {infos['경매 시작 시간'].strftime('%m월 %d일 %H시 %M분')}\n'
        auction_message += f'- 경매 종료 시간: {infos['경매 종료 시간'].strftime('%m월 %d일 %H시 %M분')}\n'
        kst = pytz.timezone('Asia/Seoul')
        now_utc = datetime.now(pytz.utc)
        registered_time = now_utc.astimezone(kst)
        remain_time = infos['경매 종료 시간'] - registered_time
        total_seconds = remain_time.total_seconds()

        total_seconds = abs(total_seconds)

        minutes, seconds = divmod(total_seconds, 60)
        auction_message += f'- 남은 경매 시간: {int(minutes)}분 {seconds}초\n\n'

    await message.channel.send(f'{auction_message}')

async def register_auction_participant(message):
    auction_parts = message.content.split(" /")
    if len(auction_parts) < 5:
        warning_message = ''
        warning_message += '명령어 형식이 올바르지 않습니다.\n'
        warning_message += '올바른 형식: !경매 /참여 /[상품번호] /[희망금액] /[구매자] \n'
        warning_message += '상품 번호를 모르신다면 [!경매 /현황] 명령어를 통해 확인해주세요\n'
        await message.channel.send(warning_message)
        return
    price_number = int(auction_parts[2])
    price_cost = int(auction_parts[3])
    participant = auction_parts[4]

    kst = pytz.timezone('Asia/Seoul')
    now_utc = datetime.now(pytz.utc)
    registered_time = now_utc.astimezone(kst)
    remain_time = auction_item_table[price_number]['경매 종료 시간'] - registered_time
    time_diff = (remain_time).total_seconds()
    
    if time_diff < 0:
        await message.channel.send('경매 종료된 상품입니다!')
        return
    
    if int(price_cost) > int(auction_item_table[price_number]['최고 금액']):
        past_price_cost = auction_item_table[price_number]['최고 금액']
        auction_item_table[price_number]['최고 금액'] = price_cost
        auction_item_table[price_number]['입찰자'] = participant
        auction_message = f'"{participant}" 님께서 입찰에 성공하셨습니다!\n'
        auction_message += f'- 상품번호: {price_number}\n'
        auction_message += f'- 아이템명: {auction_item_table[price_number]['아이템명']}\n'
        auction_message += f'- 입찰 금액: {price_cost}\n'
        auction_message += f'- 금액 변동: {past_price_cost} -> {auction_item_table[price_number]['최고 금액']}\n'
        auction_message += f'- 경매 종료 시간: {auction_item_table[price_number]['경매 종료 시간'].strftime('%m월 %d일 %H시 %M분')}\n'
        total_seconds = remain_time.total_seconds()

        total_seconds = abs(total_seconds)

        minutes, seconds = divmod(total_seconds, 60)
        auction_message += f'- 남은 경매 시간: {int(minutes)}분 {seconds}초\n'
        await message.channel.send(auction_message)
    else:
        await message.channel.send(f'입력하신 금액이 현재 최고 금액보다 적습니다! 금액을 다시 설정해주세요')


# Heroku에서 환경 변수를 사용하여 토큰을 저장하므로 아래와 같이 사용합니다.
TOKEN = os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
