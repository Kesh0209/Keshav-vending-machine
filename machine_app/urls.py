from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('enter-name/', views.enter_name, name='enter_name'),
    path('vending/', views.vending_machine, name='vending'),
    path('purchase/', views.purchase, name='purchase'),
    path('products/', views.products, name='products'),
    path('logout/', views.logout_view, name='logout'),
]