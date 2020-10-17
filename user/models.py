from django.db import models


# Create your models here.
class UserProfile(models.Model):
    username = models.CharField(max_length=11, verbose_name='用户名', unique=True)  # unique=True : 唯一约束
    password = models.CharField(max_length=32)
    email = models.EmailField(verbose_name='邮箱')
    phone = models.CharField(max_length=11, verbose_name='手机号')
    is_active = models.BooleanField(default=False, verbose_name='激活状态')
    crated_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        "更改表名"
        db_table = 'user_user_profile'

    def __str__(self):
        return "%s_%s" % (self.id, self.is_active)  # 看到相关信息


# 一个用户多个地址；

class Address(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # 外键  一对多
    receiver = models.CharField(verbose_name='收件人', max_length=11)
    address = models.CharField(verbose_name='收货地址', max_length=100)
    postcode = models.CharField(verbose_name='邮编', max_length=6)
    receiver_mobile = models.CharField(verbose_name='联系人', max_length=11)
    tag = models.CharField(verbose_name='标签', max_length=10)
    is_defalut = models.BooleanField(verbose_name='是否为默认地址', default=False)
    is_active = models.BooleanField(verbose_name='是否删除', default=False)

    # mysql表名：应用名_类名  user_Address  - - > user_address
    def __str__(self):
        return "%s,%s,%s,%s" % (self.id, self.receiver, self.address, self.is_defalut)


class WeiboProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile,on_delete=models.CASCADE, null=True)  #可以为空
    wuid = models.CharField(max_length=10, verbose_name='微博uid', unique=True)  # 唯一
    access_token = models.CharField(verbose_name='微博授权令牌', max_length=32)

    class Meta:
        db_table = 'user_weibo_profile'


