#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import os

import uvicorn
from wcferry import Wcf
# from wcfhttp import Http, __version__
from wcf_http.core import Http, __version__


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument("-v", "--version", action="version", version=f"{__version__}")
    parse.add_argument("--wcf_host", type=str, default=None, help="WeChatFerry 监听地址，默认本地启动监听 0.0.0.0")
    parse.add_argument("--wcf_port", type=int, default=10086, help="WeChatFerry 监听端口 (同时占用 port + 1 端口)，默认 10086")
    parse.add_argument("--wcf_debug", type=bool, default=True, help="是否打开 WeChatFerry 调试开关")
    parse.add_argument("--host", type=str, default="0.0.0.0", help="wcfhttp 监听地址，默认监听 0.0.0.0")
    parse.add_argument("--port", type=int, default=9999, help="wcfhttp 监听端口，默认 9999")
    parse.add_argument("--cb", type=str, default="", help="接收消息回调地址")

    logging.basicConfig(level="INFO", format="%(asctime)s %(message)s")
    args = parse.parse_args()
    cb = args.cb
    if not cb:
        logging.warning("没有设置接收消息回调，消息直接通过日志打印；请通过 --cb 设置消息回调")
        logging.warning(f"回调接口规范参考接收消息回调样例：http://{args.host}:{args.port}/docs")

    # Create the log directory as a quick fix for https://github.com/lich0821/WeChatRobot/issues/70
    # Fixed in https://github.com/lich0821/WeChatFerry/commit/19079bc468fe6681a65887a42a9215a9ec7392d1
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    wcf = Wcf(args.wcf_host, args.wcf_port, args.wcf_debug)
    # home = "https://github.com/lich0821/WeChatFerry"
    github = "https://github.com/yuxiaoli/wcf-http"
    pypi = "https://pypi.org/project/wcf-http-server/"
    qrcodes = """<table>
<thead>
<tr>
<!-- <th style="text-align:center"><img src="https://s2.loli.net/2023/09/25/fub5VAPSa8srwyM.jpg" alt="碲矿"></th> -->
<!-- <th style="text-align:center"><img src="https://s2.loli.net/2023/09/25/gkh9uWZVOxzNPAX.jpg" alt="赞赏"></th> -->
<th style="text-align:center"><img src="https://api.codetabs.com/v1/proxy/?quest=https://mmbiz.qpic.cn/sz_mmbiz_png/NqSD0p9cbmiauQkiaVZOgmxF2KVTVMsxExocdAscXfqUKSicbBy6kPyQDToeCPwUbqgrSBWr5l8TnaxIwDgwBW7JA/640?wx_fmt=png&from=appmsg" alt="图灵信使"></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:center">
后台回复 <code>wcf-http</code> 加群交流
<!-- <br />如果你觉得有用 -->
</td>
</tbody>
</table>"""
    http = Http(wcf=wcf,
                cb=cb,
                title="WeChatFerry HTTP 客户端",
                description=f"GitHub: <a href='{github}'>wcf-http</a> | PyPI: <a href='{pypi}'>wcf-http-server</a>{qrcodes}",)

    uvicorn.run(app=http, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
