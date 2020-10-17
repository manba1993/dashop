from django.urls import path
from . import views
from django.views.decorators.cache import  cache_page
urlpatterns =[
    path('/index',cache_page(60,cache='goods')(views.GoodsIndexView.as_view()) ) ,#视图类引用时需要带上as_view()
    #http://127.0.0.1:8000/v1/goods/detail/1
    path('/detail/<str:sku_id>',views.GoodsDetailView.as_view())


]