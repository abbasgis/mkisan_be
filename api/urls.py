from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
schema_view = get_schema_view(
    openapi.Info(
        title="Mera Kisan API",
        default_version='v1',
        # description="Test description",
        # terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="sabbasgis@gmail.com"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # path('swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('', include('rest_framework.urls')),
    path('jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # new
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/oauth/login/<str:type>/', oauth_login, name='oauth_login'),
    path('jwt/auth/login/', user_login, name='jwt_auth_login'),
    path('auth/add_user/', auth_registration, name='auth_register'),
    path('auth/delete_user/<str:username>/', auth_delete, name='auth_delete'),
    path('auth/change_password/', auth_change_password, name='auth_change_password')

]
