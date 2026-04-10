# 纯企业微信验证代码，无任何多余逻辑，明文模式必过！
from fastapi import FastAPI, Query
import uvicorn

app = FastAPI()

# 核心：明文模式直接返回 echostr 字符串！
@app.get("/wxwork/callback")
def verify(echostr: str = Query("")):
    return echostr

# 占位接口
@app.post("/wxwork/callback")
def callback():
    return {"errcode": 0}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
