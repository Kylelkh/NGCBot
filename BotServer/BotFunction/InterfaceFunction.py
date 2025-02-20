import FileCache.FileCacheServer as Fcs
import xml.etree.ElementTree as ET
from OutPut.outPut import op
import requests
import time
import os


def getWithdrawMsgData(content):
    """
    提取撤回消息的 ID
    :param content:
    :return:
    """
    root = ET.fromstring(content)
    try:
        newMsgId = root.find(".//newmsgid").text
        replaceMsg = root.find(".//replacemsg").text
        if newMsgId and replaceMsg:
            if '撤回了一条消息' in replaceMsg:
                return newMsgId
    except Exception:
        return None

def getWechatVideoData(content):
    """
    处理微信视频号 提取objectId objectNonceId
    :param content:
    :return: objectId objectNonceId
    """
    try:
        root = ET.fromstring(content)
        finderFeed = root.find('.//finderFeed')
        objectId = finderFeed.find('./objectId').text
        objectNonceId = finderFeed.find('./objectNonceId').text
        return objectId, objectNonceId
    except Exception as e:
        op(f'[~]: 提取微信视频号ID出现错误, 错误信息: {e}, 不用管此报错 ~~~')
        return '', ''


def getAtData(wcf, msg):
    """
    处理@信息
    :param msg:
    :param wcf:
    :return:
    """
    noAtMsg = msg.content
    try:
        root_xml = ET.fromstring(msg.xml)
        atUserListsElement = root_xml.find('.//atuserlist')
        atUserLists = atUserListsElement.text.replace(' ', '').strip().strip(',').split(
            ',') if atUserListsElement is not None else None
        if not atUserLists:
            return '', ''
        atNames = []
        for atUser in atUserLists:
            atUserName = wcf.get_alias_in_chatroom(atUser, msg.roomid)
            atNames.append(atUserName)
        for atName in atNames:
            noAtMsg = noAtMsg.replace('@' + atName, '')
    except Exception as e:
        op(f'[~]: 处理@消息出现小问题, 仅方便开发调试, 不用管此报错: {e}')
        return '', ''
    return atUserLists, noAtMsg.strip()


def getIdName(wcf, Id=None, roomId=None, retry=0, max_retries=3):
    """
    获取好友或者群聊昵称
    :param wcf: 微信框架对象
    :param Id: 用户ID
    :param roomId: 群聊ID
    :param retry: 当前重试次数
    :param max_retries: 最大重试次数
    :return:
    """
    try:
        name_list = wcf.query_sql("MicroMsg.db", f"SELECT UserName, NickName FROM Contact WHERE UserName = '{Id}';")

        if not name_list and retry < max_retries:
            # 如果查询结果为空且未达到最大重试次数，则等待一秒后重试
            time.sleep(1)
            return getIdName(wcf, Id, roomId, retry + 1, max_retries)
        elif not name_list:
            # 达到最大重试次数但仍无法获取数据，返回原始ID
            op(f'[~]: 获取好友或者群聊昵称出现错误, 错误信息: 查询结果为空')
            return Id

        name = name_list[0]['NickName']

        if '@chatroom' not in Id:
            if name:
                return name
            nickName = wcf.get_alias_in_chatroom(Id, roomId)
            if not nickName:
                return Id
            return nickName
        else:
            return name

    except Exception as e:
        op(f'[~]: 获取好友或者群聊昵称出现错误, 错误信息: {e}')
        if retry < max_retries:
            # 如果发生异常且未达到最大重试次数，则等待一秒后重试
            time.sleep(1)
            return getIdName(wcf, Id, roomId, retry + 1, max_retries)
        else:
            # 达到最大重试次数但仍无法获取数据，返回原始ID
            return Id




def getUserPicUrl(wcf, sender):
    """
    获取好友头像下载地址
    :param sender:
    :param wcf:
    :return:
    """
    imgName = str(sender) + '.jpg'
    save_path = Fcs.returnAvatarFolder() + '/' + imgName

    if imgName in os.listdir(Fcs.returnAvatarFolder()):
        return save_path

    headImgData = wcf.query_sql("MicroMsg.db", f"SELECT * FROM ContactHeadImgUrl WHERE usrName = '{sender}';")
    try:
        if headImgData:
            if headImgData[0]:
                bigHeadImgUrl = headImgData[0]['bigHeadImgUrl']
                content = requests.get(url=bigHeadImgUrl, timeout=30).content
                with open(save_path, mode='wb') as f:
                    f.write(content)
                return save_path
    except Exception as e:
        op(f'[-]: 获取好友头像下载地址出现错误, 错误信息: {e}')
        return None


if __name__ == '__main__':
    getWithdrawMsgData('<sysmsg type="revokemsg"><revokemsg><session>47555703573@chatroom</session><msgid>1387587956</msgid><newmsgid>6452489353190914412</newmsgid><replacemsg><![CDATA["Vcnnn8h" 撤回了一条消息]]></replacemsg><announcement_id><![CDATA[]]></announcement_id></revokemsg></sysmsg>')
