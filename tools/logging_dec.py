"""装饰器"""
import jwt
from django.http import JsonResponse
from django.conf import settings
from user.models import UserProfile


def logging_check(func):
    def wrapper(self, request, *args, **kwargs):
        """校验请求头带过来的token"""
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            result = {'code': 403, 'error': "Please login～"}
            return JsonResponse(result)
        try:
            res = jwt.decode(token, settings.SHOP_TOKEN_KEY, algorithms='HS256')
        except Exception as e:
            print('jwt error %s' % (e))
            result = {'code': 403, 'error': 'Please login'}
            return JsonResponse(result)

        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.myuser = user

        return func(self, request, *args, **kwargs)

    return wrapper
