from django.db import models

# Create your models here.
# from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import JSONField

from api.enums import SocialAppProviders
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountInfo(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.PositiveIntegerField()
    provider = models.CharField(
        verbose_name="provider",
        max_length=30,
        choices=SocialAppProviders.choices(),
    )
    uid = models.CharField(max_length=200)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    extra_data = JSONField(verbose_name="extra data", default=dict)

    class Meta:
        unique_together = "provider", "uid"
        verbose_name = "social account"
        verbose_name_plural = "social api"

    def __str__(self):
        user = User.objects.get(id=self.user)
        return '%s: %s' % (self.provider, user.username)

    def get_user(self):
        return User.objects.get(id=self.user)

    def set_user(self, user):
        self.user = user.id


class SocialApp(models.Model):
    # name = models.CharField(max_l?ength=100)
    provider = models.CharField(
        verbose_name="provider",
        max_length=30,
        choices=SocialAppProviders.choices(),
    )
    name = models.CharField(verbose_name="name", max_length=40)
    client_id = models.CharField(
        verbose_name="client id",
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        verbose_name="secret key",
        max_length=200,
        blank=True,
        help_text="API secret, client secret, or" " consumer secret",
    )
    key = models.CharField(
        verbose_name="key", max_length=191, blank=True, help_text="Key"
    )
    # Most apps can be used across multiple domains, therefore we use
    # a ManyToManyField. Note that Facebook requires an app per domain
    # (unless the domains share a base base name).
    # blank=True allows for disabling apps without removing them
    sites = models.PositiveIntegerField(Site, blank=True)

    # We want to move away from storing secrets in the database. So, we're
    # putting a halt towards adding more fields for additional secrets, such as
    # the certificate some providers need. Therefore, the certificate is not a
    # DB backed field and can only be set using the ``APP`` configuration key
    # in the provider settings.
    certificate_key = None

    class Meta:
        verbose_name = "social application"
        verbose_name_plural = "social applications"

    def __str__(self):
        return self.name


class SocialToken(models.Model):
    app = models.ForeignKey(SocialApp, on_delete=models.CASCADE)
    account = models.ForeignKey(AccountInfo, on_delete=models.CASCADE)
    access_token = models.TextField(
        verbose_name="token",
        help_text='"oauth_token" (OAuth1) or access token (OAuth2)',
    )
    refresh_token = models.TextField(
        blank=True,
        verbose_name="token secret",
        help_text='"oauth_token_secret" (OAuth1) or refresh token (OAuth2)',
    )
    expires_at = models.DateTimeField(
        blank=True, null=True, verbose_name="expires at"
    )

    class Meta:
        unique_together = ("app", "account")
        verbose_name = "social application token"
        verbose_name_plural = "social application tokens"
