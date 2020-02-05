# -*- coding: utf-8 -*-
# @Time    : 2019/11/27 23:00
# @Author  : Leon
# @Email   : 1446684220@qq.com
# @File    : test.py
# @Desc    :
# @Software: PyCharm

from WechatPCAPI import WechatPCAPI
import time
import logging
from queue import Queue
import threading
import re
import requests

# 两个api接口，virus不稳定，故默认使用virus2接口，如果要改用virus接口的话需要对test.py做部分改动
import virus2 as virus
# import virus as virus


url = "https://service-f9fjwngp-1252021671.bj.apigw.tencentcs.com/release/pneumonia"

logging.basicConfig(level=logging.INFO)
queue_recved_message = Queue()
queue_recved_message_friendlist = Queue()


def on_message(message):
    queue_recved_message.put(message)
    queue_recved_message_friendlist.put(message)


def friendsList():
    idList = {}
    while not queue_recved_message_friendlist.empty():
        message = queue_recved_message_friendlist.get()
        # 遍历好友和群，用来推送新闻
        if 'friend::person' in message.get('type'):
            personId = message.get('data', {}).get('wx_id', '')
            if personId != 'fmessage' and personId != 'floatbottle' and personId != 'newsapp' and personId != 'weixin' and personId != 'medianote':
                idList[personId] = 1
                print("检测到用户！：" + personId)

        if 'friend::chatroom' in message.get('type'):
            chatroomId = message.get('data', {}).get('chatroom_id', '')
            idList[chatroomId] = 0
            print("检测到群聊！：" + chatroomId)


    return idList



# 消息处理示例 仅供参考

def thread_handle_message(wx_inst):


    while True:
        # schedule.run_pending()  # 运行所有可运行的任务
        # wx_inst.update_frinds()
        time.sleep(0.1)
        message = queue_recved_message.get()
        msgflag = 0
        if 'msg' in message.get('type'):
            print(message)
            time.sleep(1)

            # 这里是判断收到的是消息 不是别的响应
            msg_content = message.get('data', {}).get('msg', '')    # 收到的消息
            if message.get('data', {}).get('from_chatroom_wxid', ''):
                chatroom_wxid = message.get('data', {}).get('from_chatroom_wxid', '')
            elif message.get('data', {}).get('from_wxid', ''):
                wx_id = message.get('data', {}).get('from_wxid', '')
                msgflag = 1

            send_or_recv = message.get('data', {}).get('send_or_recv', '')
            try:
                # 读取api数据
                f = open('APIDATA.txt', 'r')
                r_read = f.read()
                r = eval(r_read)
                f.close()

                if send_or_recv[0] == '0':
                    # 0是收到的消息 1是发出的 对于1不要再回复了 不然会无限循环回复
                    if "/virusall" in msg_content :
                        msglist = re.compile(r'(?<=/virusall ).*').findall(msg_content)
                        if msglist != []:
                            msg = ''.join(msglist)
                            returnmsg = virus.provinceall(r, msg)

                            if msgflag == 0:
                                wx_inst.send_text(chatroom_wxid, returnmsg)
                            else:
                                wx_inst.send_text(to_user=wx_id, msg=returnmsg)
                            time.sleep(1)


                    elif "/virus" in msg_content :
                        msglist = re.compile(r'(?<=/virus ).*').findall(msg_content)
                        if msglist != []:
                            msg = ''.join(msglist)
                            area, confirmedCount, suspectedCount, curedCount, deadCount, updateTime = virus.area(r, msg)
                            if (area == "未查询到数据"):
                                returnmsg = area
                            else:
                                returnmsg = str(area) + ":\n" + "确诊人数：" + str(confirmedCount) + "\n" +\
                                            "治愈人数：" + str(curedCount) + "\n" + "死亡人数：" +\
                                            str(deadCount) + "\n" + "数据最后更新时间：" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updateTime)))
                                # wx_inst.send_text(chatroom_wxid, returnmsg)
                        else:
                            confirmedCount, suspectedCount, curedCount, deadCount, updateTime = virus.overall(r)
                            returnmsg = "截至" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updateTime))) + \
                                        ":\n" + "确诊人数：" + str(confirmedCount) + "\n" + "疑似感染人数：" +\
                                        str(suspectedCount) + "\n" + "治愈人数：" + str(curedCount) + "\n" + "死亡人数：" + \
                                        str(deadCount)

                        # 在这里设置回复内容
                        if msgflag == 0:
                            wx_inst.send_text(chatroom_wxid, returnmsg)
                        else:
                            wx_inst.send_text(to_user=wx_id, msg=returnmsg)
                        time.sleep(1)


            except:
                if msgflag == 0:
                    wx_inst.send_text(chatroom_wxid, "数据更新中，稍后再试")
                else:
                    wx_inst.send_text(to_user=wx_id, msg="数据库更新中，稍后再试")
                time.sleep(1)


