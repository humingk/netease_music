# !/usr/bin/env python
# -*- coding: utf-8 -*-

# author: humingk
# ----------------------
from DBUtils.PooledDB import PooledDB
import pymysql
import config
from my_tools.logger_tool import loggler_tool
import time
import warnings

logger = loggler_tool()

# 数据库信息
database_host = config.database_host
database_port = config.database_port
database_user_name = config.database_user_name
database_user_pwd = config.database_user_pwd
database_name = config.database_name
database_charset = config.database_charset

# 数据库连接池(PooledDB)
database_pool = PooledDB(
    # 使用数据库的模块
    creator=pymysql,
    # 数据库最大连接数
    maxconnections=10,
    # 初始化时，链接池中至少创建的空闲的链接
    mincached=5,
    # 初始化时，链接池中至多创建的空闲的链接,0不限制
    maxcached=0,
    # 链接池中最多共享的链接数量
    # PS: 由于pymysql和MySQLdb模块的threadsafety都为1
    # 所以_maxcached永远为0，所有链接都共享
    maxshared=10,
    # 连接池中如果没有可用连接后，是否阻塞等待
    blocking=True,
    # 一个链接最多被重复使用的次数，None表示无限制
    maxusage=None,
    # 开始会话前执行的命令列表,如["set datestyle to ...", "set time zone ..."]
    setsession=[],
    # ping MySQL服务端，检查是否服务可用
    # 如：0 = None = never, 1 = default = whenever it is requested,
    # 2 = when a cursor is created, 4 = when a query is executed, 7 = always
    ping=0,
    host=database_host,
    port=database_port,
    user=database_user_name,
    password=database_user_pwd,
    database=database_name,
    charset=database_charset
)


