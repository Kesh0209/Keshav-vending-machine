from django.urls import path
from . import views
from . import api

urlpatterns = [
    # -------------------------
    # Frontend / Website Views
    # -------------------------
    path('', views.index, name='index'),
    path('enter-name/', views.enter_name, name='enter_name'),
    path('vending/', views.vending_machine, name='vending'),
    path('purchase/', views.purchase, name='purchase'),
    path('products/', views.products, name='products'),
    path('logout/', views.logout_view, name='logout'),

    # -------------------------
    # API Endpoints
    # -------------------------
    path('api/products/', api.products_api, name='products_api'),              # GET all / POST new
    path('api/products/<int:pk>/', api.product_detail_api, name='product_detail_api'),  # GET, PUT/PATCH, DELETE single
    path('api/sessions/', api.sessions_api, name='sessions_api'),              # GET all sessions
    path('api/orders/', api.orders_api, name='orders_api'),                    # GET all orders
    path('api/purchase/', api.purchase_api, name='purchase_api'),
    path('api/purchases/', api.purchases_api, name='purchases_api'),
]




from django.urls import path
from . import views

urlpatterns = [
    # YOUR EXISTING URL PATTERNS (KEEP THESE)
    path('', views.index, name='index'),
    path('enter_name/', views.enter_name, name='enter_name'),
    path('vending/', views.vending_machine, name='vending'),
    path('products/', views.products, name='products'),
    path('purchase/', views.purchase, name='purchase'),
    path('logout/', views.logout_view, name='logout'),
    path('api/products/', views.products_api, name='products_api'),
    
    # ADD THESE NEW API ENDPOINTS FOR TKINTER
    path('api/products/', views.api_products, name='api_products'),
    path('api/purchase/', views.api_purchase, name='api_purchase'), 
    path('api/purchases/', views.api_purchases, name='api_purchases'),
]