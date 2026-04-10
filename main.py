import requests
from fastapi import FastAPI, Request, Query
import uvicorn
import hashlib

# -------------------------- 👇 只改这5个地方！👇 --------------------------
COZE_API_URL = "https://q3z3fmtgfc.coze.site/stream_run"  # 你扣子的API地址，不用改
COZE_API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdlOTQ2MGFjLWM5NjYtNGE5Ny1iYTk1LTU2YjVmMzVhYTc4NSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIm4wSkpFZzltWlZvbEZQNGZlVGQ5bHBua2Q5YXM5SVlPIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc1ODE1MTk0LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjI2NzE3NDI0MTU0MzEyNzQ0Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjI3MDY4MTg0NzUwNzE5MDI4In0.MDvR4tOfoHOHJcQrBmukspDfAQqX0v4Dmkzv6U_0AFty4zBjCFsKv7ZfSjLRybOsLb904T6un5nIPz-tMgeonrgBFrgZjxNw4ojMsfod2UUpgM028Eum89rEKEn_1gdJj3-Uu3kH00m61xckXgpJFKtHlqWVYH8U-WPkuecc7AmEe0M3HFRCJF2YcLjLCe3oRUwdvd5-9G6ado4WzqNL8R3Sy05_XxfvOctuF6fQO6FX2POmsoM-tMu7A8JUNZpfEHm7Kwis2apb8EloPJI_5DA7UmjxIF9tb4pB20NewCg5-_EQaQYFRpnsDj_qARayDapTQc0NwfBVOu4BO65mBA"  # 扣子API页面复制的完整密钥
COZE_PROJECT_ID = "7626710542341849128"  # 你扣子的项目ID，不用改

WXWORK_CORPID = "ww33685020ebcf1337"  # 企微管理后台「我的企业」里的企业ID
WXWORK_AGENT_SECRET = "vUtd_4BCFU-FvxjXrJcsL5NZdgQPohms-uP4Z2EDgDw"  # 企微应用详情页的Secret
WXWORK_AGENTID = "1000002"  # 企微应用详情页的AgentId
WXWORK_TOKEN = "vUgdEiRTrzXkkqjCtGTsupDQWbPgq"  # ✅ 必须和你企微页面的Token完全一致！
ROBOT_NAME = "亚当"  # 你的AI机器人名字，和企微应用名完全一致
# -------------------------- 👆 改完这里就不用动了！👆 --------------------------

app = FastAPI()

# 企业微信验证回调地址（新增！就是这个之前漏掉了）
@app.get("/wxwork/callback")
async def wxwork_verify(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    # 计算签名验证
    tmp_list = sorted([WXWORK_TOKEN, timestamp, nonce])
    tmp_str = "".join(tmp_list).encode("utf-8")
    tmp_sign = hashlib.sha1(tmp_str).hexdigest()
    
    if tmp_sign == msg_signature:
        return int(echostr)
    return "验证失败"

# 获取企微访问令牌（自动刷新，不用管）
def get_wx_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={WXWORK_CORPID}&corpsecret={WXWORK_AGENT_SECRET}"
    return requests.get(url).json()["access_token"]

# 调用扣子AI（完全适配你这个「亚当」智能体）
def call_coze(prompt: str, session_id: str):
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "content": {
            "query": [
                {
                    "type": "text",
                    "content": {
                        "text": prompt
                    }
                }
            ]
        },
        "type": "query",
        "session_id": session_id,
        "project_id": COZE_PROJECT_ID
    }
    response = requests.post(COZE_API_URL, headers=headers, json=data)
    # 提取AI回复内容
    return response.json()["data"]["response"]["text"]

# 接收微信群@消息，自动回复
@app.post("/wxwork/callback")
async def wxwork_callback(request: Request):
    data = await request.json()
    # 只响应@「亚当」的消息，不@不说话
    if f"@{ROBOT_NAME}" not in data.get("Content", ""):
        return {"Errcode": 0, "Errmsg": "ok"}
    
    user_id = data["FromUserName"]
    message = data["Content"].replace(f"@{ROBOT_NAME}", "").strip()
    # 用用户ID当会话ID，保证每个人的记忆独立不串台
    session_id = f"wx_{user_id}"
    
    # 调用AI生成回复
    reply = call_coze(message, session_id)
    
    # 把回复发到微信群
    token = get_wx_token()
    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    send_data = {
        "chatid": data["ChatId"],
        "msgtype": "text",
        "agentid": WXWORK_AGENTID,
        "text": {"content": reply}
    }
    requests.post(send_url, json=send_data)
    return {"Errcode": 0, "Errmsg": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
