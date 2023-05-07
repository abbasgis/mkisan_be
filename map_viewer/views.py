import json
import os
import numpy as np
from django.contrib.gis.gdal.geometries import Polygon
from django.db.models import F
from django.http import HttpResponse
from rest_framework import decorators, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rio_tiler.colormap import cmap

from api.utils import PDUtils, CommonUtils
from map_viewer.raster_utils.cog_raster import COGRaster
from map_viewer.raster_utils.rio_raster import RioRaster
from map_viewer.binary_renderer import BinaryRenderer
from map_viewer.models import LayerInfo
from rasterio.mask import mask
# @decorators.permission_classes([permissions.AllowAny])
from mkisan_be.settings import COG_DIR


@decorators.api_view(["GET"])
def layer_info(request, uuid):
    info = LayerInfo.objects.filter(uuid=uuid).annotate(style=F('layer_styling'),
                                                        zoomRange=F('zoom_range'),
                                                        dataModel=F('data_model'),
                                                        geomType=F('geom_type')) \
        .values('uuid', 'title', 'style', 'zoomRange', 'dataModel', 'geomType', 'category').first()
    return Response({"payload": info})


class TileView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, uuid, z, x, y):
        # tile_size = 256
        # cog_raster = COGRaster()
        info = LayerInfo.objects.filter(uuid=uuid).first()
        if info.data_model == 'R':
            if info.layer_access.accessibility_type == 'File':
                params = info.layer_access.params
                style = info.layer_styling
                file_path = os.path.join(COG_DIR, params['file_path'])
                cog_raster = COGRaster.open_from_local(file_path)
                # cm = COGRaster.create_custom_color_map(info.layer_styling)
                cm = cmap.get("gist_rainbow")
                data = cog_raster.read_tile_as_png(x, y, z, color_map=cm)
                return HttpResponse(data, content_type="image/png")


class MVTView(APIView):
    renderer_classes = (BinaryRenderer,)
    permission_classes = (permissions.AllowAny,)

    def get(self, request, uuid, z, x, y):
        # extent1 = GeoDBQuery.get_tile_extent(x, y, z)
        if "cols" in request.GET.keys():
            cols = request.GET["cols"].split(",")
        else:
            cols = []
        # print(cols)
        info = LayerInfo.objects.filter(uuid=uuid).first()
        # start = time.time()
        # extent = MVTUtils.to_extent_3857(x, y, z)
        # gdf = info.to_gdf(extent, cols)
        # mvt_bytes = MVTUtils.to_mvt(gdf, info.layer_name, extent)
        mvt_bytes = info.to_mvt(x, y, z)
        # end = time.time()

        # print("tile", z, x, y, "time taken", (end - start), )
        if mvt_bytes.__len__() == 0:
            # res_status = status.HTTP_400_BAD_REQUEST
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(mvt_bytes, content_type="application/vnd.mapbox-vector-tile", status=status.HTTP_200_OK)


@decorators.api_view(["GET"])
def get_layer_attributes(request, uuid):
    qs = LayerInfo.objects.filter(uuid=uuid)
    if qs.exists():
        info = qs.first()
        df = info.to_df()
        columns = [{"id": col,
                    "label": col.title().replace("_", " ") + (
                        ' USD in Million' if 'float' in str(df[col].dtype) else ''),
                    # "isNumeric": isNumeric(str(df[col].dtype)),
                    "type": PDUtils.getColGenericType(str(df[col].dtype)),
                    "disablePadding": False} for col in df.columns.tolist()]
        df = df.fillna('')
        df = df.round(0)
        return Response({"payload": {
            "columns": columns,
            "rows": df.to_dict(orient='records')}},
            status=status.HTTP_200_OK)


@decorators.api_view(["GET"])
def get_layer_extent(request, uuid):
    qs = LayerInfo.objects.filter(uuid=uuid)
    if qs.exists():
        info = qs.first()
        if info.srid != 3857:
            env = Polygon.from_bbox(info.extent)
            env.srid = info.srid
            env.transform(3857)
            extent = env.extent
        else:
            extent = info.extent
        return Response({"payload": extent}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)


