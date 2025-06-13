from rest_framework import serializers
from .models import Product, Category, Cart, CartItem, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specifications = serializers.JSONField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category',
            'stock', 'rating', 'specifications', 'images',
            'created_at', 'updated_at'
        ]

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.product.price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
    
    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
    
    def get_total_price(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all()) 