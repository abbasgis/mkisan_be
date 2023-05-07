from django.contrib import admin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import path

from api.utils import ModelUtils
from .models import *



class LayerCategoryAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(LayerCategory)
    search_fields = ['name']


admin.site.register(LayerCategory, admin_class=LayerCategoryAdmin)


class LayerQualityLevelAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(LayerQualityLevel)


admin.site.register(LayerQualityLevel, admin_class=LayerQualityLevelAdmin)


@admin.register(LayerAccessibility)
class LayerAccessibilityAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(LayerAccessibility)


@admin.register(DBConnection)
class DBConnectionAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(DBConnection)


@admin.register(LayerInfo)
class LayerInfoAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(LayerInfo, skip_fields=['dataset_info', 'extent',
                                                                          'extent_3857', 'proj4', 'abs_path'])
    search_fields = ['layer_name', 'table_name']
    list_filter = ['data_model', 'raster_type', 'vector_type', 'srid']
    actions = ['download_data']
    change_list_template = 'admin/dch_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add_layer_info/', self.addLayerInfo, name='add_layer_info'),
        ]
        return my_urls + urls

    # def delete_queryset(self, request, queryset):
        # obj: LayerInfo
        # for obj in queryset:
        #     if obj.data_model == 'raster':


        # return super(LayerInfoAdmin, self).delete_queryset(request,queryset)

    def addLayerInfo(self, request):
        # self.model.objects.all().update(is_immortal=True)
        if request.method == "GET":
            return render(request, 'admin/add_layer_info.html',
                          context={'title': 'Add Layer Info', 'subtitle': 'Add Layer Info'})
        else:
            self.message_user(request, "layer Info Added")
            return HttpResponseRedirect("../")

    # def set_3857_geom_field(self, request, queryset):
    #     for info in queryset:
    #         LayerUtils.add_3857_geometry_column(info)


@admin.register(MapInfo)
class MapInfoAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(MapInfo)
    search_fields = ['title']
