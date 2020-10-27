import hashlib
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
import  jwt
import time
# Create your views here.
from user.models import UserProfile


def tokens(request):
    #登录
    if request.method != 'POST':
        result ={'code':10200,'error':'Please use POST'}
        return JsonResponse(result)
    json_str =request.body  #从请求体里取数据，
    json_obj =json.loads(json_str)#json_obj 转成python 字典
    print(json_obj)
    #{'username': 'weimin123', 'password': '123456', 'carts': None}
    password = json_obj['password']
    username =json_obj['username']
    #校验用户存不存在
    #取值
    users =UserProfile.objects.filter(username=username)  #把username在表里取下
    print(users)#<QuerySet [<UserProfile: 5_False>]>
    if not users:
        result ={'code':10201,'error':'username or password is wrong '}
        return JsonResponse(result)
    user =users[0]
    m =hashlib.md5()
    m.update(password.encode())
    if m.hexdigest()!=user.password:
        result ={'code':10202,'error':'username or password is wrong!!'}
        return JsonResponse(result)
    token =make_token(username)
    result ={'code':200,'username':username,'data':{'token':token.decode()},'carts_cout':0}
    return JsonResponse(result)
    #发门票
#发门票的事登录注册都需要用，可以分离开来
def make_token(username,expire =3600*24):
    key =settings.SHOP_TOKEN_KEY
    now =time.time()  #当前的时间戳
    payload ={'username':username,'exp':now+expire} #要传递的数据
    return jwt.encode(payload,key,algorithm='HS256') #JWT生成的token 是字节串格式