'''
-*- coding: utf-8 -*-
@Time : 2021/12/27 16:22
@Author : yzw
@Software: PyCharm
'''
import requests
import json
import pymongo

def get_gift_info(room_id=None):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["zhibo"]
    gift_col = mydb["gift_values"]

    if room_id:
        url = "http://open.douyucdn.cn/api/RoomApi/room/" + room_id
        re = requests.request('get', url)
        gift_info = re.json()['data']['gift']
        for gift in gift_info:
            gift_values = {'id':int(gift['id']),'name':gift['name'],'value':gift['pc']}
            x = gift_col.insert_one(gift_values)
    else:
        url = "http://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json"
        re = requests.request('get',url)
        info = re.text[17:-2]
        info = json.loads(info)

        gifts_info = info['data']

        for g_id in gifts_info:
            gift_values = {'id':int(g_id),'name':gifts_info[g_id]['name'],'value':gifts_info[g_id]['pc']/100}
            x = gift_col.insert_one(gift_values)
            print(x)
    print("礼物信息收集成功！")


if __name__ == '__main__':
    get_gift_info()




