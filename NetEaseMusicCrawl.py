# -*- coding: utf-8 -*-

import os
import json
import base64

import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from prettytable import PrettyTable


BASE_URL = 'http://music.163.com/'
_session = requests.Session()

TEXT = {'username': '', 'password': '', 'rememberLogin': 'true'}
MODULUS = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
NONCE = '0CoJUm6Qyw8W8jud'
PUBKEY = '010001'

COMMENT_THRESHOLD = 10000


def create_secret_key(size):
    """
    Create a secret key whose length is 16.

    :param size:
    :return:
    """
    return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]


def aes_encrypt(text, sec_key):
    """
    AES encrypt method.

    :param text:
    :param sec_key:
    :return:
    """
    pad = 16 - len(text) % 16
    text += pad * chr(pad)
    encryptor = AES.new(sec_key, 2, '0102030405060708')
    cipher_text = encryptor.encrypt(text)
    cipher_text = base64.b64encode(cipher_text)
    return cipher_text


def rsa_encrypt(text, pub_key, modulus):
    """
    RSA encrypt method.

    :param text:
    :param pub_key:
    :param modulus:
    :return:
    """
    text = text[::-1]
    rs = int(text.encode('hex'), 16) ** int(pub_key, 16) % int(modulus, 16)
    return format(rs, 'x').zfill(256)


def get_artist_list(limit=60, offset=0):
    """
    返回前limit个热门歌手的所有信息，名字在name字段，id在id字段。

    :param limit: 前limit个热门歌手
    :param offset: 从第offset个歌手开始
    :return: 一个list，每个元素是一个字典，包含一位歌手的所有信息，其中名字在name字段，id在id字段
    """
    url = BASE_URL + 'weapi/artist/top?csrf_token='
    headers = {'Cookie': 'appver=1.5.0.75771;', 'Referer': 'http://music.163.com/discover/artist'}

    text = json.dumps(TEXT)
    sec_key = create_secret_key(16)
    enc_text = aes_encrypt(aes_encrypt(text, NONCE), sec_key)
    enc_sec_key = rsa_encrypt(sec_key, PUBKEY, MODULUS)
    data = {'params': enc_text, 'encSecKey': enc_sec_key, 'limit': limit, 'offset': offset}
    req = requests.post(url, headers=headers, data=data)
    data = json.loads(req.content)
    return data['artists']


def get_song_list(artist_id, limit=50):
    """
    输入歌手id，返回该歌手的前50首热门歌曲。

    :param artist_id:
    :param limit:
    :return: 返回一个list，每个元素的第一项是歌曲名，第二项是歌曲id
    例如： [(u'\u544a\u767d\u6c14\u7403', u'/song?id=418603077'), ...]
    """
    url = 'http://music.163.com/artist?id={}'.format(artist_id)

    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')

    ul = soup.select('ul.f-hide')[0]
    li = ul.select('li')
    # song_list 是一个列表，每个元素的第一项是歌曲名，第二项是歌曲id
    song_list = [(song.get_text(), song.select('a')[0]['href']) for song in li]

    return song_list[:limit]


def get_hot_comments(song_id, threshold=COMMENT_THRESHOLD):
    """
    输入歌曲id，返回该歌曲的前threshold个热门评论。

    :param song_id: 歌曲id，string类型和int类型均可，例如35403523
    :param threshold: 前threshold个热门评论
    :return: 返回一个list，每个子元素也是list，其中第一项为评论内容，第二项为点赞数。
    例如： [[u'\u4e24\u5929\u524d \u9648\u5955\u8fc5\u5728\u58a8\u5c14\u672c\u5f00\u6f14\u5531\u4f1a \u5b89\u4e1c\u5c3c\u53d1\u5fae\u535a\u8bf4\u4ed6\u5728\u53f0\u4e0b\u542c\u7684\u611f\u6168\u4e07\u5206 \u5c31\u50cf\u505a\u4e86\u4e00\u573a\u68a6 \u4ed6\u7ec8\u4e8e\u5b8c\u6210\u4e86\u81ea\u5df1\u7684\u68a6 \u81ea\u5df1\u559c\u6b22\u7684\u6b4c\u624b\u4e3a\u4ed6\u7684\u4e66\u5531\u7684\u4e3b\u9898\u66f2 \u4f60\u6709\u68a6\u60f3\u4f60\u5c31\u8981\u634d\u536b\u5b83~', 64520],...]
    """
    url = BASE_URL + 'weapi/v1/resource/comments/R_SO_4_{}?csrf_token='.format(song_id)
    headers = {'Cookie': 'appver=1.5.0.75771;', 'Referer': 'http://music.163.com/song?id={}'.format(song_id)}

    text = json.dumps(TEXT)
    sec_key = create_secret_key(16)
    enc_text = aes_encrypt(aes_encrypt(text, NONCE), sec_key)
    enc_sec_key = rsa_encrypt(sec_key, PUBKEY, MODULUS)
    data = {'params': enc_text, 'encSecKey': enc_sec_key}
    req = requests.post(url, headers=headers, data=data)

    data = json.loads(req.content)['hotComments']

    res = []
    for item in data:
        res.append([item['content'], item['likedCount']])

    return res[:threshold]


def get_latest_comments(song_id, threshold=COMMENT_THRESHOLD):
    """
    输入歌曲id，返回该歌曲的前threshold个最新评论。

    :param song_id: 歌曲id，string类型和int类型均可，例如35403523
    :param threshold: 前threshold个最新评论
    :return: 返回一个list，每个子元素也是list，其中第一项为评论内容，第二项为点赞数。
    例如： [[u'\u4e5f\u8bb8\u4f1a\u53d8\u6210\u611f\u52a8', 1], [u'\u53d8\u6210\u52c7\u6562', 0]]
    """
    url = BASE_URL + 'weapi/v1/resource/comments/R_SO_4_{}?csrf_token='.format(song_id)
    headers = {'Cookie': 'appver=1.5.0.75771;', 'Referer': 'http://music.163.com/song?id={}'.format(song_id)}

    text = json.dumps(TEXT)
    sec_key = create_secret_key(16)
    enc_text = aes_encrypt(aes_encrypt(text, NONCE), sec_key)
    enc_sec_key = rsa_encrypt(sec_key, PUBKEY, MODULUS)
    data = {'params': enc_text, 'encSecKey': enc_sec_key}
    req = requests.post(url, headers=headers, data=data)

    data = json.loads(req.content)['comments']

    res = []
    for item in data:
        res.append([item['content'], item['likedCount']])

    return res[:threshold]


if __name__ == "__main__":
    artist_list = get_artist_list(3)
    for artist in artist_list:
        print u'### 歌手： {} 的热门歌曲的热门评论如下： ###'.format(artist['name'])
        song_list = get_song_list(artist['id'])

        for song in song_list:
            print u'歌曲： {} 的热门评论有： '.format(song[0])
            hot_comments = get_latest_comments(song[1][9:])

            x = PrettyTable([u'评论', u'点赞数'])
            x.padding_width = 1
            for item in hot_comments:
                x.add_row(item)
            print x
