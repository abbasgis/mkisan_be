import base64
import csv
import decimal
import json
import os
import shutil
import uuid
import logging
import traceback

from cryptography.fernet import Fernet

from django.apps import apps

from django.contrib.gis.db.backends.postgis.introspection import PostGISIntrospection
from django.db import connections
from django.http import HttpResponse

from mkisan_be.settings import DATABASES
from .local_settings import CONNECTION_KEY_TESTS, MODEL_FIELD_TYPES, API_APP_LABEL, DEFAULT_KEY, CRYPTO_KEY


class DBQuery(object):
    @classmethod
    def to_url(cls, key=DEFAULT_KEY, db_protocol='postgresql'):

        db = DATABASES[key]
        url = "%s://%s:%s@%s:%s/%s" % (db_protocol, db['USER'], db['PASSWORD'],
                                       db['HOST'], db['PORT'], db['NAME'])

        return url

    @classmethod
    def get_connection_key(cls, app_label=API_APP_LABEL, model_name=None, table_name=None):
        for key in CONNECTION_KEY_TESTS:
            if app_label in CONNECTION_KEY_TESTS[key]['APPS'] and model_name in CONNECTION_KEY_TESTS[key]['MODELS']:
                return CONNECTION_KEY_TESTS[key]['DB_KEY']
            elif table_name in CONNECTION_KEY_TESTS[key]['TABLES']:
                return CONNECTION_KEY_TESTS[key]['DB_KEY']
            elif app_label in CONNECTION_KEY_TESTS[key]['APPS']:
                return CONNECTION_KEY_TESTS[key]['DB_KEY']

        return 'default'

    @classmethod
    def get_cursor(cls, query, app_label=API_APP_LABEL):
        connection_name = DBQuery.get_connection_key(app_label)
        connection = connections[connection_name]
        cursor = connection.cursor()
        cursor.execute(query)
        return cursor

    @classmethod
    def execute_query_as_list(cls, query, app_label=API_APP_LABEL):
        connection_name = DBQuery.get_connection_key(app_label)
        connection = connections[connection_name]
        with connection.cursor() as cursor:
            cursor.execute(query)
            result_list = list(cursor.fetchall())
            cursor.close()
            return result_list

    @classmethod
    def execute_query_as_dict(self, query, is_geom_include=True, app_label=API_APP_LABEL, model_name=None):
        connection_name = DBQuery.get_connection_key(app_label)
        connection = connections[connection_name]
        result = None
        with connection.cursor() as cursor:
            cursor.execute(query)
            if is_geom_include:
                result_dict = DBQuery.dictfetchall(cursor)
            else:
                result_dict = DBQuery.dictfetchallXGeom(cursor)
            cursor.close()
        return result_dict

    @classmethod
    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    @classmethod
    def dictfetchallXGeom(cls, cursor):
        columns = []
        for col in cursor.description:
            dtype = cls.get_fields_type(col, cursor.connection)
            # if col[0] != "geom":
            if dtype not in MODEL_FIELD_TYPES["spatial"]:
                columns.append(col[0])
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    @classmethod
    def get_fields_type(cls, field, connection, db='PostGIS'):
        introspection = PostGISIntrospection(connection)
        return introspection.get_field_type(field.type_code, field)

    @classmethod
    def execute_query_as_flat_list(cls, query, app_label=API_APP_LABEL, model_name=None):
        connection_name = DBQuery.get_connection_key(app_label, model_name)
        connection = connections[connection_name]
        result = []
        with connection.cursor() as cursor:
            cursor.execute(query)
            result_qs = cursor.fetchall()
            for obj in result_qs:
                result.append(obj[0])
        return result

    @classmethod
    def execute_query_as_one(cls, query, app_label=API_APP_LABEL, model_name=None, connection=None):
        if not connection:
            connection_name = DBQuery.get_connection_key(app_label, model_name)
            connection = connections[connection_name]
        result = None
        with connection.cursor() as cursor:
            cursor.execute(query)
            cur_res = cursor.fetchone()
            if cur_res is not None:
                result = cur_res[0]
            cursor.close()
        return result

    @classmethod
    def execute_dml(self, query, app_label=API_APP_LABEL, model_name=None):
        connection_name = DBQuery.get_connection_key(app_label, model_name)
        connection = connections[connection_name]
        cursor = connection.cursor()
        res = cursor.execute(query)
        return res


