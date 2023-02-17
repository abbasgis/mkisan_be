from api.utils import DBQuery


class MultiDatabaseRouter(object):
    def db_for_read(self, model, **hints):
        connection_name = DBQuery.get_connection_key(model._meta.app_label, model._meta.model_name)
        return connection_name

    def db_for_write(self, model, **hints):
        connection_name = DBQuery.get_connection_key(model._meta.app_label, model._meta.model_name)
        return connection_name

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # print("%s, %s, %s") %(db,app_label,model_name)
        # ALDBAPP = []  # ['auth']
        # ALLDBMODELS = ['contenttype']
        # if app_label in ALLDBAPP or model_name in ALLDBMODELS:
        #     return True

        req_db = DBQuery.get_connection_key(app_label, model_name)
        if db == req_db:
            return True

        return False
        # return None