def apidata(wx_inst):
    # global timer1
    try:
        r = requests.get(url).json()
        f = open('APIDATA.txt', 'w')
        f.write(str(r))
        f.close()
        print("API数据刷新成功")
    except:
        print("API异常")


def virusnews(wx_inst):
    # global timer2
    try:
        # 读取API数据
        f = open('APIDATA.txt', 'r')
        r_read = f.read()
        r = eval(r_read)
        f.close()

        idList = friendsList()
        time.sleep(5)

        newslist = virus.news(r)
        if(newslist!=[]):
            print("检测到新新闻\n--------------------")
            returnmsg = ""
            for x in newslist:
                returnmsg = returnmsg + x['title'] + '\n' + x['sourceUrl'] + '\n\n'

            print(returnmsg)

            # 读取群和好友列表


            for x in idList:
                time.sleep(3)
                if idList[x] == 0:
                    wx_inst.send_text(x, returnmsg)
                if idList[x] == 1:
                    wx_inst.send_text(to_user=x, msg=returnmsg)

            # wx_inst.send_text('31848182176@chatroom', returnmsg)
            # wx_inst.send_text('1030099185@chatroom', returnmsg)
    except:
        print("API异常")




def main():
    wx_inst = WechatPCAPI(on_message=on_message, log=logging)
    wx_inst.start_wechat(block=True)

    while not wx_inst.get_myself():
        time.sleep(5)

    print('登陆成功')
    print(wx_inst.get_myself())

    # 获取id
    # wx_inst.update_frinds()
    apidata(wx_inst)

    threading.Thread(target=thread_handle_message, args=(wx_inst,)).start()

    wx_inst.send_text(to_user='filehelper', msg='777888999')

    while True:
        apidata(wx_inst)
        # 开启自动新闻播报可能会导致帐号被封，谨慎开启
        # wx_inst.update_frinds()
        # virusnews(wx_inst)
        time.sleep(120)



    # wx_inst.send_link_card(
    #     to_user='filehelper',
    #     title='博客',
    #     desc='我的博客，红领巾技术分享网站',
    #     target_url='http://www.honglingjin.online/',
    #     img_url='http://honglingjin.online/wp-content/uploads/2019/07/0-1562117907.jpeg'
    # )
    # time.sleep(1)
    #
    # wx_inst.send_img(to_user='filehelper', img_abspath=r'C:\Users\Leon\Pictures\1.jpg')
    # time.sleep(1)
    #
    # wx_inst.send_file(to_user='filehelper', file_abspath=r'C:\Users\Leon\Desktop\1.txt')
    # time.sleep(1)
    #
    # wx_inst.send_gif(to_user='filehelper', gif_abspath=r'C:\Users\Leon\Desktop\08.gif')
    # time.sleep(1)
    #
    # wx_inst.send_card(to_user='filehelper', wx_id='gh_6ced1cafca19')

    # 这个是获取群具体成员信息的，成员结果信息也从上面的回调返回
    # wx_inst.get_member_of_chatroom('22941059407@chatroom')

    # 新增@群里的某人的功能
    # wx_inst.send_text(to_user='22941059407@chatroom', msg='test for at someone', at_someone='wxid_6ij99jtd6s4722')

    # 这个是更新所有好友、群、公众号信息的，结果信息也从上面的回调返回
    # wx_inst.update_frinds()


if __name__ == '__main__':
    main()
