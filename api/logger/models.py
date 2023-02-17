import enum
from django.db import models

from django.apps import apps
from django.db.models import JSONField

from api.logger.middleware.RequestInfo import get_current_user, get_current_user_id
from django.contrib.auth import get_user_model

from api.model_fields import UserForeignKey

User = get_user_model()


class LogType(enum.Enum):
    Err = 'Error'
    Info = 'Info'
    Warn = 'Warning'

    @classmethod
    def choices(cls):
        return [(key.name, key.value) for key in cls]


app_labels_choices = [(app.verbose_name, app.verbose_name,) for app in apps.get_app_configs()]


class ActivityLog(models.Model):
    # user = models.ForeignKey(User, default=get_current_user(), on_delete=models.CASCADE, null=True, blank=True)
    user = UserForeignKey(null=True,blank=True)
    remote_address = models.CharField(max_length=100)
    server_hostname = models.CharField(max_length=100)
    request_method = models.CharField(max_length=10)
    request_path = models.CharField(max_length=100)
    request_params = JSONField(null=True, blank=True)
    run_time = models.PositiveIntegerField()
    log_type = models.CharField(max_length=10, choices=LogType.choices())
    request_body = models.CharField(max_length=200, null=True, blank=True)
    message = models.CharField(max_length=200, null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)

    def log_message(self, log_data, log_type=LogType.Info):
        # if 'activitylog' not in log_data['request_path']:
        self.__dict__.update(log_data)
        # user = get_current_user()
        # self.user = user.id if user else -1
        self.log_type = log_type.name
        self.user = get_current_user_id()
        self.save()
