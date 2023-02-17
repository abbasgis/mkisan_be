import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.

from django.contrib.auth import get_user_model, authenticate, login
from rest_framework import response, decorators, permissions, status
from rest_framework_simplejwt.tokens import RefreshToken

from .logger.utils import DataLogger
from .models import AccountInfo, SocialToken, SocialApp
from .serializers import UserCreateSerializer

User = get_user_model()


@login_required(login_url='/admin/login/')
def redirect_main(request):
    response = redirect('/api/doc/')
    return response


@decorators.api_view(["GET"])
def auth_delete(request, username: str):
    if request.user.is_superuser:
        u = User.objects.get(username=username)
        u.delete()
        return response.Response({"msg", "successfully deleted"}, status.HTTP_200_OK)
    return response.Response({"msg", "Failed"}, status=status.HTTP_400_BAD_REQUEST)


@decorators.api_view(["POST"])
def auth_change_password(request):
    data = request.data
    u = User.objects.get(username=data['username'])
    u.set_password(data['password'])
    u.save()
    return response.Response({"msg": "success"}, status.HTTP_200_OK)


# class UserData(BaseModel):

# @decorators.permission_classes([permissions.AllowAny])
@decorators.api_view(["POST"])
def auth_registration(request):
    if request.user.is_superuser or (request.user.is_staff and 'sop_admin' in request.user.groups):
        groups = request.data['groups'] if 'groups' in request.data.keys() else None
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        for group_name in groups:
            print(group_name)
            g = Group.objects.filter(name=group_name).first()
            g.user_set.add(user)
            g.save()
        refresh = RefreshToken.for_user(user)
        res = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return response.Response(res, status.HTTP_201_CREATED)


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny, ])
def user_login(request):
    try:
        # serializer = UserCreateSerializer(data=request.data)
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if not user:
            return response.Response({"msg", "Failed to login user"}, status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        res = {
            "refreshToken": str(refresh),
            "accessToken": str(refresh.access_token),
            "userInfo": {'name': user.username,
                         # "username": user.username,
                         "email": user.email,
                         "isSuperuser": user.is_superuser,
                         "isStaff": user.is_staff,
                         "groups": list(request.user.groups.values_list('name', flat=True))}
        }
        # return response.Response(data=res, status=status.HTTP_200_OK)
        return JsonResponse(res, status=status.HTTP_200_OK)

    except Exception as e:
        DataLogger.log_error_message(e)
        return JsonResponse({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny, ])
def oauth_login(request, *args, **kwargs):
    try:
        data = json.loads(request.body.decode('utf-8'))
        type = kwargs['type']
        # token = data['tokenId']
        # accessToken = data['accessToken']
        uid = data['profileObj']['googleId']
        email = data['profileObj']['email']
        user = User.objects.filter(email=email).first()
        if not user:
            user = User()
            user.email = email
            user.username = email
            user.save()

        sa = AccountInfo.objects.filter(uid=uid).first()
        if not sa:
            sa = AccountInfo()
            sa.uid = uid
            sa.user = user.id
            sa.provider = type
            sa.extra_data = data  # ['user']
            sa.save()
        else:
            sa.extra_data = data
            sa.save()
        # user.backend = 'django.contrib.auth.backends.ModelBackend'
        # login(request, user)
        refresh = RefreshToken.for_user(user)
        app_obj = SocialApp.objects.filter(provider=type).first()
        token_obj = SocialToken.objects.filter(account=sa, app=app_obj).first()

        if not token_obj:
            token_obj = SocialToken()
            token_obj.account = sa
            token_obj.app = app_obj
        token_obj.refresh_token = str(refresh)
        token_obj.access_token = str(refresh.access_token)
        # token_obj.expires_at = datetime.fromtimestamp(data['tokenObj']['expires_at'] / 1e3)
        token_obj.save()
        login(request, user)
        # google profileObj
        name = data['profileObj']['name']
        photo_url = data['profileObj']['imageUrl']
        email = data['profileObj']['email']

        refresh = RefreshToken.for_user(user)
        res = {
            "refreshToken": str(refresh),
            "accessToken": str(refresh.access_token),
            "userInfo": {'name': name,
                         # "username": user.username,
                         "email": email,
                         "photo": photo_url,
                         "groups": list(request.user.groups.values_list('name', flat=True))}
        }
        # return response.Response(data=res, status=status.HTTP_200_OK)
        return JsonResponse(res, status=status.HTTP_200_OK)
    except Exception as e:
        DataLogger.log_error_message(e)
        return JsonResponse({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)
