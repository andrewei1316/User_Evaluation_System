#!/usr/bin/env python
# -*- coding: utf-8 -*-

class DBRouter(object):

    def db_for_read(self, model, **hints):
        #该方法定义读取时从哪一个数据库读取
        return self.__app_router(model)

    def db_for_write(self, model, **hints):
        #该方法定义写入时从哪一个数据库读取，如果读写分离，可再额外配置
        return self.__app_router(model)

    def allow_relation(self, obj1, obj2, **hints):
        #该方法用于判断传入的obj1和obj2是否允许关联，可用于多对多以及外键
        #同一个应用同一个数据库
        if self.__app_router(obj1) == self.__app_router(obj2):
            return True
        return None;

    def allow_migrate(self, db, app_label, model=None, **hints):
        """
        Make sure the auth app only appears in the 'auth_db'
        database.
        """
        if model:
            return self.__app_router(model) == db
        else:
            return self.__app_label_router(app_label)


    def allow_syncdb(self, db, model):
        #该方法定义数据库是否能和名为db的数据库同步
        return self.__app_router(model) == db

    def __app_label_router(self, app_label):
        # print 'app_label =', app_label
        if app_label in ['users', 'admin', 'auth', 'contenttypes', 'sessions']:
            return 'onlinejudge_db'           
        else:
            return 'default'

    def __app_router(self, model):
       #添加一个私有方法用来判断模型属于哪个应用，并返回应该使用的数据库
        app_label = model._meta.app_label
        return self.__app_label_router(app_label)
