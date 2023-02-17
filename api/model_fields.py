from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords

from api.logger.middleware.RequestInfo import get_current_user_id
from api.models import User


class UserForeignKey(models.PositiveBigIntegerField):
    def __init__(self, *args, **kwargs):
        # kwargs['min_value'] = 0
        kwargs['blank'] = True
        kwargs['null'] = True
        super().__init__(*args, **kwargs)
        # self.models = get_user_model()

    def formfield(self, **kwargs):
        return forms.ModelChoiceField(
            queryset=get_user_model().objects.all(),
            blank=self.blank
        )

    def get_prep_value(self, value: User):
        if value:
            if isinstance(value, int):
                return value
            elif isinstance(value, User):
                return value.pk
            elif isinstance(value, str):
                user = User.objects.filter(username=value).first()
                if user:
                    return user.pk
            else:
                raise ValidationError("Invalid input for a User instance")

    @staticmethod
    def from_db_value(value, expression, connection):
        if isinstance(value, int):
            user = get_user_model().objects.filter(pk=value).first()
            value = user.username
        elif isinstance(value,User):
            value = value.username
        return value if value else None

    def to_python(self, value: int):
        try:
            # return User.objects.get(pk=value)
            return value.pk
        except User.DoesNotExist:
            return None


class GroupForeignKey(models.PositiveBigIntegerField):
    def __init__(self, *args, **kwargs):
        # kwargs['max_length'] = 104
        kwargs['blank'] = True
        kwargs['null'] = True
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Group):
        if value:
            if not isinstance(value, Group):
                return None
                # raise ValidationError("Invalid input for a Group instance")
            return value.pk

    def to_python(self, value: int):
        try:
            return Group.objects.get(pk=value)
        except User.DoesNotExist:
            return None


class DAHistoricalRecords(HistoricalRecords):
    def __init__(self):
        super().__init__(history_user_id_field=models.PositiveIntegerField(null=True))

    def _history_user_getter(self):
        if self.history_user_id is None:
            return None
        User = get_user_model()
        try:
            return User.objects.get(pk=self.history_user_id)
        except User.DoesNotExist:
            return None

    def _history_user_setter(self, user):
        if user is not None:
            self.history_user_id = get_current_user_id() or user.pk
