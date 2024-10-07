from datetime import datetime, timedelta
import feedparser
import requests
import base64
import json
import hashlib
import re

flag = True
# 国外赛事更新:

rssUpcoming = 'https://ctftime.org/event/list/upcoming/rss/'
rssActive = 'https://ctftime.org/event/list/archive/rss/'
rssNowrunning = 'https://ctftime.org/event/list/running/rss/'

def fetch_global_ctf_content(rss_url):
    feed = feedparser.parse(rss_url)
    events = []  
    try:
        feedTitle = feed['feed']['title']
    except KeyError:
        print('RSS源解析失败，请检查URL是否正确')
        flag = False
        return False

    for entry in feed.entries:

        eventName = entry.title

        # 时间处理部分
        start_date = datetime.strptime(entry.start_date, '%Y%m%dT%H%M%S')
        finish_date = datetime.strptime(entry.finish_date, '%Y%m%dT%H%M%S')
        start_date_utc8 = start_date + timedelta(hours=8)
        finish_date_utc8 = finish_date + timedelta(hours=8)
        time_range = f'{start_date_utc8.strftime("%Y-%m-%d %H:%M:%S")} - {finish_date_utc8.strftime("%Y-%m-%d %H:%M:%S")} UTC+8'
        eventTime = time_range

        # 添加日历部分
        calendar_start_index = entry.description.find('[add to calendar]')
        if calendar_start_index != -1:
            calendar_end_index = entry.description.find('</a>', calendar_start_index)
            calendar_link_start_index = entry.description.rfind('href="', 0, calendar_start_index) + 6
            calendar_link = entry.description[calendar_link_start_index:calendar_end_index]
            calendar_link = calendar_link.replace('">[add to calendar]','')
            addCalendar = calendar_link
        else:
            addCalendar = None

        # 主办方部分
        organizers_data = json.loads(entry.organizers)
        organizers_names = []
        organizers_urls = []
        for organizer in organizers_data:
            name = organizer['name']
            url = 'https://ctftime.org/team/' + str(organizer['id'])
            organizers_names.append(name)
            organizers_urls.append(url)
        organizers_names_str = ', '.join(organizers_names)
        organizers_urls_str = ', '.join(organizers_urls)

        eventUrl = entry.url
        eventName = f'{eventName}'
        eventType = entry.format_text
        eventLogo = 'https://ctftime.org' + entry.logo_url
        eventWeight = entry.weight
        eventOrganizers =  f'{organizers_names_str} ({organizers_urls_str})'
        
        eventData= {
                    '比赛名称': eventName,
                    '比赛时间': eventTime,
                    '添加日历': addCalendar,
                    '比赛形式': eventType,
                    '比赛链接': eventUrl,
                    '比赛标志': eventLogo,
                    '比赛权重': eventWeight,
                    '赛事主办': eventOrganizers,
                    '比赛ID' : entry.ctf_id,
                    '比赛状态': ''
                }
        if rss_url == rssUpcoming:
            eventData['比赛状态'] = 'oncoming'
        elif rss_url == rssActive:
            eventData['比赛状态'] = 'past'
        elif rss_url == rssNowrunning:
            eventData['比赛状态'] = 'nowrunning'

        events.append(eventData)

    return events

upcoming_events = fetch_global_ctf_content(rssUpcoming)
active_events = fetch_global_ctf_content(rssActive)
running_events = fetch_global_ctf_content(rssNowrunning)
all_events = None

if False not in [upcoming_events, active_events, running_events]:
    all_events = upcoming_events + running_events + active_events
    with open('Global.json', 'w', encoding='utf-8') as file:
        json.dump(all_events, file, ensure_ascii=False, indent=4)
    print("国际赛事数据已更新至Global.json")
else:
    print("国际赛事数据更新失败")


# 国内赛事状态更新

with open('./CN.json', 'r', encoding='utf-8') as f:
    CN = json.load(f)

date = datetime.now() + timedelta(hours=8)

# 更新状态

with open('Achieve/CN_archive.json', 'r', encoding='utf-8') as file:
    archive = json.load(file)

for event in CN['data']['result']:
    reg_time_start = datetime.strptime(event['reg_time_start'], '%Y年%m月%d日 %H:%M')
    reg_time_end = datetime.strptime(event['reg_time_end'], '%Y年%m月%d日 %H:%M')
    comp_time_start = datetime.strptime(event['comp_time_start'], '%Y年%m月%d日 %H:%M')
    comp_time_end = datetime.strptime(event['comp_time_end'], '%Y年%m月%d日 %H:%M')
    
    if date < comp_time_start:
        event['status'] = "即将开始"
    elif date < comp_time_end:
        event['status'] = "正在就行"
    elif date > comp_time_end:
        event['status'] = "已经结束"
        
        comp_time_end = datetime.strptime(event['comp_time_end'], '%Y年%m月%d日 %H:%M')
        if date > comp_time_end + timedelta(days=60):
            print(event['name'] + "已结束超过60天，移至存档")
            archive['archive']['result'].append(event)
            CN['data']['result'].remove(event)

    if date >= bsks and date < bsjs: # 单独判断一下是否正在进行中，进行中的优先级 > 报名中
        event['status'] = 3 # 进行中

        
