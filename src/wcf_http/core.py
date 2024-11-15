#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import logging
from queue import Empty
from threading import Thread
from typing import Any

import requests
from fastapi import Body, FastAPI, Query
from pydantic import BaseModel
from wcferry import Wcf, WxMsg

__version__ = "39.2.4.0"


class Msg(BaseModel):
	id: int
	ts: int
	sign: str
	type: int
	xml: str
	sender: str
	roomid: str
	content: str
	thumb: str
	extra: str
	is_at: bool
	is_self: bool
	is_group: bool


class Http(FastAPI):
	"""WeChatFerry HTTP 客户端，文档地址：http://IP:PORT/docs"""

	def __init__(self, wcf: Wcf, cb: str, **extra: Any) -> None:
		super().__init__(**extra)
		self.LOG = logging.getLogger(__name__)
		self.LOG.info(f"wcfhttp version: {__version__}")
		self.wcf = wcf
		self._set_cb(cb)
		self.add_api_route("/msg_cb", self.msg_cb, methods=["POST"], summary="接收消息回调样例", tags=["示例"])

		# GET Routes
		self.add_api_route("/login", self.is_login, methods=["GET"], summary="获取登录状态")
		self.add_api_route("/wxid", self.get_self_wxid, methods=["GET"], summary="获取登录账号 wxid")
		self.add_api_route("/user-info", self.get_user_info, methods=["GET"], summary="获取登录账号个人信息")
		self.add_api_route("/msg-types", self.get_msg_types, methods=["GET"], summary="获取消息类型")
		self.add_api_route("/contacts", self.get_contacts, methods=["GET"], summary="获取完整通讯录")
		self.add_api_route("/friends", self.get_friends, methods=["GET"], summary="获取好友列表")
		self.add_api_route("/dbs", self.get_dbs, methods=["GET"], summary="获取所有数据库")
		self.add_api_route("/{db}/tables", self.get_tables, methods=["GET"], summary="获取 db 中所有表")
		self.add_api_route("/pyq", self.refresh_pyq, methods=["GET"], summary="刷新朋友圈（数据从消息回调中查看）")
		self.add_api_route("/chatroom-member", self.get_chatroom_members, methods=["GET"], summary="获取群成员")
		self.add_api_route("/alias-in-chatroom", self.get_alias_in_chatroom, methods=["GET"], summary="获取群成员名片")
		self.add_api_route("/ocr-result", self.get_ocr_result, methods=["GET"], summary="获取 OCR 结果")

		# POST Routes
		self.add_api_route("/text", self.send_text, methods=["POST"], summary="发送文本消息")
		self.add_api_route("/image", self.send_image, methods=["POST"], summary="发送图片消息")
		self.add_api_route("/file", self.send_file, methods=["POST"], summary="发送文件消息")
		self.add_api_route("/rich-text", self.send_rich_text, methods=["POST"], summary="发送卡片消息")
		self.add_api_route("/pat", self.send_pat_msg, methods=["POST"], summary="发送拍一拍消息")
		# Deprecated or unimplemented APIs are commented out
		# self.add_api_route("/xml", self.send_xml, methods=["POST"], summary="发送 XML 消息")
		# self.add_api_route("/dec-image", self.decrypt_image, methods=["POST"], summary="（废弃）解密图片")
		# self.add_api_route("/attachment", self.download_attachment, methods=["POST"], summary="（废弃）下载图片、文件和视频")
		self.add_api_route("/save-image", self.download_image, methods=["POST"], summary="下载图片")
		self.add_api_route("/save-audio", self.get_audio_msg, methods=["POST"], summary="保存语音")

		# DELETE Routes
		self.add_api_route("/chatroom-member", self.del_chatroom_members, methods=["DELETE"], summary="删除群成员")

	def _forward_msg(self, msg: WxMsg, cb: str):
		data = {
			"id": msg.id,
			"ts": msg.ts,
			"sign": msg.sign,
			"type": msg.type,
			"xml": msg.xml,
			"sender": msg.sender,
			"roomid": msg.roomid,
			"content": msg.content,
			"thumb": msg.thumb,
			"extra": msg.extra,
			"is_at": msg.is_at(self.wcf.self_wxid),
			"is_self": msg.from_self(),
			"is_group": msg.from_group(),
		}

		try:
			rsp = requests.post(url=cb, json=data, timeout=30)
			if rsp.status_code != 200:
				self.LOG.error(f"消息转发失败，HTTP 状态码为: {rsp.status_code}")
		except Exception as e:
			self.LOG.error(f"消息转发异常: {e}")

	def _set_cb(self, cb: str):
		def callback(wcf: Wcf):
			while wcf.is_receiving_msg():
				try:
					msg = wcf.get_msg()
					if cb:
						self.LOG.info(f"收到消息，转发至回调：{msg}")
						self._forward_msg(msg, cb)
					else:
						print(f"收到消息：{msg}")
				except Empty:
					continue  # Empty message
				except Exception as e:
					self.LOG.error(f"Receiving message error: {e}")

		self.LOG.info(f"消息回调: {cb}" if cb else "没有设置回调，打印消息")
		self.wcf.enable_receiving_msg(pyq=True)  # 同时允许接收朋友圈消息
		Thread(target=callback, name="GetMessage", args=(self.wcf,), daemon=True).start()

	def is_login(self) -> dict:
		"""获取登录状态"""
		ret = self.wcf.is_login()
		return {"status": 0, "message": "成功", "data": {"login": ret}}

	def get_self_wxid(self) -> dict:
		"""获取登录账号 wxid"""
		ret = self.wcf.get_self_wxid()
		if ret:
			return {"status": 0, "message": "成功", "data": {"wxid": ret}}
		return {"status": -1, "message": "失败"}

	def get_msg_types(self) -> dict:
		"""获取消息类型"""
		ret = self.wcf.get_msg_types()
		if ret:
			return {"status": 0, "message": "成功", "data": {"types": ret}}
		return {"status": -1, "message": "失败"}

	def get_contacts(self) -> dict:
		"""获取完整通讯录"""
		ret = self.wcf.get_contacts()
		if ret:
			return {"status": 0, "message": "成功", "data": {"contacts": ret}}
		return {"status": -1, "message": "失败"}

	def get_friends(self) -> dict:
		"""获取好友列表"""
		ret = self.wcf.get_friends()
		if ret:
			return {"status": 0, "message": "成功", "data": {"friends": ret}}
		return {"status": -1, "message": "失败"}

	def get_dbs(self) -> dict:
		"""获取所有数据库"""
		ret = self.wcf.get_dbs()
		if ret:
			return {"status": 0, "message": "成功", "data": {"dbs": ret}}
		return {"status": -1, "message": "失败"}

	def get_tables(self, db: str) -> dict:
		"""获取 db 中所有表

		Args:
			db (str): 数据库名（可通过 `get_dbs` 查询）

		Returns:
			List[dict]: `db` 下的所有表名及对应建表语句
		"""
		ret = self.wcf.get_tables(db)
		if ret:
			return {"status": 0, "message": "成功", "data": {"tables": ret}}
		return {"status": -1, "message": "失败"}

	def get_user_info(self) -> dict:
		"""获取登录账号个人信息"""
		ret = self.wcf.get_user_info()
		if ret:
			return {"status": 0, "message": "成功", "data": {"ui": ret}}
		return {"status": -1, "message": "失败"}

	def get_ocr_result(self, extra: str = Body("C:/...", description="消息中的 extra"),
					   timeout: int = Body("30", description="超时时间（秒）")) -> dict:
		"""获取 OCR 结果

		Args:
			extra (str): 待识别的图片路径，消息里的 extra
			timeout (int): 超时时间（秒）

		Returns:
			str: OCR 结果
		"""
		ret = self.wcf.get_ocr_result(extra, timeout)
		if ret:
			return {"status": 0, "message": "成功", "data": {"ocr": ret}}
		return {"status": -1, "message": "可能失败，可以看看日志。这接口没啥用，别用了。"}

	def msg_cb(self, msg: Msg = Body(description="微信消息")):
		"""示例回调方法，简单打印消息"""
		print(f"收到消息：{msg}")
		return {"status": 0, "message": "成功"}

	def send_text(
			self, msg: str = Body(description="要发送的消息，换行用\\n表示"),
			receiver: str = Body("filehelper", description="消息接收者，roomid 或者 wxid"),
			aters: str = Body("", description="要 @ 的 wxid，多个用逗号分隔；@所有人 用 notify@all")) -> dict:
		"""发送文本消息

		Args:
			msg (str): 要发送的消息，换行使用 `\\n`；如果 @ 人的话，需要带上跟 `aters` 里数量相同的 @
			receiver (str): 消息接收人，wxid 或者 roomid
			aters (str): 要 @ 的 wxid，多个用逗号分隔；`@所有人` 只需要 `notify@all`

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_text(msg, receiver, aters)
		return {"status": ret, "message": "成功" if ret == 0 else "失败"}

	def send_image(self,
				   path: str = Body("C:\\Projs\\WeChatRobot\\TEQuant.jpeg", description="图片路径"),
				   receiver: str = Body("filehelper", description="消息接收者，roomid 或者 wxid")) -> dict:
		"""发送图片

		Args:
			path (str): 图片路径，如：`C:/Projs/WeChatRobot/TEQuant.jpeg` 或网络图片 URL（仅本地模式支持）
			receiver (str): 消息接收人，wxid 或者 roomid

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_image(path, receiver)
		return {"status": ret, "message": "成功" if ret == 0 else "失败"}

	def send_file(self,
				  path: str = Body("C:\\Projs\\WeChatRobot\\README.MD", description="本地文件路径"),
				  receiver: str = Body("filehelper", description="roomid 或者 wxid")) -> dict:
		"""发送文件

		Args:
			path (str): 本地文件路径，如：`C:/Projs/WeChatRobot/README.MD` 或网络文件 URL（仅本地模式支持）
			receiver (str): 消息接收人，wxid 或者 roomid

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_file(path, receiver)
		return {"status": ret, "message": "成功" if ret == 0 else "失败"}

	def send_rich_text(
			self, name: str = Body("碲矿", description="左下显示的名字"),
			account: str = Body("gh_75dea2d6c71f", description="填公众号 id 可以显示对应的头像"),
			title: str = Body("【FAQ】WeChatFerry 机器人常见问题 v39.0.10", description="标题，最多两行"),
			digest: str = Body("先看再问，少走弯路。", description="最多三行，会占位"),
			url: str = Body(
				"http://mp.weixin.qq.com/s?__biz=MzI0MjI1OTk0OQ==&mid=2247487601&idx=1&sn=1bf7a0d1c659f8bc78a00cba18d7b204",
				description="点击后跳转的链接"),
			thumburl: str = Body(
				"https://mmbiz.qpic.cn/mmbiz_jpg/XaSOeHibHicMGIiaZsBeYYjcuS2KfBGXfm8ibb9QrKJqk0H0W3JHia9icVica9nlWMiaD0xWmA0pKHpMOWbeBCJaAQc2IQ/0?wx_fmt=jpeg",
				description="缩略图的链接"),
			receiver: str = Body("filehelper", description="接收人, wxid 或者 roomid")) -> dict:
		"""发送卡片消息

		Args:
			name (str): 左下显示的名字
			account (str): 填公众号 id 可以显示对应的头像（gh_ 开头的）
			title (str): 标题，最多两行
			digest (str): 摘要，三行
			url (str): 点击后跳转的链接
			thumburl (str): 缩略图的链接
			receiver (str): 接收人, wxid 或者 roomid

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_rich_text(name, account, title, digest, url, thumburl, receiver)
		return {"status": ret, "message": "成功" if ret == 0 else "失败，原因见日志"}

	def send_pat_msg(
			self, roomid: str = Body(description="群聊 roomid"),
			wxid: str = Body("wxid_xxxxxxxxxxxxx", description="要拍的群友 wxid")) -> dict:
		"""拍一拍群友

		Args:
			roomid (str): 群聊的 roomid
			wxid (str): 要拍的群友的 wxid

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_pat_msg(roomid, wxid)
		return {"status": ret, "message": "成功" if ret == 1 else "失败，原因见日志"}

	def send_emotion(self,
					 path: str = Body("C:/Projs/WeChatRobot/emo.gif", description="本地表情路径"),
					 receiver: str = Body("filehelper", description="roomid 或者 wxid")) -> dict:
		"""发送表情

		Args:
			path (str): 本地表情路径，如：`C:/Projs/WeChatRobot/emo.gif`
			receiver (str): 消息接收人，wxid 或者 roomid

		Returns:
			dict: 包含发送结果的字典
		"""
		ret = self.wcf.send_emotion(path, receiver)
		return {"status": ret, "message": "成功" if ret == 0 else "失败"}

	def query_sql(self,
				  db: str = Body("MicroMsg.db", description="数据库"),
				  sql: str = Body("SELECT * FROM Contact LIMIT 1;", description="SQL 语句")) -> dict:
		"""执行 SQL，如果数据量大注意分页，以免 OOM

		Args:
			db (str): 要查询的数据库
			sql (str): 要执行的 SQL

		Returns:
			dict: 包含查询结果的字典
		"""
		ret = self.wcf.query_sql(db, sql)
		if ret:
			for row in ret:
				for k, v in row.items():
					if isinstance(v, bytes):
						row[k] = base64.b64encode(v).decode('utf-8')
			return {"status": 0, "message": "成功", "data": {"bs64": ret}}
		return {"status": -1, "message": "失败"}

	def accept_new_friend(self,
						  v3: str = Body("v3", description="加密用户名 (好友申请消息里 v3 开头的字符串)"),
						  v4: str = Body("v4", description="Ticket (好友申请消息里 v4 开头的字符串)"),
						  scene: int = Body(30, description="申请方式 (好友申请消息里的 scene)")) -> dict:
		"""通过好友申请

		Args:
			v3 (str): 加密用户名 (好友申请消息里 v3 开头的字符串)
			v4 (str): Ticket (好友申请消息里 v4 开头的字符串)
			scene (int): 申请方式 (好友申请消息里的 scene)

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.accept_new_friend(v3, v4, scene)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def add_chatroom_members(self,
							 roomid: str = Body("xxxxxxxx@chatroom", description="待加群的 id"),
							 wxids: str = Body("wxid_xxxxxxxxxxxxx", description="要加到群里的 wxid，多个用逗号分隔")) -> dict:
		"""添加群成员

		Args:
			roomid (str): 待加群的 id
			wxids (str): 要加到群里的 wxid，多个用逗号分隔

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.add_chatroom_members(roomid, wxids)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def invite_chatroom_members(self,
								roomid: str = Body("xxxxxxxx@chatroom", description="待邀请的群 id"),
								wxids: str = Body("wxid_xxxxxxxxxxxxx", description="要邀请到群里的 wxid，多个用逗号分隔")) -> dict:
		"""邀请群成员

		Args:
			roomid (str): 群的 id
			wxids (str): 要邀请成员的 wxid，多个用逗号分隔

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.invite_chatroom_members(roomid, wxids)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def del_chatroom_members(self,
							 roomid: str = Body("xxxxxxxx@chatroom", description="群的 id"),
							 wxids: str = Body("wxid_xxxxxxxxxxxxx", description="要删除的 wxid，多个用逗号分隔")) -> dict:
		"""删除群成员

		Args:
			roomid (str): 群的 id
			wxids (str): 要删除的 wxid，多个用逗号分隔

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.del_chatroom_members(roomid, wxids)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def receive_transfer(self,
						 wxid: str = Body("wxid_xxxxxxxxxxxxx", description="转账消息里的发送人 wxid"),
						 transferid: str = Body("transferid", description="转账消息里的 transferid"),
						 transactionid: str = Body("transactionid", description="转账消息里的 transactionid")) -> dict:
		"""接收转账

		Args:
			wxid (str): 转账消息里的发送人 wxid
			transferid (str): 转账消息里的 transferid
			transactionid (str): 转账消息里的 transactionid

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.receive_transfer(wxid, transferid, transactionid)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def refresh_pyq(self, id: int = Query(0, description="开始 id，0 为最新页")) -> dict:
		"""刷新朋友圈

		Args:
			id (int): 开始 id，0 为最新页

		Returns:
			dict: 包含操作结果的字典
		"""
		ret = self.wcf.refresh_pyq(id)
		return {"status": ret, "message": "成功" if ret == 1 else "失败"}

	def download_image(self,
					   id: int = Body("0", description="消息中的 id"),
					   extra: str = Body("C:/...", description="消息中的 extra"),
					   dir: str = Body("C:/...", description="保存图片的目录"),
					   timeout: int = Body("30", description="超时时间（秒）")) -> dict:
		"""下载图片

		Args:
			id (int): 消息中 id
			extra (str): 消息中的 extra
			dir (str): 存放图片的目录（目录不存在会出错）
			timeout (int): 超时时间（秒）

		Returns:
			dict: 包含下载结果的字典
		"""
		ret = self.wcf.download_image(id, extra, dir, timeout)
		if ret:
			return {"status": 0, "message": "成功", "data": {"path": ret}}

		return {"status": -1, "message": "失败，原因见日志"}

	def get_audio_msg(self,
					  id: int = Body("0", description="消息中的 id"),
					  dir: str = Body("C:/...", description="保存语音的目录"),
					  timeout: int = Body("30", description="超时时间（秒）")) -> dict:
		"""保存语音

		Args:
			id (int): 消息中 id
			dir (str): 存放语音的目录
			timeout (int): 超时时间（秒）

		Returns:
			dict: 包含保存结果的字典
		"""
		ret = self.wcf.get_audio_msg(id, dir, timeout)
		if ret:
			return {"status": 0, "message": "成功", "data": {"path": ret}}

		return {"status": -1, "message": "失败，原因见日志"}

	def get_chatroom_members(self, roomid: str = Query("xxxxxxxx@chatroom", description="群的 id")) -> dict:
		"""获取群成员

		Args:
			roomid (str): 群的 id

		Returns:
			dict: 包含群成员列表的字典
		"""
		ret = self.wcf.get_chatroom_members(roomid)
		return {"status": 0, "message": "成功", "data": {"members": ret}}

	def get_alias_in_chatroom(self, wxid: str = Query("wxid_xxxxxxxxxxxxx", description="wxid"),
							  roomid: str = Query("xxxxxxxx@chatroom", description="群的 id")) -> dict:
		"""获取群成员名片

		Args:
			wxid (str): wxid
			roomid (str): 群的 id

		Returns:
			dict: 包含名片信息的字典
		"""
		ret = self.wcf.get_alias_in_chatroom(wxid, roomid)
		return {"status": 0, "message": "成功", "data": {"alias": ret}}
