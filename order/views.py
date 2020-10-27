import datetime
import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from tools.logging_dec import logging_check
from  user.models import Address
from carts.views import CartView
from django.conf import settings
from .models import OrderInfo,OrderGoods
from goods.models import SKU
# Create your views here.

class OrderInfoView(View):
    @logging_check
    def post(self,request,username):
        #生成用户订单
        user =request.myuser
        address_id =json.loads(request.body).get('address_id') #取地址
        try:
            address =Address.objects.get(id =address_id,is_active=True)
        except Exception as e:
            return JsonResponse({'code':10500,'errmsg':'address error'})
        #开启事物  乐观锁（MySQL 事务主要用于处理操作量大，复杂度高的数据。）
        with transaction.atomic():  #所有的sql将会包裹在一个事物里
            sid = transaction.savepoint()  #存档点
            #时间戳  + 用户主键 （相对唯一性）
            now =datetime.datetime.now()
            order_id ="%s%02d" %(now.strftime('%Y%m%d%H%M%S'),user.id)    #"%s%02d":不足两位左边补零
            order =OrderInfo.objects.create(
                order_id =order_id,
                user_profile=user,
                address =address.address,
                receiver =address.receiver,
                receiver_mobile =address.receiver_mobile,
                tag =address.tag,
                total_amount=0,
                total_count=0,
                freight=0,
                pay_method=1,
                status=1,

            )
            #取出购物车数据
            carts_obj =CartView()
            all_carts =carts_obj.get_carts_all_data(user.id)
            #过滤出选中的商品
            carts_data ={k:v for k,v in all_carts.items() if v[1]==1}
            skus = SKU.objects.filter(id__in =carts_data.keys())
            total_count =0
            total_amount =0
            for sku in skus:
                carts_count =int(carts_data[sku.id][0])
                if sku.stock <carts_count:
                    #库存不够
                   #回滚  到最初始的位置
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code':10501,'errmsg':'stock error %s'%(sku.id)})

                #修改库存&乐观锁
                old_version =sku.version
                result =SKU.objects.filter(id =sku.id,version =old_version).update(stock =sku.stock - carts_count,sales =sku.sales + carts_count, version =old_version+1)
                if result ==0:
                    #证明当前数据有变化
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'code':10502,'errmsg':'库存有变化，请稍后再试'})
                #创建订单商品数据
                OrderGoods.objects.create(
                    order_id =order_id,
                    sku_id=sku.id,
                    count =carts_count,
                    price =sku.price
                )
                #计算总数量和总金额
                total_amount +=sku.price*carts_count
                total_count +=carts_count
                #更新订单数据
            order.total_count =total_count
            order.total_amount =total_amount
            order.save()

            #提交事务
            transaction.savepoint_commit(sid)

        #删除购物车中  勾选状态的商品

        data ={
            'saler':'dashop11',
            'total_amount':order.total_amount + order.freight,
            'order_id':order_id,
            'pay_url':''
        }
        return JsonResponse({'code':200,'data':data})


class AdvanceView(View):

    def get_address(self,user_id):
        #获取用户的地址
        all_address =Address.objects.filter(user_profile_id =user_id,is_active =True)
        if not all_address:
            #没有地址循环为空
            return []
        #默认地址要显现在所有地址最前面
        address_default =[]#默认地址
        address_normal =[]
        for addr in all_address:
            addr_dict ={
                "id":addr.id,
                'name':addr.receiver,
                'mobile':addr.receiver_mobole,
                'title':addr.tag,  #标签
                'address':addr.address  #详细地址
            }
            if addr.is_default:
                address_default.append(addr_dict)
            else:
                address_normal.append(addr_dict)
        return address_default+address_normal  #默认地址会在前面

    @logging_check
    #http://127.0.0.1:8000/v1/orders/weimin576/advance?settlement_type=0
    def get(self,request,username):
        user =request.myuser   #登录状态下可以直接取出用户名
        settlement =int(request.GET['settlement_type'])  #取查询字符串
        if settlement ==0:
            #购物车  点的 确认订单
            #获取地址(从购物车或者商品详情页都需要地址）
            address_list =self.get_address(user.id)
            #获取购物车中 勾选上的物品信息
            carts_obj =CartView()
            skus_list =carts_obj.get_carts_lists(user.id)
            selected_carts =[s for s in skus_list if s['selected']==1] #购物车里选中的状态

            #点了商品详情页中的理解购买确认订单
            data ={}
            data['addresses'] = address_list
            data['sku_list'] =selected_carts
            return JsonResponse({'code':200,'data':data,'base_url':settings.PIC_URL})
        else:
            pass