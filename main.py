import asyncio
import time
from lxml import etree
import aiohttp
import pymongo
from Douyu import DouyuClient
import gift_info

class myClient(DouyuClient):
    def __init__(self,room_id):
        '''初始化'''
        super(myClient, self).__init__(room_id)
        # 连接MongoDB数据库
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = self.myclient["zhibo"]
        self.col = self.mydb['send_gift']
        # 获取礼物价值
        self.gift_values = self.mydb['gift_values']
        self.login_data = {
            'username': '15222795271',
            'password': 'yzw971128'
        }
        # 弹幕列表及时间索引
        self.timer_idx = []
        self.danmaku_txt = []

        gift_info.get_gift_info(room_id)

    async def get_badges_info(self,user_id,receive_nn):
        '''获取用户虚拟徽章信息'''
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://www.doseeing.com/login?redirect=/data/fan/{user_id}',
                                    data=self.login_data) as re:
                text = await re.text()
                selector = etree.HTML(text)
                divs = selector.xpath("//div[@class='info']/child::*")
                if len(divs) > 3:
                    badges_info = divs[2]
                elif len(divs) == 3:
                    badges_info = divs[1]
                elif len(divs) == 2:
                    return 0,0,0
                badges = {}
                for b in badges_info:
                    if b.xpath("./text()"):continue
                    else:
                        try:
                            if b.xpath("./span/text()")[0] != '0':
                                badges[b.xpath("./a/text()")[0]] = int(b.xpath("./span/text()")[0])
                        except Exception as e:
                            print(user_id)
                            exit(e)
                print(badges)

                badge_num = 0 # 粉丝徽章数量
                max_level = 0 # 粉丝徽章最高等级
                cur_level = 0 # 当前直播间粉丝徽章等级
                for k,v in badges.items():
                    badge_num += 1
                    max_level = max(v,max_level)
                    if k == receive_nn:
                        cur_level = v
                print(badge_num,max_level,cur_level)
                await session.close()
                return badge_num,max_level,cur_level

    async def save_data(self,data):
        '''调整数据格式并存储到MongoDB数据库'''
        # 从数据库中查询对应id的礼物价值，返回的是mongogb指针对象
        value = list(self.gift_values.find({'id':int(data['gfid'])}))
        badge_num,max_level,cur_level = await self.get_badges_info(data['uid'],data['receive_nn'])
        # 存储数据格式
        send_gift = {'user_id':data['uid'],'user_name':data['nn'],'gift_id':data['gfid'],'gift_nums':data['gfcnt'],\
                     'gift_values':int(data['gfcnt'])*value[0]['value'],'badge_num':badge_num,'max_lvl':max_level,\
                     'cur_lvl':cur_level,'danmaku':data['danmaku_list']}
        x = self.col.insert_one(send_gift)
        print(x)

    def drop_danmaku(self,interval=15):
        '''维护弹幕列表，保留时间范围为interval（seconds）以内的弹幕'''
        now = time.time()
        for i in range(len(self.time_idx)):
            if now - self.time_idx[i] <= interval:
                break
        self.time_idx = self.time_idx[i:]
        self.danmaku_txt = self.danmaku_txt[i:]


    async def get_data(self):
        '''获取数据并进行相应的处理'''
        while not self.isstop:
            async for msg in self.ws:
                ms = self.decode_data(msg.data)
                for m in ms:
                    if m['type'] == 'chatmsg':
                        # 记录弹幕及发送时间
                        self.timer_idx.append(m['time'])
                        self.danmaku_txt.append(m['txt'])
                        print(f"{time.asctime(time.localtime(m['time']))} {m['nn']}:{m['txt']}")
                        now_time = time.time()
                        if now_time - self.timer_idx[0] > 60:
                            self.drop_danmaku()

                    if m['type'] == 'dgb':
                        m['danmaku_list'] = self.danmaku_txt
                        await self.save_data(m)
            await asyncio.sleep(1)
            await self.stop()
            await self.login()
            await asyncio.sleep(1)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    room_id = input("请输入房间号：")
    dy = myClient(room_id)
    loop.run_until_complete(dy.main())