from celery import Celery
import os
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE','ddshop11.settings')


#参数中的名字　自定义
app=Celery('ddshop11')

app.conf.update(
    BROKER_URL ='redis://@127.0.0.1:6379/4'
)

#告诉celery 去哪找任务
app.autodiscover_tasks(settings.INSTALLED_APPS)  # settings.INSTALLED_APPS:去所有应用（app)下去查找带有特殊装饰器的函数