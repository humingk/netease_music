# !/usr/bin/env python
# -*- coding: utf-8 -*-

# author: humingk
# ----------------------
import config
import json
from netease.first_param import first_param
from netease.request_data import request_data
from netease.database_pool import database_pool
import logger

log = logger.loggler()


class user_ranklist_songs:
    """
    排行榜歌曲获取类

    """

    def __init__(self):
        # 排行榜歌曲列表
        self.user_ranklist_songs_list = []

    def get_ranklist_songs(self, user_id=config.user_id, rank_type=config.rank_type, rank_max=config.rank_max):
        """
         获取排行榜歌曲列表

        :param user_id: 用户id
        :param rank_max: 排行榜歌曲获取最大数
        :return: status: 是否获取到歌曲
        :return: 排行榜歌曲列表
        """
        # 请求参数
        _first_param = first_param().get_first_param_ranklist(user_id=user_id, rank_type=rank_type)
        # 请求数据
        content = request_data().get_request_data(first_param=_first_param[1], url=config.url_user_rank)
        print(json.loads(content[1]))
        # print(json.loads(content[1])["weekData"])
        try:
            if content[0]:
                if rank_type == config.rank_type_all:
                    json_data = json.loads(content[1])["allData"]
                elif rank_type == config.rank_type_week:
                    json_data = json.loads(content[1])["weekData"]
            else:
                return False, []
        except KeyError as e:
            log.error("get_ranklist_songs failed, Maybe the guy's ranklist is hidden,can you see it in the webpage ?",
                      "user_id:{},rank_type:{},error:{}".format(user_id, rank_type, e))
            return False, []
        except Exception as e:
            log.error("get_ranklist_songs failed", "user_id:{},rank_type:{},error:{}"
                      .format(user_id, rank_type, e))
            return False, []
        song_count = 0
        pool = database_pool()
        while song_count < rank_max and song_count < len(json_data):
            self.__add(song_count, rank_type, json_data, pool)
            song_count += 1
        log.debug("get_ranklist_songs success", "user_id:{},rank_type:{},rank_count:{}"
                  .format(user_id, rank_type, song_count))
        pool.commit()
        return True, self.user_ranklist_songs_list

    def __add(self, song_count, rank_type, json_data, pool):
        """
        添加到排行榜歌曲列表

        :param song_count: 排行榜歌曲位移
        :param rank_type: 排行榜种类
        :param json_data: 待添加的数据
        :param pool: 数据库连接池
        """
        song = {
            "song_id": json_data[song_count]["song"]["id"],
            "song_name": json_data[song_count]["song"]["name"],
            "song_source": config.song_source_rank,
            "song_source_type": rank_type,
            "rank_score": json_data[song_count]["score"]
        }
        self.user_ranklist_songs_list.append(song)
        pool.execute(
            "insert into song(song_id,song_name,song_source,song_source_type,rank_score) values({},{},{},{},{})"
                .format(song["song_id"], song["song_name"], song["song_source"], song["song_source_type"],
                        song["rank_score"]))


if __name__ == "__main__":
    print(user_ranklist_songs().get_ranklist_songs(user_id=config.user_id, rank_type=config.rank_type_week))
    print(user_ranklist_songs().get_ranklist_songs(user_id=config.user_id, rank_type=config.rank_type_all))
