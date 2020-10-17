import hashlib
import json
from urllib.parse import urlencode
import requests
from django.http import JsonResponse
from django.shortcuts import render
from .models import UserProfile, Address,WeiboProfile
from django.conf import settings
import json
from dtoken.views import make_token
import random
import base64
from django.core.cache import cache, caches
from django.core.mail import send_mail
from .tasks import send_active_email_celery
from django.views import View
from tools.logging_dec import logging_check



EMAIL_CACHE = caches['user_email']


# 10100 - 10199  状态码

# Create your views here.
def users(request):
    if request.method == 'POST':
        '注册用户'
        data = request.body  # 取出请求体里的所有数据，拿到json串
        json_obj = json.loads(data)  # 反序列化，变成python字典
        print(data)
        username = json_obj['uname']
        email = json_obj['email']
        password = json_obj['password']
        phone = json_obj['phone']
        if len(password) < 6:
            result = {'code': 10100, 'error': 'password is error!'}
            return JsonResponse(result)  # JsonResponse可以把传进来的参数序列化成一个字典，并且吧响应头里的content—type变成便准的application/json，

        """
        #用户名是否可用，已注册的话给个错误返回
        #创建用户 密码用md5
        #用jwt 签发token  有效期1天，token 里面存放e:xxx
        #查看用户名是否注册过，filter返回queryset结构，
        """
        old_user = UserProfile.objects.filter(username=username)
        if old_user:
            result = {'code': 10101, 'error': 'The username is already exist～'}
            return JsonResponse(result)
        # 创建用户 密码用md5
        p_m = hashlib.md5()
        p_m.update(password.encode())  # update传进去需要一个字节串，password是字符串，需要encode
        password = p_m.hexdigest()
        # 创建用户需要try下
        try:
            # 创建用户
            user = UserProfile.objects.create(username=username, password=password, email=email, phone=phone)
        except Exception as e:
            print('create error is %s' % (e))
            result = {'code': 10102, 'error': 'The username is Already exist～'}
            return JsonResponse(result)
        token = make_token(username)

        """
        #生成四位随机数   
        #拿用户名 + 随机数 拼接成一个新的字符串
        #b64(新字符串）
        #存储随机数
        #生成激活链接   “http://127.0.0.1:7000/dadashop/templates/active.html?code =%s'
        #将链接发送至用户邮箱
        """
        code = "%s" % (random.randint(1000, 9999))
        code_str = code + "_" + username
        code_bs = base64.urlsafe_b64encode(code_str.encode())  # 字节串
        # 存储随机数
        EMAIL_CACHE.set('email_active_%s' % (username), code, 3600 * 24 * 3)
        # 激活链接
        verify_url = "http://127.0.0.1:7000/dadashop/templates/active.html?code =%s" % (code_bs.decode())
        # 将链接发送至用户邮箱
        # send_active_email(email,verify_url)
        send_active_email_celery.delay(email, verify_url)  # 用新写的方法代替容易阻塞的方法去执行
        # 此阶段通讯了QQ,响应
        return JsonResponse({'code': 200, 'username': username, 'data': {'token': token.decode()}, 'carts_count': 0})
    # token.decode：转成字符串


def send_active_email(email_address, verify_url):
    subject = 'dashop11激活邮件'
    html_message = '''
    <P>  尊敬的用户 您好</p>
    <p> 您的激活链接为<a href="%s" target ="_blank">点击激活链接</a></p>
    ''' % (verify_url)
    send_mail(subject, "", settings.EMAIL_HOST_USER, [email_address],
              html_message=html_message)  # 引入from django.core.mail import send_mail


def user_active(request):
    # 激活用户   # 只接get请求
    if request.method != 'GET':
        result = {'code': 10103, 'error': 'Please use GET'}
        return JsonResponse(result)
    # c =request.get_full_path()
    # print("-" * 40)
    # print(c)   #/v1/users/activation?code%20=NzU1MV93ZWltaW41NzY=
    code = request.GET.get('code%20')  # 取查询字符串
    print("-" * 40)
    print(code)
    if not code:
        return JsonResponse({'code': 10104, 'error': 'please give me code!!!'})
    code_str = base64.urlsafe_b64decode(code.encode()).decode()
    # code_str:'code_username
    random_code, username = code_str.split("_")
    # 取出原先存储好的code
    old_code = EMAIL_CACHE.get("email_active_%s" % (username))
    if not old_code:
        return JsonResponse({'code': 10105, 'error': 'Link is wrong'})
    # 比对
    if random_code != old_code:
        return JsonResponse({'code': 10106, 'error': 'Link is wrong!'})

    # orm 更新 一查二改三保存
    try:
        user = UserProfile.objects.get(username=username)  # get 查不到或查多了都会报错，用try
    except Exception as e:
        return JsonResponse({'code': 10107, 'error': "User get error"})
    user.is_active = True
    user.save()

    # 删除缓存
    EMAIL_CACHE.delete('email_active_%s' % (username))
    return JsonResponse({'code': 200, 'data': 'ok'})


