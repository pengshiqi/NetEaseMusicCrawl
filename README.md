### 网易云音乐新版API爬虫

在网易云音乐更新了API之后，现在的API都是经过AES和RSA算法加密过了，需要携带加密的信息通过POST方式请求。

`NetEaseMusicCrawl.py` 中实现了3个小爬虫，分别是：

× `get_artist_list`: 爬取热门歌手列表

× `get_song_list`: 爬取某个歌手的热门歌曲列表

× `get_hot_comments`: 爬取某个歌曲的热门评论

各个函数传入的参数可以看函数说明，网易云音乐其他API的爬取方式也都和这三个大同小异，可以通过类似的方式得到。
