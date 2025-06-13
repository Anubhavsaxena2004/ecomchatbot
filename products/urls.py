from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'cart', views.CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('products/search/', views.ProductViewSet.as_view({'get': 'search'}), name='product-search'),
    path('products/<int:pk>/add-to-cart/', views.ProductViewSet.as_view({'post': 'add_to_cart'}), name='add-to-cart'),
    path('cart/<int:pk>/update-item/', views.CartViewSet.as_view({'post': 'update_item'}), name='update-cart-item'),
    path('cart/<int:pk>/remove-item/', views.CartViewSet.as_view({'post': 'remove_item'}), name='remove-cart-item'),
    path('cart/<int:pk>/clear/', views.CartViewSet.as_view({'post': 'clear'}), name='clear-cart'),
] 