class ModelUtils:
    @classmethod
    def get_model_filter_result_dict(cls, app_label, model_name, field_value, field_name='id'):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        res = list(model.objects.filter(**{field_name: field_value}).values())
        return res

    @classmethod
    def get_model_fields_names(cls, app_label, model_name, include_geometry=False):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        fields = model._meta.get_fields()
        field_names = [];
        skip_field_types = MODEL_FIELD_TYPES["relational"] + MODEL_FIELD_TYPES["spatial"] if not include_geometry else [
            "AutoField"]
        for field in fields:
            if field.get_internal_type() not in skip_field_types:
                field_names.append({"name": field.name, "db_col": field.column, "type": field.get_internal_type()})
        return field_names

    @classmethod
    def get_model_col_name(cls, model):
        fields_name = cls.get_model_fields_names(model._meta.app_label, model._meta.model_name)
        cols = []
        for field in fields_name:
            cols.append(field['name'])
        return cols

    @classmethod
    def get_model_spatial_cols_names(cls, model):
        fields = model._meta.get_fields()
        cols = []
        for field in fields:
            if field.get_internal_type() in MODEL_FIELD_TYPES["spatial"]:
                cols.append(field.name)
        return cols

    @classmethod
    def get_model_foreign_cols_names(cls, model):
        fields = model._meta.get_fields()
        cols = []
        for field in fields:
            if field.get_internal_type() in MODEL_FIELD_TYPES["relational"]:
                if field.many_to_one == True:
                    cols.append(field.name)
        return cols

    @classmethod
    def get_field_name_list(cls, model, skip_fields=[]):
        # if store._meta.model_name.lower() == 'courseallocation':
        #     print("Found")
        # print(store._meta.model_name)
        fields = model._meta.get_fields()
        field_names = []
        for field in fields:
            if not (field.name in skip_fields) and not field.one_to_many:
                field_names.append(field.name)

        return field_names


class CommonUtils:
    @classmethod
    def export_to_csv(cls, field_names, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
            'working_hours')
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    @classmethod
    def removeAllFiles(cls, location):
        shutil.rmtree(location, ignore_errors=True)
        # files = glob.glob(location + "/*")
        # for f in files:
        #     if os.path.isfile(f)      :
        #         os.remove(f)

    @classmethod
    def get_uuid1(cls):
        uuid1 = uuid.uuid1()
        return str(uuid1)

    @classmethod
    def removeAllSpecialCharacter(cls, string, replace_with):
        output = ''
        for character in string:
            if character.isalnum():
                output += character
            else:
                output += replace_with
        return output

    @staticmethod
    def handle_uploaded_file(uploaded_file, destination_path):
        with open(destination_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

    @classmethod
    def make_dirs(cls, fp):
        dir_name = os.path.dirname(fp)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


class CryptoUtils:
    encode_scheme = 'utf-8'
    # key = Fernet.generate_key()
    # key = 'sOdFCgtaru8UxtdEbtuAfWdN7E1r_9C1FREoZVb02EI='
    key = CRYPTO_KEY

    def encrypt_txt(self, txt):
        # convert integer etc to string first
        txt = str(txt)
        # key = Fernet.generate_key()
        # decode_key = key.decode(self.encode_scheme)
        # get the key from settings
        fernet_key = self.key.encode(self.encode_scheme)
        cipher_suite = Fernet(fernet_key)  # key should be byte
        # #input should be byte, so convert the text to byte
        encrypted_text = cipher_suite.encrypt(txt.encode(self.encode_scheme))
        # encode to urlsafe base64 format
        encrypted_text = base64.urlsafe_b64encode(encrypted_text).decode("ascii")
        return encrypted_text

    def decrypt_txt(self, txt):
        try:
            # base64 decode
            txt = base64.urlsafe_b64decode(txt)
            fernet_key = self.key.encode(self.encode_scheme)
            cipher_suite = Fernet(fernet_key)
            decoded_text = cipher_suite.decrypt(txt).decode("ascii")
            return decoded_text
        except Exception as e:
            # log the error
            logging.getLogger("error_logger").error(traceback.format_exc())
            return None


class PDUtils:
    @staticmethod
    def getColGenericType(d_type: str):
        number_types = ["int64", "float64"]
        date_types = ["datetime64"]
        if d_type in number_types:
            return "number"
        elif d_type in date_types:
            return "date"
        else:
            return "string"
