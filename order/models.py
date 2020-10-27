from django.db import models
from tools.models import BaseModel
from user.models import UserProfile
from goods.models import SKU
# Create your models here.

STATUS_CHOICES =(
    (1,'待付款'),
    (2,'待发货'),
    (3,'待收货'),
    (4,'订单完成')
)
class OrderInfo(BaseModel):  #订单表
    #与用户表一对多的关系
    order_id =models.CharField(max_length=64,primary_key=True,verbose_name='订单号',default='')
    user_profile =models.ForeignKey(UserProfile,on_delete=models.CASCADE)#外键
    total_count =models.IntegerField(verbose_name='商品总数')
    total_amount =models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品总金额')
    freight =models.DecimalField(max_digits=10,decimal_places=2,verbose_name='运费')
    pay_method = models.SmallIntegerField(default=1,verbose_name='支付方式')

    #订单地址
    receiver =models.CharField(verbose_name='收件人',max_length=11)
    address =models.CharField(max_length=100,verbose_name='收货地址')
    receiver_mobile =models.CharField(max_length=11,verbose_name='收件人电话')
    tag =models.CharField(verbose_name='标签',max_length=10)
    status =models.SmallIntegerField(verbose_name='订单状态',choices=STATUS_CHOICES)

    class Meta:
        db_table ='order_order_info'

#一个订单有多个商品
class OrderGoods(BaseModel):
    #与订单表一对多
    order =models.ForeignKey(OrderInfo,on_delete=models.CASCADE) #
    sku =models.ForeignKey(SKU,on_delete=models.CASCADE)
    count =models.IntegerField(default=1,verbose_name='数量')  #单个商品的数量
    price =models.DecimalField(max_digits=10,decimal_places=2,verbose_name='单价')#订单里商品价格
    
    class Meta:
        db_table ='order_order_goods'
    def __str__(self):
        return self.sku.name