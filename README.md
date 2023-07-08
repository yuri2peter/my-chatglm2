# my-chatglm2

my-chatglm2 是基于 [chatglm2](https://github.com/THUDM/ChatGLM2-6B) 的 API 服务端，搭配了量身定制的客户端和整合包。

欢迎 issues 留言交流，喜欢的话不妨点个免费的星星，谢啦！

<img src="https://github.com/yuri2peter/my-chatglm2/assets/23306626/2fae71f2-faa6-4d2a-97a7-72d548786a59" width="700" />

## 特性

- 支持**引导词**（让 AI 的回答按固定内容开头）
- 专属网页/桌面客户端 [docile-chatty](https://github.com/yuri2peter/docile-chatty)
- 专为 windows 设计的懒人包，小白也能放心玩耍
- 支持流式 API
- 支持生成时主动打断
- 自动限制输入长度，拒绝意外爆显存
- 预定义大、中、小三档显存的启动脚本

## 获取

有两种方式使用 my-chatglm2

1. （推荐）百度网盘下载 [开箱即用整合包](https://pan.baidu.com/s/1auZ14BHjpj5e08sbnkf7lQ?pwd=1tdn)
2. clone 本项目，并参考下文“安装”说明进行安装，适用于动手能力强，有二次开发需求的朋友

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

### POST OR GET /generate

描述：生成文本，支持 GET 和 POST（推荐） 两种方式，可选流式输出。

请求参数：

```ts
interface Params {
  query: string; // prompt
  answer_prefix: string; // 引导词
  max_length: string; // token上限
  history: Array<[string, string]>; // 对话历史
  stream: boolean; // 是否流式输出
  top_p: number;
  temperature: number;
}
```

返回结果：

```
非流式："string"

流式：data: { "response": "string" }
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

## 问题

- 本地模型读取时提示路径错误？transformers 版本限制到 4.26.1 试试。

## 感谢

- [ChatGLM2-6B](https://github.com/THUDM/ChatGLM2-6B)开源如此优秀的语言模型
- [CreativeChatGLM](https://github.com/ypwhs/CreativeChatGLM)提供了诱导词的实现思路

## 版本

- V1.1 2023/07/08 文本输出接口修改为`/generate`，精简输出内容，支持 GET 请求，支持 “常规” / “流式” 两种生成方式。
- V1.0 2023/06/27 第一个版本。
