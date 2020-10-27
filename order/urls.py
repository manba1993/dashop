from django.urls import path

from . import views


urlpatterns =[
    path("/<str:username>",views.OrderInfoView.as_view()),
    path("/<str:username>/advance",views.AdvanceView.as_view())


]