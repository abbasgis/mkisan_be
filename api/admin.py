from django.contrib import admin

# Register your models here.
from api.utils import ModelUtils
from api.models import *


class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(AccountInfo)


admin.site.register(AccountInfo, AccountInfoAdmin)


class SocialAppAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'provider']  # ModelUtils.get_list_display(SocialApp,skip_fields=['sites'])
    pass


admin.site.register(SocialApp, SocialAppAdmin)


class SocialTokenAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(SocialToken)


admin.site.register(SocialToken, SocialTokenAdmin)