class AddressView(View):
    @logging_check
    def dispatch(self, request, *args, **kwargs):
        # 405响应  如果视图类没定义该http 请求动作的方法，则报405错误
        """ dispatch:分开
        #所有请求的入口，集中做些请求的过滤   """
        json_str = request.body
        request.json_obj = {}
        if json_str:
            json_obj = json.loads(json_str)
            request.json_obj = json_obj  # 给request.对象绑定一个属性，
            # request会传到return super().dispatch(request,*args,**kwargs)后面的视图函数可以直接调用
        return super().dispatch(request, *args, **kwargs)

    # 把请求根据具体的动作分发给具体的方法
    def get(self, request,username):
        #user = request.myuser
        #all_addr = user.address_set.filter(is_active=True)  # 反向查询
        all_addr = Address.objects.filter(user_profile=request.myuser, is_active=True)
        res = []
        for addr in all_addr:
            addr_data = {}
            addr_data['id'] = addr.id
            addr_data['address'] = addr.address
            addr_data['receiver'] = addr.receiver
            addr_data['tag'] = addr.tag
            addr_data['receiver_mobile'] = addr.receiver_mobile
            addr_data['is_default'] = addr.is_default
            res.append(addr_data)
        return JsonResponse({'code': 200, 'addresslist': res})

    def post(self, request, username):
        # 前段提交的数据插入表里
        # 默认地址原则，第一个创建出来的地址 为 默认地址
        # 登录的用户不能改其他人的地址【url里传过来的，aiax 传过来的地址里的username不可信,取token里的用户是正确的，url 里的用户与token里的用户相比较】
        print(request.myuser)
        data = request.json_obj
        address = data['address']
        postcode = data['postcode']
        receiver = data['receiver']
        receiver_mobile = data['receiver_phone']
        tag = data['tag']
        #
        # users = UserProfile.objects.filter(username=username)  # filter查找出来的只有一个
        # # <QuerySet [<UserProfile: 9_False>]>
        # if not users:
        #     return JsonResponse({'code': 10107, 'error': 'username is error'})
        # user = users[0]
        # 取出user里的username
        # 判断一下 默认地址问题
        # if request.myuser.username !=username
        #   pass   request.user =user
        user = request.myuser
        # user.address_ser.all()
        old_addr = Address.objects.filter(user_profile=user)
        default_status = False
        # is_defalut = models.BooleanField(verbose_name='是否为默认地址', default=False)
        if not old_addr:
            default_status = True
        Address.objects.create( user_profile=user, receiver=receiver, postcode=postcode,receiver_mobile=receiver_mobile,tag=tag, is_defalut=default_status, address=address)
        return JsonResponse({'code': 200, 'data': 'ok'})


    def put(self,request):
        pass

    def delete(self,request):
        pass


def oauth_url(request):
    #获取微博授权地址，返回url  http://127.0.0.1:8000/v1/users/weibo/authorization
    params ={
        'response_type':'code',
        'client_id':settings.WEIBO_CLIENT_ID,
        'redirect_uri':settings.WEIBO_REDIRECT_URI                  #用户授权完后，跳转地址
    }

    weibo_url ='https://api.weibo.com/oauth2/authorize?'
    #拼出微博授权地址
    url =weibo_url+urlencode(params)
    return JsonResponse({'code':200,'oauth_url':url})

def oauth_token(request):
    ##http://127.0.0.1:8000/v1/users/weibo/users?code =xxxx
    if request.method =='GET': #拿授权码
        code =request.GET.get('code')
        #给微博服务器请求 用 授权码 交换用户token
        token_url ='https://api.weibo.com/oauth2/access_token'
        req_data ={
            'client_id': settings.WEIBO_CLIENT_ID,
            'client_secret':settings.WEIBO_CLIENT_SECRET,
            'grant_type':'authrization_code' ,   #当前为授权码模式
            'code':code,
            'redirect_uri':settings.WEIBO_REDIRECT_URI
        }

        #前端拿到code,立刻给后端发一个get 请求，将code加载查询字符串发给后端，后端取出ｃｏｄｅ向微博服务器（携带附属信息）　发请求，换去token，同时关注状态码状态
        #sudo pip3 install requests  requests: 专门发http请求
        response =requests.post(token_url,data=req_data)

        if response.status_code == 200:
            res_data =json.loads(response.text)  #response.text：此次响应体的内容
        else:
            print('change code error %s'%(response.status_code))
            return JsonResponse({'code':10108,'error':'weibo error～'})

        if res_data.get('error'):
            print(res_data.get('error'))
            return JsonResponse({'code':10109,'error':'weibo error!'})
        print("----weibo token id ---")
        print(res_data)
        #token取到后，需要入库，微博账号还需和电商用户绑定，用户需要在电商页面注册，同时与微博账号绑定，“绑定关联’,待下次微博登录，可以直接获取之前绑定电商账号的信息，正常走内部登录流程，发自己电商的token .

        weibo_uid =res_data['uid']
        access_token =res_data['access_token']
        #先检查 该微博用户是否第一次进入我们的网站

        try:
            weibo_user =WeiboProfile.objects.get(wuid = weibo_uid)
        except Exception as e:
            #报错证明该用户第一次来，走插入数据流程
            WeiboProfile.objects.create(access_token=access_token,wuid=weibo_uid)
            # 如果是第一次来，赶紧存下来，外键可以暂时为空
            return JsonResponse({'code':201,'uid':weibo_uid})#让前端知道是哪个用户需要注册
          #如果get 没有报错，走到else,
        else:
            #微博账号来过：
            user =weibo_user.user_profile  #取外键
            if user:
            #1.执行过完成流程，完成了绑定注册
                pass
            else:
            #2.来过但没绑定注册。
                return JsonResponse({'code': 201, 'uid': weibo_uid})  # 让前端知道是哪个用户需要注册
    elif request.method == 'POST':
        #绑定注册
        data =json.loads(request.body)
        uid =data['uid']
        username =data['username']
        password =data['password']
        phone =data['phone']
        email =data['email']

        #TODO 检查用户名是否存在
        m =hashlib.md5()
        m.update(password.encode())
        #创建内部用户& 绑定微博用户

        return JsonResponse({'code':200})

