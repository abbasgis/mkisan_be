from threading import local

from django.contrib.auth import get_user_model, login
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
_user = local()
_user.value = None

from django.contrib.auth.middleware import get_user
from django.utils.functional import SimpleLazyObject


# from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class CurrentUserMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        if 'Authorization' in request.headers and request.user.is_anonymous:
            authorization = request.headers.get('Authorization').split(' ')
            if len(authorization) > 1:
                access_token = authorization[1]
                _user.value = self.get_user_from_access_token(access_token)
                # login(request, user)

        return self.get_response(request)

    def get_user_from_access_token(self, access_token_str):
        access_token_obj = AccessToken(access_token_str)
        user_id = access_token_obj['user_id']
        user = User.objects.get(id=user_id)
        # authenticate(user)
        return user
        # print('user_id: ', user_id)
        # print('user: ', user)
        # print('user.id: ', user.id)
        # content = {'user_id': user_id, 'user': user, 'user.id': user.id}
        # return Response(content)

    def process_request(self, request):
        _user.value = request.user


def get_current_user():
    return _user.value  # if _user.value.id is not None else None


def get_current_user_id():
    return _user.value.id if _user.value else None