@decorators.api_view(["GET"])
def get_pixel_value(request, uuid, long, lat):
    info = LayerInfo.objects.filter(uuid=uuid).first()
    if info.data_model == 'R':
        if info.layer_access.accessibility_type == 'File':
            params = info.layer_access.params
            file_path = os.path.join(COG_DIR, params['file_path'])
            cog_raster = COGRaster.open_from_local(file_path)
            data = cog_raster.get_pixel_value_at_long_lat(long, lat)
            # print(data)
            return Response({"payload": data}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)


@decorators.api_view(["GET"])
def get_raster_area_from_polygon(request, uuid, geojson_str):
    info = LayerInfo.objects.filter(uuid=uuid).first()
    if info.data_model == 'R':
        if info.layer_access.accessibility_type == 'File':
            params = info.layer_access.params
            file_path = os.path.join(COG_DIR, params['file_path'])
            polygon_geojson = json.loads(geojson_str)
            # sample_geoms = [{'type': 'Polygon', 'coordinates': [
            #     [(250204.0, 141868.0), (250942.0, 141868.0), (250942.0, 141208.0), (250204.0, 141208.0),
            #      (250204.0, 141868.0)]]}]
            geoms = [polygon_geojson['features'][0]['geometry']]
            rio_raster = RioRaster(file_path)
            if rio_raster.get_crs() != 'EPSG:3857':
                rio_raster.reproject_raster('EPSG:3857')
            out_image, out_transform = mask(rio_raster.dataset, geoms, crop=True)
            pixel_size_x, pixel_size_y = rio_raster.get_spatial_resoultion()
            array = np.array(out_image)
            unique_pixels = np.unique(array)
            # unique_pixels = np.unique(array, count=True) # update accordingly count
            arr_pixels = []
            total_pixels = 0
            for p in unique_pixels:
                pixel_sum = np.sum(array == p)
                total_pixels = total_pixels + pixel_sum
                area = pixel_sum * pixel_size_x * pixel_size_y
                # area_class = 'class_' + str(p)
                pixel_count = {'pixel': p, 'count': pixel_sum, 'area': round(area, 2)}
                arr_pixels.append(pixel_count)
            total_area = round((total_pixels * pixel_size_x * pixel_size_y), 2)
            print(str(arr_pixels))
            return Response({"payload": arr_pixels}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)


@decorators.api_view(["GET"])
def get_feature_detail(request, uuid, col_name, col_val):
    info = LayerInfo.objects.filter(uuid=uuid).first()
    rs = info.get_row_detail(col_name, col_val)
    obj = {}
    for key in rs[0]:
        if key != 'geom':
            obj[key] = rs[0][key]
    # print(obj)
    if rs:
        return Response({"payload": obj}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)


class FloatUrlParameterConverter:
    regex = '[0-9]+\.?[0-9]+'

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return str(value)


@decorators.api_view(["GET"])
def create_cog_raster(request, raster_name):
    try:
        ori_raster_path = os.path.join(COG_DIR, f'{raster_name}.tif')
        rio = RioRaster(ori_raster_path)
        uuid = CommonUtils.get_uuid1()
        print("uuid", uuid)
        cog_path = os.path.join(COG_DIR, f'{uuid}.tif')
        cog_raster = COGRaster.create_cog(rio, cog_path)
        return HttpResponse("COG Created....")
    except Exception as e:
        return HttpResponse("Failed to create")


@decorators.api_view(["POST"])
def get_raster_value_from_geo_json(request):
    uuid = request.GET.get('uuid')
    data = request.data
    geojson = json.loads(data)
    info = LayerInfo.objects.filter(uuid=uuid).first()
    if info.data_model == 'R':
        if info.layer_access.accessibility_type == 'File':
            params = info.layer_access.params
            file_path = os.path.join(COG_DIR, params['file_path'])
            cog_raster = COGRaster.open_from_local(file_path)
            data = cog_raster.get_raster_value_from_geojson(geojson)
            # print(data)
            return Response({"payload": data}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_204_NO_CONTENT)
