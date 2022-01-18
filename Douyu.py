'''
-*- coding: utf-8 -*-
@Time : 2021/12/20 14:56
@Author : yzw
@Software: PyCharm
'''
import aiohttp
import asyncio
from struct import pack
import re
import json
import requests
import time

class DouyuClient:
    def __init__(self,room_id):
        self.room_id = room_id  # 房间号
        self.wss_url = 'wss://danmuproxy.douyu.com:8503/'   # 弹幕服务器地址
        self.heartbeat = b'\x14\x00\x00\x00\x14\x00\x00\x00\xb1\x02\x00\x00\x74\x79\x70\x65\x40\x3d\x6d\x72\x6b\x6c' \
                         b'\x2f\x00 '
        self.isstop = None
        self.hs = None
        self.ws = None

        # 检查房间 是否存在/是否开播
        re = requests.request("get","https://open.douyucdn.cn/api/RoomApi/room/"+room_id)
        if re.text == '"Not Found"\n':
            print("房间不存在")
            exit(0)
        info = json.loads(re.text)
        if info['data']['room_status'] != '1':
            print("房间未开播")
            exit(0)

    async def login(self):
        '''登录'''

        self.hs = aiohttp.ClientSession()
        self.ws = await self.hs.ws_connect('wss://danmuproxy.douyu.com:8503/')
        self.isstop = False

        login_data = []
        # 登录房间
        data = f'type@=loginreq/roomid@={self.room_id}/'
        s = pack('i', 9 + len(data)) * 2
        s += b'\xb1\x02\x00\x00'  # 689
        s += data.encode('ascii') + b'\x00'
        login_data.append(s)

        # 登录弹幕分组
        data = f'type@=joingroup/rid@={self.room_id}/gid@=-9999/'
        s = pack('i', 9 + len(data)) * 2
        s += b'\xb1\x02\x00\x00'  # 689
        s += data.encode('ascii') + b'\x00'
        login_data.append(s)

        for log_data in login_data:
            await self.ws.send_bytes(log_data)

        print('login')

    async def heartbeats(self,interval=10):
        '''向服务器发送心跳讯息，保持登陆状态'''
        while not self.isstop and self.heartbeat:
            await asyncio.sleep(interval)
            try:
                await self.ws.send_bytes(self.heartbeat)
            except:
                pass

    def decode_data(self,res_data):
        '''对传回来的字节数据进行解码'''
        msgs = []
        for msg in re.findall(b'(type@=.*?)\x00', res_data):
            try:
                if b"gbroadcast" in msg:
                    continue
                msg = msg.replace(b'@=', b'":"').replace(b'/', b'","')
                msg = msg.replace(b'@A', b'@').replace(b'@S', b'/')
                msg = json.loads((b'{"' + msg[:-2] + b'}').decode('utf8', 'ignore'))
                msg['time'] = time.time()
                msgs.append(msg)
            except Exception as e:
                print(f"Wrong! {msg}")
                continue
        return msgs

    async def get_data(self):
        '''获取数据并进行相应的处理'''
        while not self.isstop:
            async for msg in self.ws:
                ms = self.decode_data(msg.data)
                for m in ms:
                    if m['type'] == 'chatmsg':
                        print(f"{m['nn']}:{m['txt']}")
            await asyncio.sleep(1)
            await self.stop()
            await self.login()
            await asyncio.sleep(1)

    async def stop(self):
        '''停止连接'''
        self.isstop = True
        print("stop")
        await self.hs.close()

    async def main(self):
        await self.login()
        await asyncio.gather(
            self.heartbeats(),
            self.get_data(),
        )


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    room_id = input("请输入房间号:")
    dy = DouyuClient(room_id)
    loop.run_until_complete(dy.main())
