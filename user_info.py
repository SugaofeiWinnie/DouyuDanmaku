'''
-*- coding: utf-8 -*-
@Time : 2022/1/4 15:53
@Author : yzw
@Software: PyCharm
'''
import aiohttp
import asyncio
from lxml import etree

# log_url = 'https://www.doseeing.com/login?'
user_info_url = 'https://www.doseeing.com/data/fan/'
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}
login_data = {
    'username':'15222795271',
    'password':'yzw971128'
}
async def login(headers=headers,login_data=login_data,user_id='19656651'):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'https://www.doseeing.com/login?redirect=/data/fan/{user_id}',headers=headers,data=login_data) as re:
            text = await re.text()
            selector = etree.HTML(text)
            divs = selector.xpath("//div[@class='info']/child::*")
            if len(divs) > 3:
                badges_info = divs[2]
            else:
                badges_info = divs[1]

            for b in badges_info:
                if b.xpath("./text()"): continue
                else:
                    if b.xpath("./span/text()"):
                        print(b.xpath("./span/text()"))
                    print(b.xpath("./a/text()"))



async def main():
    await login()



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
