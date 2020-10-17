"""ddshop11 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from . import views
from  django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('test',views.test_cors),
    #http://127.0.0.1/v1/users
    path('v1/users',include('user.urls')),
    path('v1/tokens',include('dtoken.urls')),
    path('v1/goods',include('goods.urls')),
    path('v1/carts',include('carts.urls'))
]
#设置static方法，绑定MEDIA_URL和MEDIA_ROOT,实现了127.0.0.1:8000/media/a.jpg请求到达djaogo后,django 去MEDIA_ROOT下寻找相应资源问价；当前方法只在debug=True生效
#static会解析document_root里的文件
urlpatterns +=static(settings.MEDIA_URL,document_root =settings.MEDIA_ROOT)