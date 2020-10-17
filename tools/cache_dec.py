from django.core.cache import caches


# 参数 key_prefix,key_param,expire(s),cache(where)

def cache_check(**cache_kwargs):
    def _cache_check(func):  # 视图
        def wrapper(self, request, *args, **kwargs):  # 具体 func 要传的参数
            CACHE = caches['default']
            if 'cache' in cache_kwargs:
                CACHE =caches[cache_kwargs['cache']]   #如果传参数，用传过来的
            key_prefix =cache_kwargs['key_prefix']
            key_param =cache_kwargs['key_param']  #取哪一项做唯一标识
            expire =cache_kwargs.get('expire',30)  #过期时间
            #"/detail/1   - - > def get(self,request,sku_id)
            if key_param not in kwargs:
                raise
            cache_key =key_prefix + kwargs[key_param]
            print('cache_key is %s'%(cache_key))
            res =CACHE.get(cache_key)
            if res:  #有缓存，直接跳出装饰器
                print('return %s cache'%(cache_key))
                return res
            #没有缓存，走视图
            res = func(self,request,*args,**kwargs)  #def get JsonResponse
            CACHE.set(cache_key,res,expire)
            return res

            #return func
        return wrapper
    return _cache_check
