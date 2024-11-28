#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import os
import threading
import webbrowser
import sys

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
	parse.add_argument("--systray", action="store_true", help="enable system tray icon")  # Added tray option

	logging.basicConfig(level="INFO", format="%(asctime)s %(message)s")
	args = parse.parse_args()
	cb = args.cb
	url = f"http://{args.host.replace('0.0.0.0', '127.0.0.1')}:{args.port}/docs"
	if not cb:
		# logging.warning("没有设置接收消息回调，消息直接通过日志打印；请通过 --cb 设置消息回调")
		logging.warning("没有设置接收消息回调，消息直接通过日志打印；请通过 --cb 或 POST Callback API 设置消息回调")
		logging.warning(f"回调接口规范参考接收消息回调样例：{url}")
	# self.LOG.info(f"Server is running at {url}")
	print(f"Server is running at {url}")

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
				host=args.host.replace('0.0.0.0', '127.0.0.1'),
				port=args.port,
				title="WeChatFerry HTTP 客户端",
				description=f"GitHub: <a href='{github}'>wcf-http</a> | PyPI: <a href='{pypi}'>wcf-http-server</a>{qrcodes}",)

	if args.systray:
		# Attempt to import pystray and other necessary modules
		try:
			# Import necessary modules for the tray icon
			import pystray
			from pystray import MenuItem as item
			from PIL import Image#, ImageDraw
		except ImportError:
			logging.warning("pystray or PIL is not installed. Running server without tray icon.")
			# Run uvicorn server normally
			uvicorn.run(app=http, host=args.host, port=args.port)
			return

		# Function to create an icon image
		def create_image():
			# Get the absolute path of the current file's directory
			current_dir = os.path.dirname(os.path.abspath(__file__))
			return Image.open(os.path.join(current_dir, "assets", "images", 'wcf-http.png'))

		# Global variable to control the server
		global uvicorn_server
		uvicorn_server = None
		exit_event = threading.Event()

		# Function to run uvicorn server
		def run_uvicorn():
			global uvicorn_server
			config = uvicorn.Config(app=http, host=args.host, port=args.port)
			uvicorn_server = uvicorn.Server(config)
			uvicorn_server.run()

		# Start uvicorn server in a separate thread
		server_thread = threading.Thread(target=run_uvicorn)
		server_thread.start()

		# Function to open the documentation webpage
		def on_open(icon, item):
			webbrowser.open(url)

		# Function to exit the application
		def on_exit(icon, item):
			# Stop the uvicorn server
			if uvicorn_server is not None:
				uvicorn_server.should_exit = True
			# Stop the tray icon
			icon.stop()
			# Signal the main thread to exit
			exit_event.set()

		# Create the tray icon and menu
		icon_image = create_image()
		menu = pystray.Menu(
			item('Open API Docs', on_open),
			item('Exit', on_exit)
		)
		icon = pystray.Icon("WeChatFerry", icon_image, "WeChatFerry", menu)

		# Run the tray icon in a separate thread to avoid blocking
		def run_tray_icon():
			icon.run()

		tray_thread = threading.Thread(target=run_tray_icon)
		tray_thread.start()

		# Wait for the exit event
		try:
			exit_event.wait()
		except KeyboardInterrupt:
			pass
		finally:
			# Ensure that the server and tray icon are stopped
			if uvicorn_server is not None:
				uvicorn_server.should_exit = True
			if icon is not None:
				icon.stop()
			# Wait for threads to finish
			server_thread.join()
			tray_thread.join()

	else:
		# Run uvicorn server normally
		uvicorn.run(app=http, host=args.host, port=args.port)


if __name__ == "__main__":
	main()
