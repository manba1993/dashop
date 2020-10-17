from django.db import models

class BaseModel(models.Model):
    #此类可为其他模型类补充字段  --抽象类
    """
    auto_now: 每次保存对象时，自动设置该字段为当前时间(取值:True/False)。
    auto_now_add: 当对象第一次被创建时自动设置当前时间(取值:True/False)。
    default: 设置当前时间(取值:字符串格式时间如: '2019-6-1')。
    """
    created_time =models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
    updated_time =models.DateTimeField(auto_now=True,verbose_name='更新时间')

    class Meta:
        abstract=True