# 更新存档
            
with open('Achieve/CN_archive.json', 'w', encoding='utf-8') as file:
    json.dump(archive, file, ensure_ascii=False, indent=4)
        
status_order = {
    '即将开始': 0,
    '正在进行': 1,
    '已经结束': 2
}
# 状态排序
CN['data']['result'] = sorted(CN['data']['result'], key=lambda x: status_order[x['status']])

with open('./CN.json', 'w', encoding='utf-8') as f:
    json.dump(CN, f, ensure_ascii=False, indent=4)

if all_events == None:
    with open('Global.json', 'r', encoding='utf-8') as f:
        all_events = json.load(f)
        
# 生成国内比赛的日历订阅内容
def create_CN_ical_event(event):
    start_date = datetime.strptime(event['comp_time_start'], '%Y年%m月%d日 %H:%M') - timedelta(hours=8)
    finish_date = datetime.strptime(event['comp_time_end'], '%Y年%m月%d日 %H:%M') - timedelta(hours=8)
    start_date_utc8 = start_date
    finish_date_utc8 = finish_date
    eventData= {
                'BEGIN':'VEVENT',
                'SUMMARY':event['name'],
                'DTSTART':start_date_utc8.strftime("%Y%m%dT%H%M%SZ"),
                'DTEND':finish_date_utc8.strftime("%Y%m%dT%H%M%SZ"),
                'UID':hashlib.md5(event['name'].encode('utf-8')).hexdigest(),
                'VTIMEZONE':'Asia/Shanghai',
                'DTSTAMP':datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                'CREATED':datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                'URL':event['link'],
                'DESCRIPTION':event['type']+' | '+event['link']+' | '+' | '+'报名---'+event['reg_time_start']+'-'+event['reg_time_end']+'-备注-'+re.sub(r"\s+", "", event['readmore']),
                'END':'VEVENT'
            }
    return eventData

# 生成国外比赛的日历订阅内容

def create_Global_ical_event(event):
    start_date = event['比赛时间'].split(' - ')[0]
    finish_date = event['比赛时间'].split(' - ')[1].replace(' UTC+8', '')
    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
    finish_date = datetime.strptime(finish_date, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
    eventData= {
                'BEGIN':'VEVENT',
                'SUMMARY':event['比赛名称'],
                'DTSTART':start_date.strftime("%Y%m%dT%H%M%SZ"),
                'DTEND':finish_date.strftime("%Y%m%dT%H%M%SZ"),
                'UID':hashlib.md5(event['比赛名称'].encode('utf-8')).hexdigest(),
                'VTIMEZONE':'Asia/Shanghai',
                'DTSTAMP':datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                'CREATED':datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                'URL':event['比赛链接'],
                'DESCRIPTION':event['比赛形式']+' | '+event['比赛链接']+' | '+' | '+'比赛ID - '+str(event['比赛ID']),
                'END':'VEVENT'
            }
    return eventData

# 生成国内赛事日历
CN_ical_events = []
for event in CN['data']['result']:
    CN_ical_events.append(create_CN_ical_event(event))

with open('./calendar/CN.ics', 'w', encoding='utf-8') as f:
    f.write('BEGIN:VCALENDAR\n')
    f.write('VERSION:2.0\n')
    f.write('PRODID:-//CTF//CN//\n')
    f.write('CALSCALE:GREGORIAN\n')
    f.write('X-WR-CALNAME:CN\n')
    for event in CN_ical_events:
        for key, value in event.items():
            f.write(f'{key}:{value}\n')
        f.write('\n')
    f.write('END:VCALENDAR')

# 生成国际赛事日历
Global_ical_events = []
for event in all_events:
    Global_ical_events.append(create_Global_ical_event(event))

with open('./calendar/Global.ics', 'w', encoding='utf-8') as f:
    f.write('BEGIN:VCALENDAR\n')
    f.write('TZID:Asia/Shanghai\n')
    f.write('VERSION:2.0\n')
    f.write('PRODID:-//CTF//Global//\n')
    f.write('CALSCALE:GREGORIAN\n')
    f.write('X-WR-CALNAME:Global\n')
    for event in Global_ical_events:
        for key, value in event.items():
            f.write(f'{key}:{value}\n')
        f.write('\n')
    f.write('END:VCALENDAR')

# 将Global.json 和 CN.json 通过Base64编码后存储为 Global.b64 以供大陆用户使用
with open('Global.json', 'r', encoding='utf-8') as f:
    Global = f.read()
    Global = Global.encode('utf-8')
    Global = base64.b64encode(Global).decode('utf-8')
    with open('Global.b64', 'w', encoding='utf-8') as f:
        f.write(Global)

with open('CN.json', 'r', encoding='utf-8') as f:
    CN = f.read()
    CN = CN.encode('utf-8')
    CN = base64.b64encode(CN).decode('utf-8')
    with open('CN.b64', 'w', encoding='utf-8') as f:
        f.write(CN)  
