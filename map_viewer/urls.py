from django.urls import path, register_converter
from .views import *

register_converter(FloatUrlParameterConverter, 'float')
urlpatterns = [
    # z=6, x= 44, y=37
    path('create_cog/<str:raster_name>', create_cog_raster, name='create_cog'),
    path('layer_mvt/<str:uuid>/<int:z>/<int:x>/<int:y>/', MVTView.as_view(), name='layer_mvt'),
    path('raster_tile/<str:uuid>/<int:z>/<int:x>/<int:y>/', TileView.as_view(), name='layer_tile'),
    path('layer_extent/<str:uuid>/', get_layer_extent, name='get_layer_extet'),
    path('layer_attributes/<str:uuid>/', get_layer_attributes, name='get_layer_attributes'),
    path('get_pixel_value/<str:uuid>/<float:long>/<float:lat>/', get_pixel_value, name='get_pixel_value'),
    path('get_feature_detail/<str:uuid>/<str:col_name>/<str:col_val>/', get_feature_detail, name='get_feature_detail'),
    path('get_raster_area/<str:uuid>/<str:geojson_str>/', get_raster_area_from_polygon, name='get_raster_area'),
    path('get_raster_value_from_geo_json/', get_raster_value_from_geo_json, name='get_raster_value_from_geo_json'),

]
