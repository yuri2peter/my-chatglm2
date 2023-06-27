from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from my_utils import inputs_length_fixer
import uvicorn
import argparse
import logging
import json
import sys
from my_model import get_tokenizer_and_model

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

    def decorate(generator, sessionIndex):
        lastStr = ""
        for item in generator:
            lastStr = item[0]
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        logger.info("Output {} - {}".format(sessionIndex, {"response": lastStr}))

    #  返回服务器整体状态
    @app.get("/")
    def index():
        return {"message": "Server started", "success": True}

    #  流式生成
    @app.post("/stream")
    def continue_question_stream(arg_dict: dict):
        sessionIndexHandle[0] += 1
        sessionIndex = sessionIndexHandle[0]
        try:
            query = arg_dict["query"]
            answer_prefix = arg_dict.get("answer_prefix", "")
            max_length = min(arg_dict.get("max_length", MAX_LENGTH), MAX_LENGTH)
            history = arg_dict.get("history", [])
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
                "top_p": float(arg_dict.get("top_p", 0.7)),
                "temperature": float(arg_dict.get("temperature", 1.0)),
                "allow_generate": allow_generate,
                "history": history,
            }

            logData = inputs.copy()
            del logData["tokenizer"]
            del logData["allow_generate"]

            logger.info(
                "Inputs {} - {}".format(
                    sessionIndex, json.dumps(logData, ensure_ascii=False)
                )
            )
            return StreamingResponse(
                decorate(model.my_stream_chat(**inputs), sessionIndex)
            )
        except Exception as e:
            return StreamingResponse(alertError(e, sessionIndex))

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

    logger.info("System - Server started.")
    serverParams = {
        "host": http_address,
        "port": port,
        "quantize_level": quantize_level,
        "max_length": MAX_LENGTH,
    }
    logger.info(f"System - Confgis = { json.dumps(serverParams, ensure_ascii=False)}")
    uvicorn.run(app=app, host=http_address, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream API Service for ChatGLM2-6B")
    parser.add_argument(
        "--quantize", "-q", help="level of quantize, option：16, 8 or 4", default=4
    )
    parser.add_argument("--host", "-H", help="host to listen", default="0.0.0.0")
    parser.add_argument(
        "--port", "-P", help="port of this service", default=DEFAULT_PORT
    )
    args = parser.parse_args()
    start_server(int(args.quantize), args.host, int(args.port))
