#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sqlite3
import re
from vavava import sqliteutil

SQL_CREATE_TABLES = """
        CREATE TABLE IF NOT EXISTS url(
            id integer primary key,
            title TEXT,
            url varchar(512),
            post_time real,
            category_id int,
            create_time real
            );
            CREATE TABLE IF NOT EXISTS category (
            id integer,
            cid integer,
            name TEXT
        );
"""

class DBCategory:
    def __init__(self, path=""):
        self.db_path = path


class DBRowUrl:
    def __init__(self, title="", url="",
                 post_time="1900-01-01 00:00", category=0):
        if url == "":
            return
        try:
            self.id = -1
            self.title = title
            self.url = url
            # tt = re.compile(r"(?P<tt>\d{4}(--|-)\d{1,2}(--|-)\d{1,2}(\s|@)\d{1,2}:\d{1,2})")
            # post_time = tt.findall(post_time)[0][0].replace('--', '-').replace('@', ' ')
            self.post_time = time.mktime(
                time.strptime(post_time, "%Y-%m-%d %H:%M"))
            self.category_id = category
            self.create_time = time.time()
        except Exception as e:
            print e.message
            print title
            print url


class DBUrl:
    def __init__(self, db_path="tmp.db3"):
        self.db_path = db_path
        self.__conn = self.get_conn()
        self.create_db(SQL_CREATE_TABLES)

    def get_conn(self):
        try:
            re = self.__get_conn()
        except Exception as e:
            print e.message
        return re

    def create_db(self, script):
        try:
            self.__conn.executescript(script)
        except Exception as e:
            print e.message

    def insert(self, url):
        try:
            re = self.__insert(url)
        except Exception as e:
            print e.message
        return re

    def insert_category(self, cid, name):
        try:
            sql = "insert into category(cid, name) values('%d','%s') " %(cid, name)
            self.__conn.execute(sql)
            self.__conn.commit()
        except Exception as e:
            # print e.message
            pass

    def query_by_title(self, key=None, categories=[], page_num=1, page_size=10):
        re = None
        try:
            re = self.__query_by_title( key, categories, page_num, page_size )
        except Exception as e:
            print e.message
        return re

    def __get_conn(self):
        try:
            self.__conn = sqlite3.connect(self.db_path, timeout=3)
            return self.__conn
        except Exception as e:
            print e.message

    def __insert(self, url):
        try:
            already_in_db = self.__query_by_url(url.url)
            if already_in_db and len(already_in_db)>0:
                return False
            sql = "insert into url(title,url,post_time,category_id,create_time) "\
                  "values('%s','%s',%f,%d,%f) "\
                  %(url.title,url.url,url.post_time,url.category_id,url.create_time)
            self.__conn.execute(sql)
            self.__conn.commit()
            return True
        except Exception as e:
            print e.message
            return False

    def __query_by_title(self,key,categories,page_num,page_size):
        if key:
            key = unicode(key, 'gbk')
            key = key.strip()
        # init query sql
        catagory_condition = ""
        tmp_categories = []
        for i in range(len(categories)):
            tmp = categories[i]
            if isinstance(tmp,type("str")) and tmp.strip() != "":
                tmp_categories.append(int(tmp))
        if len(tmp_categories) > 0:
            for i in range(len(tmp_categories)):
                catagory = tmp_categories[i]
                if i > 0:
                    catagory_condition += " or category_id=%d "%catagory
                else:
                    catagory_condition += " and ( category_id=%d "%catagory
            catagory_condition += " ) "
        if key and key != "":
            sql1 = r"select count(id) from url "\
                  r"where title like '%%%s%%' %s"%(key,catagory_condition)
            sql2 = r"select * from url "\
                  r"where title like '%%%s%%' %s"\
                  r"order by track_time title "%(key,catagory_condition)
        else:
            sql1 = r"select count(id) from url "
            sql2 = r"select * from url order by post_time title "
        cursor = None
        try:
            cursor = self.__conn.cursor()
            cursor.execute(sql1)
            print "sql1=%s",sql1
            dbset = cursor.fetchone()
             #data list size
            if dbset > 0:
                total = int(dbset[0])
            else:
                total = 0
            if page_size and page_size > 0:
                page_num = int(page_num)
                page_size = int(page_size)
                if page_size > 0:
                    sql2 += r" limit %d Offset %d"%(page_size,page_size*page_num)
            print "query(total=%d):%s",total,sql2
            cursor.execute(sql2)
            dbset = cursor.fetchall()
            re = []
            for row in dbset:
                item = DBRowUrl()
                item.id          = row[0]
                item.title       = row[1]
                item.url         = row[2]
                item.post_time  = time.localtime(row[3])
                item.category_id = row[4]
                item.create_time = time.localtime(row[5])
                re.append( item )
            cursor.close()
            return re,total
        except Exception as e:
            if cursor: cursor.close()
            print e.message

    def __query_by_url(self,url):
        cursor = None
        try:
            cursor = self.__conn.cursor()
            sql = r"select * from url where url='%s'" % url
            cursor.execute(sql)
            dbset = cursor.fetchall()
            re = []
            for row in dbset:
                item = DBRowUrl()
                item.id          = row[0]
                item.title       = row[1]
                item.url         = row[2]
                item.post_time  = time.localtime(row[3])
                item.category_id = row[4]
                item.create_time = time.localtime(row[5])
                re.append( item )
            cursor.close()
            return re
        except Exception as e:
            if cursor: cursor.close()
            print e.message

    def __get_categories(self):
        cursor = None
        try:
            cursor = self.__conn.cursor()
            sql = r"select distinct id from url order by id"
            cursor.execute(sql)
            dbset = cursor.fetchall()
            re = []
            for row in dbset:
                re.append( row[0] )
            cursor.close()
            return re
        except Exception as e:
            if cursor: cursor.close()
            print e.message

    def __del__(self):
        if self.__conn:
            self.__conn.close()


# insert work for sqlite_util.dbpool
class Insert(sqliteutil.WorkBase):
    def __init__(self, url):
        self.url = url

    def handle(self, db):
        if not isinstance(db, DBUrl):
            raise ValueError("DBUrl needed")
        if db.insert(self.url):
            print "[new] ", self.url.post_time, " ", self.url.title
        # else:
        #     print "[old] ", self.url.post_time, " ", self.url.title

class InsertCagegory(sqliteutil.WorkBase):
    def __init__(self, cid, name):
        self.cid = cid
        self.name = name

    def handle(self, db):
        if not isinstance(db, DBUrl):
            raise ValueError("DBUrl needed")
        if db.insert_category(self.cid, self.name):
            print "[new category] ", self.cid, " ", self.name

class Query(sqliteutil.WorkBase):
    def __init__(self, key=None, categories=[],
                 page_num=1, page_size=10, callback=None):
        self.key = key
        self.categories = categories
        self.pn = page_num
        self.ps = page_size
        self.callback = callback
        self.handle = lambda self, db:self.callback(
            db.query_by_title(self.key, self.categories, self.pn, self.ps))

import unittest
class TestUtil(unittest.TestCase):
    def testDBRowUrl(self):
        post = 'ss2012--11--3@12:1 123'
        tt = re.compile(r"(?P<tt>\d{4}(--|-)\d{1,2}(--|-)\d{1,2}(\s|@)\d{1,2}:\d{1,2})")
        post = tt.findall(post)[0][0].replace('--', '-').replace('@', ' ')
        print DBRowUrl(title='title', url='url',
                 post_time=post, category=0).post_time

if __name__ == "__main__":
    unittest.main()
