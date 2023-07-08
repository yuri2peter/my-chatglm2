import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import argparse
import logging
import json
import sys
from my_model import get_tokenizer_and_model
from my_utils import inputs_length_fixer

# 文本token长度上限(该上限同时对输入和输出起作用，如果输入太长，剩余的输出字数就会减少)
# 该参数只能限制输出效果
# 该参数并不能防止输入过长导致爆显存
MAX_LENGTH = 2048

# 中断控制
allow_generate = [True]

# 默认端口号
DEFAULT_PORT = 5178


# 接入log
def getLogger(name, file_name, use_formatter=True):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s    %(message)s")
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    if file_name:
        handler = logging.FileHandler(file_name, encoding="utf8")
        handler.setLevel(logging.INFO)
        if use_formatter:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
            handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = getLogger("ChatGLM", "chatlog.log")
sessionIndexHandle = [0]


# 接入FastAPI
def start_server(quantize_level, http_address: str, port: int):
    tokenizer, model = get_tokenizer_and_model(quantize_level)

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def alertError(e, sessionIndex):
        logger.error(f"Error {sessionIndex}: {e}")
        yield f"data: {e}\n\n"

    def decorate(generator, sessionIndex, stream=False):
        lastStr = ""
        for item in generator:
            lastStr = item[0]
            if stream:
                yield f"data: {json.dumps({'response': item[0]}, ensure_ascii=False)}\n\n"
        logger.info("Output {} - {}".format(sessionIndex, {"response": lastStr}))
        if not stream:
            yield lastStr

    def generate(
        query,
        answer_prefix,
        max_length,
        history,
        stream,
        top_p,
        temperature,
    ):
        sessionIndexHandle[0] += 1
        sessionIndex = sessionIndexHandle[0]
        max_length = min(max_length, MAX_LENGTH)
        history = [tuple(h) for h in history]
        # inputs_length_fixer对输入的长度进行限制，一定程度上防止了显存超限
        history = inputs_length_fixer(
            tokenizer, query, answer_prefix, history, max_length
        )
        inputs = {
            "sessionIndex": sessionIndex,
            "tokenizer": tokenizer,
            "query": query,
            "answer_prefix": answer_prefix,
            "max_length": max_length,
            "top_p": float(top_p),
            "temperature": float(temperature),
            "allow_generate": allow_generate,
            "history": history,
        }
        # 记录输入日志
        logData = inputs.copy()
        del logData["tokenizer"]
        del logData["allow_generate"]
        logger.info(
            "Inputs {} - {}".format(
                sessionIndex, json.dumps(logData, ensure_ascii=False)
            )
        )
        # 生成并返回
        streamChat = model.my_stream_chat(**inputs)
        if stream:
            return StreamingResponse(
                decorate(streamChat, sessionIndex, stream),
                media_type="text/event-stream",
            )
        else:
            responseText = next(decorate(streamChat, sessionIndex))
            return Response(content=responseText, media_type="text/plain")

    #  返回服务器整体状态
    @app.get("/")
    def index(request: Request):
        return {"message": "Server started", "success": True}

    #  Test
    @app.get("/generate")
    def generate1(
        query="",
        answer_prefix="",
        max_length=MAX_LENGTH,
        history="[]",
        stream=False,
        top_p=0.7,
        temperature=1.0,
    ):
        history = json.loads(history)
        params = {
            "query": query,
            "answer_prefix": answer_prefix,
            "max_length": max_length,
            "history": history,
            "stream": stream,
            "top_p": top_p,
            "temperature": temperature,
        }
        return generate(**params)

    @app.post("/generate")
    def generate2(
        arg_dict: dict,
    ):
        params = {
            "query": arg_dict.get("query", ""),
            "answer_prefix": arg_dict.get("answer_prefix", ""),
            "max_length": arg_dict.get("max_length", MAX_LENGTH),
            "history": arg_dict.get("history", []),
            "stream": arg_dict.get("stream", False),
            "top_p": arg_dict.get("top_p", 0.7),
            "temperature": arg_dict.get("temperature", 1.0),
        }
        return generate(**params)

    # 打断当前的生成
    @app.post("/interrupt")
    def interrupt():
        allow_generate[0] = False
        logger.info("Interrupted.")
        return {"message": "OK", "success": True}

    # 使用tokenizer分解字符串，统计token数目
    @app.post("/tokenize")
    def tokenize(arg_dict: dict):
        text = arg_dict["text"]
        return_tokens = arg_dict.get("return_tokens", False)
        tokens = tokenizer.tokenize(text)
        return {tokens: tokens if return_tokens else [], len: len(tokens)}

    # 启动后提示
    @app.on_event("startup")
    def on_startup():
        print(
            f"\n\033[92mINFO:     \033[93mTry http://{http_address}:{port}/generate?stream=yes&query=Hi\033[0m"
        )

    # 记录启动参数
    logger.info("System - Server started.")
    serverParams = {
        "host": http_address,
        "port": port,
        "quantize_level": quantize_level,
        "max_length": MAX_LENGTH,
    }
    logger.info(f"System - Confgis = { json.dumps(serverParams, ensure_ascii=False)}")

    # 启动web服务
    uvicorn.run(app=app, host=http_address, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream API Service for ChatGLM2-6B")
    parser.add_argument(
        "--quantize", "-q", help="level of quantize, option：0, 8 or 4", default=4
    )
    parser.add_argument("--host", "-H", help="host to listen", default="127.0.0.1")
    parser.add_argument(
        "--port", "-P", help="port of this service", default=DEFAULT_PORT
    )
    args = parser.parse_args()
    start_server(int(args.quantize), args.host, int(args.port))
