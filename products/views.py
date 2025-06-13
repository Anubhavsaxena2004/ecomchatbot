from django.shortcuts import render
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Product, Category, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer
from django.core.cache import cache
from ecommerce_chatbot.cache import cache_product_list, cache_product_details, cache_search_results
from ecommerce_chatbot.error_handling import handle_api_error, handle_validation_error

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in a category."""
        category = self.get_object()
        products = Product.objects.filter(category=category)
        
        # Apply filters
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Apply sorting
        sort_by = request.query_params.get('sort_by', '-rating')
        if sort_by in ['price', '-price', 'rating', '-rating', 'name', '-name']:
            products = products.order_by(sort_by)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'specifications']
    ordering_fields = ['price', 'rating', 'name']
    ordering = ['-rating']

    @cache_product_list(timeout=300)
    def list(self, request, *args, **kwargs):
        """List products with filtering and pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply price range filter
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Apply category filter
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Apply rating filter
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @cache_product_details(timeout=300)
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single product with caching."""
        return super().retrieve(request, *args, **kwargs)

    @cache_search_results(timeout=300)
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search endpoint with caching."""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build search query
        search_query = Q(name__icontains=query) | Q(description__icontains=query)
        
        # Add category to search if provided
        category = request.query_params.get('category')
        if category:
            search_query &= Q(category__name__icontains=category)
        
        # Add price range to search if provided
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            search_query &= Q(price__gte=min_price)
        if max_price:
            search_query &= Q(price__lte=max_price)
        
        # Execute search
        products = Product.objects.filter(search_query)
        
        # Apply sorting
        sort_by = request.query_params.get('sort_by', '-rating')
        if sort_by in ['price', '-price', 'rating', '-rating', 'name', '-name']:
            products = products.order_by(sort_by)
        
        # Paginate results
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_to_cart(self, request, pk=None):
        """Add a product to the user's cart."""
        product = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            return Response({'error': 'Quantity must be greater than 0'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if quantity > product.stock:
            return Response({'error': 'Not enough stock available'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    
    def get_queryset(self):
        """Return cart for the current user."""
        return Cart.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_item(self, request, pk=None):
        """Update quantity of an item in the cart."""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 0))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            if quantity > cart_item.product.stock:
                return Response({'error': 'Not enough stock available'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity
            cart_item.save()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from the cart."""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Clear all items from the cart."""
        cart = self.get_object()
        cart.items.all().delete()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
