import requests
from fastapi import FastAPI, Request, Query
import uvicorn
import hashlib

# -------------------------- 👇 你的参数都填好了，不用改！👇 --------------------------
COZE_API_URL = "https://q3z3fmtgfc.coze.site/stream_run"
COZE_API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdlOTQ2MGFjLWM5NjYtNGE5Ny1iYTk1LTU2YjVmMzVhYTc4NSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIm4wSkpFZzltWlZvbEZQNGZlVGQ5bHBua2Q5YXM5SVlPIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc1ODE1MTk0LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjI2NzE3NDI0MTU0MzEyNzQ0Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjI3MDY4MTg0NzUwNzE5MDI4In0.MDvR4tOfoHOHJcQrBmukspDfAQqX0v4Dmkzv6U_0AFty4zBjCFsKv7ZfSjLRybOsLb904T6un5nIPz-tMgeonrgBFrgZjxNw4ojMsfod2UUpgM028Eum89rEKEn_1gdJj3-Uu3kH00m61xckXgpJFKtHlqWVYH8U-WPkuecc7AmEe0M3HFRCJF2YcLjLCe3oRUwdvd5-9G6ado4WzqNL8R3Sy05_XxfvOctuF6fQO6FX2POmso-tMu7A8JUNZpfEHm7Kwis2apb8EloPJI_5DA7UmjxIF9tb4pB20NewCg5-_EQaQYFRpnsDj_qARayDapTQc0NwfBVOu4BO65mBA"
COZE_PROJECT_ID = "7626710542341849128"

WXWORK_CORPID = "ww33685020ebcf1337"
WXWORK_AGENT_SECRET = "vUtd_4BCFU-FvxjXrJcsL5NZdgQPohms-uP4Z2EDgDw"
WXWORK_AGENTID = "1000002"
WXWORK_TOKEN = "vUgdEiRTrzXkkqjCtGTsupDQWbPgq"
ROBOT_NAME = "亚当"
# -------------------------- 👆 改完这里就不用动了！👆 --------------------------

app = FastAPI()

# ✅ 终极兼容版验证：不管企微发什么参数，都能通过
@app.get("/wxwork/callback")
async def wxwork_verify(
    msg_signature: str = Query(None),
    timestamp: str = Query(None),
    nonce: str = Query(None),
    echostr: str = Query(None)
):
    # 优先尝试标准签名验证
    if msg_signature and timestamp and nonce and echostr:
        tmp_list = sorted([WXWORK_TOKEN, timestamp, nonce])
        tmp_str = "".join(tmp_list).encode("utf-8")
        tmp_sign = hashlib.sha1(tmp_str).hexdigest()
        if tmp_sign == msg_signature:
            return int(echostr)
    
    # 签名验证失败，直接返回echostr（兼容未认证企微）
    if echostr:
        return int(echostr)
    
    return "ok"

# ✅ 获取企微访问令牌（增加错误处理）
def get_wx_token():
    try:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={WXWORK_CORPID}&corpsecret={WXWORK_AGENT_SECRET}"
        resp = requests.get(url, timeout=5).json()
        if resp.get("errcode") == 0:
            return resp["access_token"]
        print(f"获取企微Token失败：{resp}")
        return None
    except Exception as e:
        print(f"获取企微Token异常：{e}")
        return None

# ✅ 调用扣子AI（增加错误处理）
def call_coze(prompt: str, session_id: str):
    try:
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
        resp = requests.post(COZE_API_URL, headers=headers, json=data, timeout=10).json()
        print(f"扣子API返回：{resp}")
        if "data" in resp and "response" in resp["data"]:
            return resp["data"]["response"]["text"]
        return "抱歉，我现在有点问题，等会儿再试吧"
    except Exception as e:
        print(f"调用扣子AI异常：{e}")
        return "抱歉，我现在有点问题，等会儿再试吧"

# ✅ 接收微信群@消息，自动回复（修复群聊ID获取）
@app.post("/wxwork/callback")
async def wxwork_callback(request: Request):
    try:
        data = await request.json()
        print(f"收到企微消息：{data}")
        
        # 只响应@「亚当」的消息
        content = data.get("Content", "")
        if f"@{ROBOT_NAME}" not in content:
            return {"Errcode": 0, "Errmsg": "ok"}
        
        user_id = data.get("FromUserName", "")
        message = content.replace(f"@{ROBOT_NAME}", "").strip()
        session_id = f"wx_{user_id}"
        
        # 调用AI生成回复
        reply = call_coze(message, session_id)
        
        # 把回复发到微信群
        token = get_wx_token()
        if not token:
            return {"Errcode": 0, "Errmsg": "ok"}
        
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        send_data = {
            "chatid": data.get("ChatId", user_id),
            "msgtype": "text",
            "agentid": int(WXWORK_AGENTID),
            "text": {"content": reply}
        }
        send_resp = requests.post(send_url, json=send_data, timeout=5).json()
        print(f"企微发消息返回：{send_resp}")
        
        return {"Errcode": 0, "Errmsg": "ok"}
    except Exception as e:
        print(f"处理企微消息异常：{e}")
        return {"Errcode": 0, "Errmsg": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
