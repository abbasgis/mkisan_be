from typing import Union

import xml.etree.ElementTree as ET
import pandas as pd
from django.contrib.postgres.fields import ArrayField
from django.db import models, connections
from django.db.models import JSONField
from django.utils import timezone
from sqlalchemy import create_engine

from api.logger.middleware.RequestInfo import get_current_user_id
from api.model_fields import DAHistoricalRecords, UserForeignKey
from api.utils import CryptoUtils, DBQuery
from map_viewer.enum import DataModel, VectorModel, RasterModel, AccessibilityType
import geopandas as gpd


class LayerCategory(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class LayerQualityLevel(models.Model):
    level = models.IntegerField()
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class DBConnection(models.Model):
    name = models.CharField(unique=True, max_length=100)
    params = JSONField()

    def __str__(self):
        return self.name

    @staticmethod
    def get_db_conection(con_name: str, engine: str = None,
                         host: str = None, port: str = None,
                         user: str = None, password: str = None,
                         db_name: str = None):
        if not DBConnection.objects.filter(name=con_name).exists():
            db_conn = DBConnection()
            db_conn.name = con_name
            db_conn.params = {
                "engine": engine,
                "host": host,
                "port": port,
                "user": user,
                "password": CryptoUtils().encrypt_txt(password),
                "db_name": db_name
            }
            db_conn.save()
        else:
            db_conn = DBConnection.objects.filter(name=con_name).first()
        return db_conn

    def get_sqlalchemy_engine(self):
        conn = self.params
        pwd = CryptoUtils().decrypt_txt(conn["password"])
        db_connection_url = f"{conn['engine']}://{conn['user']}:{pwd}@{conn['host']}:{conn['port']}/{conn['db_name']}"
        engine = create_engine(db_connection_url)
        return engine

    def get_django_connection(self):
        conn = self.params
        pwd = CryptoUtils().decrypt_txt(conn["password"])
        # id = self.name
        if not self.name in connections.databases.keys():
            db_params = {
                "id": self.name,
                "ENGINE": "django.contrib.gis.db.backends.postgis",
                "NAME": conn['db_name'],
                "USER": conn['user'],
                "PASSWORD": pwd,
                "HOST": conn['host'],
                "PORT": conn['port']
            }
            connections.databases[self.name] = db_params
        return connections[self.name]


class LayerAccessibility(models.Model):
    accessibility_type = models.CharField(max_length=30, choices=AccessibilityType.choices(), null=True, blank=True)
    params = JSONField()

    def __str__(self):
        return self.accessibility_type

    @classmethod
    def create_file_accessibility(cls, file_path: str):
        la = cls()
        la.accessibility_type = AccessibilityType.File.name
        la.params = {"file_path": file_path}
        la.save()
        return la

    @staticmethod
    def create_db_accessibility(table_name: str, db_conn: Union[DBConnection, str], columns: dict, pk_cols: list):
        cols = []
        g_col = None

        def getType(dtype: str):
            number_types = ["int64", "float64"]
            date_types = ["datetime64"]
            if dtype in number_types:
                return "number"
            elif dtype in date_types:
                return "date"
            else:
                return "string"

        for k, v in columns.items():
            v = str(v)
            if v != "geometry":
                cols.append({"name": k, "d_type": getType(v)})
            else:
                g_col = k
        params = {
            "conn_name": db_conn.name if isinstance(db_conn, DBConnection) else db_conn,
            "table_name": table_name,
            "columns": cols,
            "g_col": g_col,
            "pk_cols": pk_cols
        }
        qs = LayerAccessibility.objects.filter(params__conn_name=params["conn_name"],
                                               params__table_name=params["table_name"])
        if not qs.exists():
            la = LayerAccessibility()
        else:
            la = qs.first()
        la.accessibility_type = AccessibilityType.DB.name
        la.params = params
        la.save()
        return la


class LayerInfo(models.Model):
    uuid = models.CharField(max_length=40, unique=True)
    app_label = models.CharField(max_length=100, default='gis')
    title = models.CharField(max_length=255)
    layer_name = models.CharField(max_length=100)
    layer_access = models.ForeignKey(LayerAccessibility, on_delete=models.CASCADE)
    srid = models.IntegerField(null=True, blank=True)
    proj4 = models.TextField(null=True, blank=True)
    extent = ArrayField(base_field=models.FloatField(), null=True, blank=True)
    data_model = models.CharField(max_length=30, choices=DataModel.choices(), null=True, blank=True)
    vector_type = models.CharField(max_length=20, null=True, blank=True, choices=VectorModel.choices())
    raster_type = models.CharField(max_length=20, null=True, blank=True, choices=RasterModel.choices())
    geom_type = ArrayField(base_field=models.CharField(max_length=50), null=True, blank=True)
    layer_styling = JSONField(null=True, blank=True)
    zoom_range = ArrayField(base_field=models.FloatField(), default=[0, 30])
    category = models.ForeignKey(LayerCategory, on_delete=models.DO_NOTHING, null=True, blank=True)
    quality_level = models.ForeignKey(LayerQualityLevel, on_delete=models.DO_NOTHING, null=True, blank=True)
    dataset_info = JSONField(null=True, blank=True)
    uploaded_by = UserForeignKey(null=True, blank=True)
    updated_date = models.DateTimeField(default=timezone.now)
    creation_date = models.DateField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    # history = DAHistoricalRecords()

    def __str__(self):
        return self.layer_name

    def save(self, *args, **kwargs):
        if not self.uploaded_by:
            self.uploaded_by = get_current_user_id()
        super().save(*args, **kwargs)

    def to_df(self, cols=[]) -> pd.DataFrame:
        if self.data_model == DataModel.V.name:
            if self.layer_access.accessibility_type == AccessibilityType.DB.name:
                params = self.layer_access.params
                engine = DBConnection.objects.filter(name=params["conn_name"]) \
                    .first() \
                    .get_sqlalchemy_engine()
                if len(cols) == 0:
                    cols = [info['name'] for info in params['columns']
                            if not info["name"].lower() in ["extent", params['g_col'], "geojson", "geom"]]
                select_cols = ','.join(f'"{c}"' for c in cols)
                query = f"Select {select_cols} from {params['table_name']}"

                df = pd.read_sql(query, con=engine)
                return df

    def get_col_name(self, cols=[]):
        params = self.layer_access.params
        pk_cols = "," + ",".join(params["pk_cols"]) if len(params["pk_cols"]) > 0 else ""
        style_cols = []
        if self.layer_styling and self.layer_styling["type"] == "sld":
            xml_str = self.layer_styling['style']
            tree = ET.ElementTree(ET.fromstring(xml_str))
            root = tree.getroot()
            for property_tag in root.findall('.//{http://www.opengis.net/ogc}PropertyName'):
                style_cols.append(property_tag.text)

        elif self.layer_styling and self.layer_styling["type"] not in ["single", "sld"]:
            style_cols = [rule["filter"]["field"] for rule in self.layer_styling["style"]["rules"]]
        cols = set(cols + style_cols)
        cols = "," + ",".join(cols) if len(cols) > 0 else ""
        return pk_cols, cols

    def to_mvt(self, x, y, z, cols=[]) -> gpd.GeoDataFrame:
        if self.layer_access.accessibility_type == AccessibilityType.DB.name:
            params = self.layer_access.params
            connection = DBConnection.objects.filter(name=params["conn_name"]) \
                .first() \
                .get_django_connection()
            if 'postgis' in str(connection):
                g_col = f"{params['g_col']}" if self.srid == 3857 else f"st_transform({params['g_col']}, 3857)"
                pk_cols, cols = self.get_col_name(cols)
                query = f"WITH mvtgeom AS(" \
                        f"SELECT ST_AsMVTGeom({g_col}, ST_TileEnvelope({z}, {x}, {y}), " \
                        f"extent => 4096, buffer => 64) as geom {pk_cols} {cols} " \
                        f"from {params['table_name']} " \
                        f") SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom where geom is not null"

                print(query)
                mvt = DBQuery.execute_query_as_one(query, connection=connection)
                return bytes(mvt)

    def to_gdf(self, extent_3857: list, cols=[]) -> gpd.GeoDataFrame:
        if self.data_model == DataModel.V.name:
            if self.layer_access.accessibility_type == AccessibilityType.DB.name:
                params = self.layer_access.params
                engine = DBConnection.objects.filter(name=params["conn_name"]) \
                    .first() \
                    .get_sqlalchemy_engine()

                # envelop = box(*extent_3857)
                # envelop = Polygon.from_bounds(*extent_3857)
                # columns = []

                min_x = extent_3857[0]
                min_y = extent_3857[1]
                max_x = extent_3857[2]
                max_y = extent_3857[3]
                wkt = f'POLYGON(({min_x} {min_y}, {max_x} {min_y},{max_x} {max_y},{min_x} {max_y},{min_x} {min_y}))'
                if engine.name == 'postgresql':
                    g_col = f"{params['g_col']}" if self.srid == 3857 else f"st_transform({params['g_col']}, 3857)"
                    pk_cols, cols = self.get_col_name(cols)
                    query = f"Select {g_col} as geom {pk_cols} {cols} from {params['table_name']} " \
                            f"where st_intersects({g_col}, st_geomfromtext('{wkt}',3857))"
                    # print(query)
                    gdf = gpd.read_postgis(query, con=engine)
                    return gdf

    def get_row_detail(self, col_name, col_value):
        params = self.layer_access.params
        connection = DBConnection.objects.filter(name=params["conn_name"]) \
            .first() \
            .get_django_connection()
        if 'postgis' in str(connection):
            query = f"SELECT * " \
                    f"from {params['table_name']} " \
                    f"where {col_name} = '{col_value}'"
            with connection.cursor() as cursor:
                cursor.execute(query)
                result_dict = DBQuery.dictfetchall(cursor)
                cursor.close()
            return result_dict


unit_choices = (('m', 'meter'), ('ft', 'feet'), ('dd', 'decimal_degree'))


class MapInfo(models.Model):
    uuid = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=100)
    extent = ArrayField(base_field=models.FloatField(), default=[-20037508.3427892,
                                                                 -20037508.3427892,
                                                                 20037508.3427892,
                                                                 20037508.3427892])
    layers = JSONField()
    srid = models.IntegerField(default=3857)
    units = models.CharField(max_length=10, default='m', choices=unit_choices)
    description = models.TextField(null=True, blank=True)
