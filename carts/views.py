from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import json
from django.conf import settings
from tools.logging_dec import logging_check
from goods.models import SKU
from django.core.cache import caches

CARTS_CACHE =caches['carts']  #调settings里新添加的caches配置

# Create your views here.
class CartView(View):
    @logging_check
    def dispatch(self, request, *args, **kwargs):
        # 分发方法
        # 所有对应该视图类的请求，优先走该方法
        # 集中检查  -  logging_check
        # 集中处理参数 - json_obj
        json_str =request.body
        request.json_obj ={}
        # 设置默认值，如果取到
        if json_str:
            json_obj =json.loads(json_str)
            request.json_obj =json_obj
            #调super触发dispatch  的父类
        return super().dispatch(request,*args,**kwargs)

    def get_sku_attr_name_and_values(self,sku):
        sku_sale_attr_name =[]
        sku_sale_attr_values =[]
        #正向查询，拿到销售值，orm
        sku_sale_values=sku.sale_attr_value.all()#取出sku关联的所有值
        for sale in sku_sale_values:
            sku_sale_attr_values.append(sale.name)
            sku_sale_attr_name.append(sale.spu_sale_attr.name)
        return sku_sale_attr_name,sku_sale_attr_values

    def get_cache_key(self,uid):
        #负责返回当前业务redis的key
        return 'carts_%s'%(uid)

    def get_carts_all_data(self,uid):
        #拿出用户所有的购物车数据
        #key  -> carts_%s(uid)
        #方案1：value  - >{skuid:{'count':1,'selected':1}}
        #方案2：value  - >{skuid:[count,selected]}
        key =self.get_cache_key(uid)  #缓存的key【carts_uid】
        value =CARTS_CACHE.get(key)    #CARTS_CACHE =caches['carts']
        if not value:
            return {}  #返回一个字典
        data ={int(k):v for k,v in value.items()}
        return data

    def set_carts_data(self,uid,sku_id,data):
        key =self.get_cache_key(uid)  #当前用户的key拿到
        all_data =self.get_carts_all_data(uid)  #取现在用户的购物车
        all_data[sku_id] =data  #如果为空，加data进去
        CARTS_CACHE.set(key,all_data)   #存储

    def post(self,request,username):
        #添加购物车
        #{“ sku_id”:xxxx, 'count':1}
        #取值sku_id,count
        sku_id =request.json_obj['sku_id']
        count =request.json_obj['count']
        user =request.myuser
        #取sku ，查sku_id 是否存在
        try:
            sku =SKU.objects.get(id = sku_id,is_launched=True)
        except Exception as e:
            print('sku get error %s'%(e))
            return JsonResponse({'code':'10400','error':'no sku'})
        count =int(count)
        #预判断库存是否充裕
        if count>sku.stock:   #添加的大于库存
            return JsonResponse({'code':10401,'error':'stock error'})

        #取用户购物车数据
        carts =self.get_carts_all_data(user.id)  #查看当前用户在redis有无数据
        if not carts:
            #用户第一次使用购物车功能数据
            #初始化商品状态
            info =[count,1]  #count： 数量  1： 选中状态
            #存储到购物车
            self.set_carts_data(user.id,int(sku_id),info)
            return JsonResponse({'code':200,'data':{'carts_count':1},'base_url':settings.PIC_URL})
        else:
            my_info =carts.get(int(sku_id))  #查看是否有值，有值代表之前加过购物车数据，
            if not my_info:#如果没有值，初始化商品数据
                new_info =[count,1]
            else:
                #代表购物车之前有数据
                old_count =my_info[0] #取出之前添加的购物车数量
                new_count =old_count +count  #加上这次添加的数量
                if new_count > sku.stock:#和当前的库存进行比对
                    return JsonResponse({'code':10401,'error':'stock error'})
                old_select =my_info[0]#取出原来选中的状态
                new_info =[new_count,old_select]  #拼出最新的情况
            self.set_carts_data(user.id,int(sku_id),new_info)  #将数据存到redis
            carts_data =self.get_carts_all_data(user.id)  #取
            return JsonResponse({'code':200,'data':{'carts_count':len(carts_data)},'base_url':settings.PIC_URL}) #len(carts_data)：购物车有几种数据

    def get(self,request,username):
        #取购物车
        user =request.myuser
        carts_data =self.get_carts_all_data(user.id)

        if  not carts_data:
            return JsonResponse({'code':200,'data':[],'base_url':settings.PIC_URL})
        #进行orm查询，把购物车对应的数据取出来
        skus =SKU.objects.filter(id_in =carts_data.keys())#queryset
        skus_list =[]  #循环
        for sku in skus:
            sku_dict ={}
            sku_dict['id'] =sku.id
            sku_dict['name'] =sku.name
            sku_dict['price']=str(sku.price)
            sku_dict['default_image_url'] =str(sku.default_image_url)
            sku_dict['count'] =int(carts_data[sku.id][0])
            sku_dict['selected'] =int(carts_data[sku.id][1])
            #拿到当前sku销售的属性值和销售属性值对应的属性名
            #sku_sale_attr_name =['尺寸','颜色']
            #sku_sale_attr_val =['18寸','蓝色']
            sku_sale_attr_name,sku_sale_attr_val =self.get_sku_attr_name_and_values(sku)
            sku_dict['sku_sale_attr_name'] =sku_sale_attr_name
            sku_dict['sku_sale_attr_val'] =sku_sale_attr_val
            skus_list.append(sku_dict)
        return JsonResponse({'code':200,'data':skus_list,'base_url':settings.PIC_URL})

    def merge_carts(self,user_id,carts_info):
        #返回值  - > 购物车sku 种类的数量  -> 同步购物车小红点
        carts_data =self.get_carts_all_data(user_id)  #有没有购物车数据
        if not carts_info:
             # 前段购物车没数据
            return len(carts_data)
        for c_dic in carts_info:
            sku_id =int(c_dic['id'])
            count =int(c_dic['count'])
            #判断下储存
            sku_data =SKU.objects.get(id = sku_id)
            if sku_id in carts_data:
                #合并
                old_count =carts_data[sku_id][0]
                #两者取大后再与库存取最小
                new_count =min(sku_data.stock,max(count,old_count))
                new_info =[new_count,1]
            else:
                new_info =[min(count,sku_data.stock),1]
                self.set_carts_data(user_id,sku_id,new_info)
            new_carts =self.get_carts_all_data(user_id)
            return len(new_carts)