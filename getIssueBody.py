import re
import json

# 从 .gihub/issues/temp 文件中提取issue_body

with open(".github/issues/temp", "r", encoding="utf-8") as f:
    issue_body = f.read()

def body2json(issue_body):
    print(issue_body)

    result_dict = {}
    
    sections = issue_body.split("###")[1:]  
    sections = [section.strip().split("\n\n", 1) for section in sections] 
    
    for item in sections:
        if len(item) == 2:  
            key, vals = item[0].strip(), item[1].strip()
            if key == "比赛状态":
                match = re.search(r'\d+', vals)
                if match:
                    vals = match.group()
                    vals = int(vals)
            result_dict[key] = vals
    json_data = json.dumps(result_dict, ensure_ascii=False, indent=4).replace("时间", "")
    json_dic = {"赛事名称":"name", "比赛链接":"link", "比赛类型":"type", "报名开始":"bmks", "报名结束":"bmjz", "比赛开始":"bsks", "比赛结束":"bsjs", "备注信息":"readmore", "比赛状态":"status"}
    for key, value in json_dic.items():
        json_data = json_data.replace(key, value)

    print(json_data)

    return json_data

json_data = body2json(issue_body)
with open(f"./ReviewPending/{json.loads(json_data)['name']}.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)