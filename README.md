# my-chatglm2

my-chatglm2 是基于 [chatglm2](https://github.com/THUDM/ChatGLM2-6B) 的 API 服务端 + 客户端一键启动方案。

欢迎 issues 留言交流。

## 特性

- 支持引导词（让 AI 的回答按固定内容开头）
- 专属网页/桌面客户端 [docile-chatty](https://github.com/yuri2peter/docile-chatty)
- 专为 windows 设计的懒人包，小白也能放心玩耍
- 支持流式 API
- 支持生成时主动打断
- 自动限制输入长度，拒绝意外爆显存
- 预定义大、中、小三档显存的启动脚本

## API

### GET /

描述：返回服务器已启动的消息
请求参数：无
返回结果：

```json
{
  "message": "Server started",
  "success": true
}
```

### POST /stream

描述：流式生成
请求参数：

```ts
interface Params {
  query: string; // prompt
  answer_prefix: string; // 引导词
  max_length: string; // token上限
  history: Array<[string, string]>; // 对话历史
  top_p: number;
  temperature: number;
}
```

返回结果：

```ts
type EventData = [string, Array<[string, string]>]; // 回复,对话历史
```

### POST /interrupt

描述：打断当前的生成
请求参数：无
返回结果：

```json
{
  "message": "OK",
  "success": true
}
```

### POST /tokenize

描述：使用 tokenizer 分解字符串，统计 token 数目
请求参数：

```ts
interface Params {
  text: string;
  return_tokens?: boolean; // 是否返回分解后的token列表
}
```

返回结果：

```ts
type Returns = {
  tokens: string[]; // 分词结果,
  len: number; //token数目
};
```

## 安装

仅在未使用懒人包、整合包、环境补丁或依赖有问题的情况下需要重新安装。

1. 确保国际网络畅通
2. 确保 python 独立环境（见下文）正常
3. 检查 `requirements.txt` 依赖是否正确
4. 执行 `setup_offline.bat` 安装依赖
5. 运行 `开启API服务.bat`，程序将自动下载模型并运行

## python 独立环境

1. 下载 [python3.10.10 离线包](https://www.python.org/ftp/python/3.10.10/python-3.10.10-embed-amd64.zip)

2. 解压到 `./system/python` 目录下
3. 下载 [get-pip.py](https://bootstrap.pypa.io/get-pip.py) 保存到 `./system/python` 目录下
4. *[必做]*解压之后，删除 `./system/python/python310._pth` 文件，以解决安装依赖的问题。
5. 执行 `setup_offline.bat` 安装依赖

## 获取模型

程序目前自动下载并读取 chatglm2-6b 模型。您也可以手动[下载模型](https://huggingface.co/THUDM/chatglm2-6b/tree/main)并放置到 `THUDM/chatglm2-6b`目录下。

## 显存占用测试（不完全）

| 量化(BIT) | 空载  | 1024 tokens |
| --------- | ----- | ----------- |
| 4         | -     | -           |
| 8         | 7.6 G | 8.8 G       |
| 16        | -     | -           |

> 1024 个 token 约等于 1640 个中文字符，或者 3980 个英文字符

## 协议

沿用 chatglm2 的使用协议。

## 问题记录

- 本地模型读取时提示路径错误？transformers 版本限制到 4.26.1 试试。