class database_tool:
    """
    数据库连接池工具类

    """

    def __init__(self):
        """
        初始化连接池

        """
        self.database_pool = database_pool
        self.connection = None
        self.__connect()

    def __connect(self):
        """
        建立数据库连接

        """
        try:
            self.connection = database_pool.connection()
        except Exception as e:
            logger.error("database connect failed", "error_type:{},error:{}".format(type(e), e))

    def execute(self, sql):
        """
        execute语句

        :param sql: sql语句
        :return: 执行状态
        """
        try:
            if self.connection is None:
                self.__connect()
            self.connection.cursor().execute(sql)
            return True
        except pymysql.err.IntegrityError as e:
            # 主键重复
            if e.args[0] == 1062:
                logger.debug("database execute duplicate", "sql:{},error_type:{},error:{}".format(sql, type(e), e))
            # 外检约束
            elif e.args[0] == 1452:
                logger.warning("database execute need foreign key",
                               "sql_count:{},sql:{},error_type:{},error:{}".format(len(data_list), sql, type(e), e))
            else:
                logger.error("database execute failed", "sql:{},error_type:{},error:{}".format(sql, type(e), e))
        except Exception as e:
            logger.error("database execute failed", "sql:{},error_type:{},error:{}".format(sql, type(e), e))
        finally:
            return False

    def executemany(self, sql, data_list):
        """
        executemany语句

        :param sql: sql语句
        :param data_list: 数据列表
        :return: 执行状态
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if self.connection is None:
                    self.__connect()
                self.connection.cursor().executemany(sql, data_list)
                # logger.info("database executemany success", "sql_count:{},sql:{}".format(len(data_list), sql))
                return True
            except pymysql.err.IntegrityError as e:
                # 主键重复
                if e.args[0] == 1062:
                    logger.debug("database executemany duplicate",
                                 "sql_count:{},sql:{},error_type:{},error:{}".format(len(data_list), sql, type(e), e))
                # 外检约束
                elif e.args[0] == 1452:
                    logger.warning("database executemany need foreign key",
                                   "sql_count:{},sql:{},error_type:{},error:{}".format(len(data_list), sql, type(e), e))
                else:
                    logger.error("database executemany failed",
                                 "sql_count:{},sql:{},error_type:{},error:{}".format(len(data_list), sql, type(e), e))
            except Exception as e:
                logger.error("database executemany failed",
                             "sql_count:{},sql:{},error_type:{},error:{}".format(len(data_list), sql, type(e), e))
        return False

    def commit(self):
        try:
            self.connection.commit()
            return True
        except Exception as e:
            logger.error("database commit failed", "error_type:{},error:{}".format(type(e), e))
            return False

    def close(self):
        try:
            self.connection.close()
            return True
        except Exception as e:
            logger.error("database conn close failed", "error_type:{},error:{}".format(type(e), e))
            return False

    # 表插入封装 -----------------

    def insert_many_user(self, data_list):
        self.executemany(
            "insert into user(user_id,user_name) values(%s,%s) on duplicate key update user_id = user_id,user_name=user_name",
            data_list
        )

    def insert_many_ranklist(self, data_list):
        self.executemany(
            "insert into ranklist(ranklist_id, ranklist_type,ranklist_date) values (%s,%s,%s) on duplicate key update ranklist_id = ranklist_id",
            data_list
        )

    def insert_many_song(self, data_list):
        self.executemany(
            "insert into song(song_id,song_name) values (%s,%s) on duplicate key update song_id = song_id,song_name=song_name",
            data_list
        )

    def insert_many_user_ranklist(self, data_list):
        self.executemany(
            "insert into user_ranklist(user_id,ranklist_id) values (%s,%s) on duplicate key update user_id = user_id",
            data_list
        )

    def insert_many_song_ranklist(self, data_list):
        self.executemany(
            "insert into song_ranklist(song_id,ranklist_id,song_score) values (%s,%s,%s) on duplicate key update song_id = song_id",
            data_list
        )

    def insert_many_playlist(self, data_list):
        self.executemany(
            "insert into playlist(playlist_id,playlist_name,playlist_songs_total,playlist_play_count,playlist_update_date) values (%s,%s,%s,%s,%s)  on duplicate key update playlist_id = playlist_id",
            data_list
        )

    def insert_many_user_playlist(self, data_list):
        self.executemany(
            "insert into user_playlist(user_id,playlist_id,playlist_type) values (%s,%s,%s) on duplicate key update user_id = user_id",
            data_list
        )

    def insert_many_song_playlist(self, data_list):
        self.executemany(
            "insert into song_playlist(song_id,playlist_id,playlist_type) values (%s,%s,%s) on duplicate key update song_id = song_id",
            data_list
        )

    def insert_many_comment(self, data_list):
        self.executemany(
            "insert into comment(comment_id, comment_type, comment_date, comment_content,comment_like_count) values (%s,%s,%s,%s,%s) on duplicate key update comment_id = comment_id",
            data_list
        )

    def insert_many_song_comment(self, data_list):
        self.executemany(
            "insert into song_comment(song_id,comment_id) values (%s,%s) on duplicate key update song_id = song_id",
            data_list
        )

    def insert_many_user_comment(self, data_list):
        self.executemany(
            "insert into user_comment(user_id,comment_id) values (%s,%s) on duplicate key update user_id = user_id",
            data_list
        )

    def insert_many_artist(self, data_list):
        self.executemany(
            "insert into artist(artist_id,artist_name,artist_score) values (%s,%s,%s) on duplicate key update artist_id = artist_id",
            data_list
        )

    def insert_many_artist_song(self, data_list):
        self.executemany(
            "insert into artist_song(artist_id,song_id) values (%s,%s) on duplicate key update artist_id = artist_id",
            data_list
        )

    # 表更新封装 ----------------------

    def update_song_hot_comment_count(self, song_id, song_hot_comment_count=0):
        self.execute(
            "update song set song_hot_comment_count={} where song_id={}"
                .format(song_hot_comment_count, song_id)
        )

    def update_song_default_comment_count(self, song_id, song_default_comment_count=0):
        self.execute(
            "update song set song_default_comment_count={} where song_id={}"
                .format(song_default_comment_count, song_id)
        )


def test(pool, data_list):
    pool.insert_many_song(data_list)


if __name__ == '__main__':
    time1 = time.clock()

    _database_tool = database_tool()
    data_list = []
    for i in range(100001, 200000):
        data_list.append((i, i * 2))
    _database_tool.insert_many_user(data_list)
    _database_tool.commit()
    _database_tool.close()

    time2 = time.clock()

    _database_tool = database_tool()
    for i in range(100):
        _database_tool.insert_many_user([(i, i * 3)])
    _database_tool.insert_many_user([(11, 11 * 3), (111, 22 * 3), (112, 33 * 3)])
    _database_tool.commit()
    _database_tool.close()

    time3 = time.clock()
    print(time2 - time1)
    print(time3 - time2)
