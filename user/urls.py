from django.urls import path
from . import views

urlpatterns =[
    #http://127.0.0.0.1:8000/v1/users  :注册
    path("",views.users),
    #http://127.0.0.0.1:8000/v1/users/activation?code=XXXX
    path("/activation",views.user_active),
    #htpp ://127.0.0.1:8000/v1/user/<username>/address
    path("/<str:username>/address",views.AddressView.as_view()),

    #微博相关  http://127.0.0.1:8000/v1/users/weibo/authorization
    path("/weibo/authorization",views.oauth_url),
    #http://127.0.0.1:8000/v1/users/weibo/users?code =xxxx
    path("/weibo/users",views.oauth_token)

]