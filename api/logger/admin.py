from django.contrib import admin

# Register your models here.
from api.logger.models import ActivityLog
from api.utils import ModelUtils


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ModelUtils.get_field_name_list(ActivityLog)
    search_fields = ['request_path', 'message']
    list_filter = ['log_type']
