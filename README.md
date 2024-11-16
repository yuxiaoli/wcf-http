# wcf-http

基于 [wcferry](https://pypi.org/project/wcferry/) 封装的 HTTP 客户端。

- GitHub: [https://github.com/yuxiaoli/wcf-http](https://github.com/yuxiaoli/wcf-http)
- PyPI: [https://pypi.org/project/wcf-http-server/](https://pypi.org/project/wcf-http-server/)

Python HTTP server for [WeChatFerry](https://github.com/lich0821/WeChatFerry) [v39.2.4](https://github.com/lich0821/WeChatFerry/releases/tag/v39.2.4)，适配微信 3.9.10.27 [WeChatSetup-3.9.10.27.exe](https://github.com/lich0821/WeChatFerry/releases/download/v39.2.4/WeChatSetup-3.9.10.27.exe)

## 安装

```sh
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -U wcf-http-server
```

## 运行

```sh
# 查看版本
wcfhttp -v

# 查看帮助
wcfhttp -h

usage: wcfhttp [-h] [-v] [--wcf_host WCF_HOST] [--wcf_port WCF_PORT]
               [--wcf_debug WCF_DEBUG] [--host HOST] [--port PORT] [--cb CB]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --wcf_host WCF_HOST   WeChatFerry 监听地址，默认本地启动监听 0.0.0.0
  --wcf_port WCF_PORT   WeChatFerry 监听端口 (同时占用 port + 1 端口)，默认 10086
  --wcf_debug WCF_DEBUG 是否打开 WeChatFerry 调试开关
  --host HOST           wcfhttp 监听地址，默认监听 0.0.0.0
  --port PORT           wcfhttp 监听端口，默认 9999
  --cb CB               接收消息回调地址

# 忽略新消息运行
wcfhttp

# 新消息转发到指定地址
wcfhttp --cb http://host:port/callback
```

## 接收消息回调接口文档

参考文档（默认地址为：[http://localhost:9999/docs](http://localhost:9999/docs)）接收消息回调样例。

更多关于回调的介绍可以参考这篇文章：[回调到底是什么？](https://mp.weixin.qq.com/s?__biz=MzI0MjI1OTk0OQ==&mid=2247487514&idx=1&sn=fbc2275eb1bdf8e28193f2134307a43c&scene=21#wechat_redirect)

