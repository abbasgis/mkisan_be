import json
import math
import re

import geopandas as gpd
import mapbox_vector_tile
import mercantile as mercantile
import numpy as np
from django.contrib.gis.geos import Polygon
from shapely.affinity import affine_transform
from shapely.wkt import loads

from api.local_settings import API_APP_LABEL
from api.logger.utils import DataLogger
from api.utils import DBQuery
from dch.maptiles.globel_map_tiles import GlobalMercator


class MVTUtils:
    @classmethod
    def to_lat_lon(cls, x, y, z):
        n = 2.0 ** z
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return lon_deg, lat_deg

    @classmethod
    def to_extent_4326(cls, x: int, y: int, z: int):
        n = math.pow(2, z)
        left_lon_deg = x / n * 360.0 - 180.0
        right_lon_deg = (x + 1) / n * 360.0 - 180.0
        top_lat_deg = (math.atan(math.sinh(math.pi * (1 - 2 * y / n)))) * 180 / math.pi
        bottom_lat_deg = (math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))) * 180 / math.pi
        gm = GlobalMercator()
        res = gm.TileLatLonBounds(x, y, z)
        return [res[1], res[0], res[3], res[2]]

    @classmethod
    def to_zxy(cls, extent: list, z: int = 6):
        gm = GlobalMercator()
        x1, y1 = gm.MetersToTile(extent[0], extent[1], z)
        x2, y2 = gm.MetersToTile(extent[2], extent[3], z)
        return x1, y1, x2, y2

    @classmethod
    def to_extent_3857(cls, x: int, y: int, z: int):
        tile_xyz = (x, y, z)
        tile_bounds = Polygon.from_bbox(mercantile.bounds(*tile_xyz))
        tile_bounds.srid = 4326
        tile_bounds.transform(3857)
        extent = tile_bounds.extent
        # extent = [-math.pi * 6378137, math.pi * 6378137]
        # tile_size = extent[1] * 2 / math.pow(2, z)
        # min_x = extent[1] + x * tile_size
        # max_x = extent[0] + (x + 1) * tile_size
        # max_y = extent[0] - y * tile_size
        # min_y = extent[1] - (y + 1) * tile_size
        # buff_size = 0
        # gm = GlobalMercator()
        # res = gm.TileBounds(x, y, z)
        # extent = list(res)
        # f = lambda i: res[i] if i % 2 == 0 else -res[i]
        # extent = [f(i) for i in range(len(res))]
        return extent
        # return [min_x + buff_size, min_y + buff_size, max_x + buff_size, max_y + buff_size]

    @classmethod
    def get_query(cls, table_name, geom_field, fields, x, y, z, srid):
        query = 'WITH mvtgeom AS (' \
                'SELECT ST_AsMVTGeom("%s", ' \
                'ST_TileEnvelope(%s, %s, %s), extent => 4096, buffer => 64) ' \
                'AS geom, %s ' \
                'FROM "%s" ' \
                'WHERE %s && ST_TileEnvelope(%s, %s, %s)' \
                ') SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom' % (
                    geom_field, z, x, y, fields, table_name, geom_field, z, x, y)
        print(query)
        return query

    @classmethod
    def to_mvt(cls, gdf: gpd.GeoDataFrame, name, tile_extent: tuple):
        features = []
        if not gdf.empty:
            # if gdf.crs.srs.upper() != 'EPSG:4326':
            #     gdf = gdf.to_crs('EPSG:4326')
            for k, v in gdf.dtypes.items():
                if str(v) == "geometry":
                    g_col = k

            def get_affine_matrix():
                # scale = 4096
                bounds = (0., 0., 4096., 4096.)
                (x0, y0, x_max, y_max) = tile_extent
                P = np.array([[x0, x0, x_max], [y0, y_max, y_max], [1, 1, 1]])
                Pd = np.array([[bounds[0], bounds[0], bounds[2]], [bounds[1], bounds[3], bounds[3]], [1, 1, 1]])
                A = np.matmul(Pd, np.linalg.inv(P))
                A = A.reshape(-1)
                # [a, b, d, e, xoff, yoff]
                a = [round(A[0], 3), round(A[1], 3), round(A[3], 3), round(A[4], 3), A[2], A[5]]
                return a

            A = get_affine_matrix()

            simpledec = re.compile(r"\d*\.\d+")

            # def m_round(match):
            #     return "{:.1f}".format(float(match.group()))
            #
            # def apply_affine(wkt):
            #     geom = loads(re.sub(simpledec, m_round, wkt))
            #     return affine_transform(geom, A)

            # geoms = gdf.geometry.apply(lambda x: loads(re.sub(simpledec, mround, x.wkt)))
            # geoms = gdf.geometry.apply(lambda x: apply_affine(x.wkt))
            geoms = gdf.geometry.affine_transform(A)
            geoms = geoms.simplify(1000, preserve_topology=True)
            for index, row in gdf.iterrows():
                try:
                    # geom = affine_transform(gdf.geometry[index], A)
                    # geom = geom.simplify(10, preserve_topology=True)
                    features.append({"geometry": geoms[index].wkb,
                                     "properties": {k: v for k, v in row.items() if k != g_col}})
                except Exception as e:
                    DataLogger.log_error_message(e)

        mvt = mapbox_vector_tile.encode({"name": name, "features": features})
        return bytes(mvt)


class GeoDBQuery(DBQuery):
    @classmethod
    def get_tile_extent(cls, x, y, z, app_labeL=API_APP_LABEL):
        query = f"SELECT ST_AsText( ST_TileEnvelope({z}, {x}, {y}) );"
        res = DBQuery.execute_query_as_one(query, app_labeL)
        polygon = Polygon.from_ewkt(res)
        return polygon.extent

    @classmethod
    def get_mvt_geom(cls):
        # query =
        pass

    @classmethod
    def execute_query_as_geojson(cls, query, app_label=API_APP_LABEL,
                                 geom_field='geom', is_json=True, styling="default"):
        geo_json_query = f"SELECT jsonb_build_object(" \
                         f"'type',     'FeatureCollection', " \
                         f"'styling', '{styling}', " \
                         f"'features', jsonb_agg(feature)) " \
                         f"FROM ( " \
                         f"SELECT jsonb_build_object( " \
                         f"'type', 'Feature', " \
                         f"'geometry',   ST_AsGeoJSON({geom_field})::jsonb," \
                         f"'properties', to_jsonb(row) - 'geom' -'geometry' - '{geom_field}'" \
                         f") AS feature " \
                         f"FROM ({query}) row) features;"
        result = DBQuery.execute_query_as_one(geo_json_query, app_label=app_label)
        if is_json:
            return json.loads(result)
        else:
            return result

    @classmethod
    def execute_query_as_mvt(cls, table_name, geom_field, fields, x, y, z, srid, app_label=API_APP_LABEL):
        query = MVTUtils.get_query(table_name, geom_field, fields, x, y, z, srid)
        mvt = cls.execute_query_as_one(query)
        mvt_bytes = bytes(mvt)
        return mvt_bytes
