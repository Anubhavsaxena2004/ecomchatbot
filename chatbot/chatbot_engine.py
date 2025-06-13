import re
from django.db.models import Q
from products.models import Product, Category
from products.serializers import ProductSerializer

class ChatbotEngine:
    def __init__(self):
        self.intent_patterns = {
            'greeting': [r'hello', r'hi', r'hey', r'good morning', r'good afternoon'],
            'search_product': [r'search for', r'find', r'looking for', r'show me', r'i want', r'need'],
            'price_inquiry': [r'price', r'cost', r'how much', r'expensive', r'cheap'],
            'category_browse': [r'category', r'type', r'kind of'],
            'cart_inquiry': [r'cart', r'basket', r'added', r'purchase'],
            'help': [r'help', r'assist', r'support', r'what can you do'],
            'goodbye': [r'bye', r'goodbye', r'see you', r'thanks', r'thank you'],
        }
        
        self.price_patterns = {
            'under': r'under (\d+)',
            'above': r'above (\d+)',
            'between': r'between (\d+) and (\d+)',
            'around': r'around (\d+)',
        }
    
    def detect_intent(self, message):
        message = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return intent
        
        return 'unknown'
    
    def extract_search_terms(self, message):
        # Remove common words and extract meaningful terms
        stop_words = ['i', 'want', 'need', 'looking', 'for', 'find', 'search', 'show', 'me']
        words = message.lower().split()
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        return ' '.join(search_terms)
    
    def extract_price_range(self, message):
        message = message.lower()
        
        for range_type, pattern in self.price_patterns.items():
            match = re.search(pattern, message)
            if match:
                if range_type == 'under':
                    return {'max_price': int(match.group(1))}
                elif range_type == 'above':
                    return {'min_price': int(match.group(1))}
                elif range_type == 'between':
                    return {'min_price': int(match.group(1)), 'max_price': int(match.group(2))}
                elif range_type == 'around':
                    price = int(match.group(1))
                    return {'min_price': price - 50, 'max_price': price + 50}
        
        return {}
    
    def search_products(self, query, price_range=None):
        search_query = Q(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        ) & Q(is_active=True)
        
        products = Product.objects.filter(search_query)
        
        if price_range:
            if 'min_price' in price_range:
                products = products.filter(price__gte=price_range['min_price'])
            if 'max_price' in price_range:
                products = products.filter(price__lte=price_range['max_price'])
        
        return products[:10]  # Limit to 10 results
    
    def process_message(self, message, session_context=None):
        intent = self.detect_intent(message)
        
        response = {
            'intent': intent,
            'message': '',
            'products': [],
            'suggestions': [],
            'actions': []
        }
        
        if intent == 'greeting':
            response['message'] = "Hello! I'm your shopping assistant. I can help you find products, check prices, and manage your cart. What are you looking for today?"
            response['suggestions'] = [
                "Show me electronics",
                "Find laptops under $1000",
                "What's in my cart?",
                "Help me find a gift"
            ]
        
        elif intent == 'search_product':
            search_terms = self.extract_search_terms(message)
            price_range = self.extract_price_range(message)
            
            if search_terms:
                products = self.search_products(search_terms, price_range)
                
                if products.exists():
                    response['message'] = f"I found {products.count()} products matching '{search_terms}'"
                    response['products'] = ProductSerializer(products, many=True).data
                    response['actions'] = ['show_products']
                else:
                    response['message'] = f"Sorry, I couldn't find any products matching '{search_terms}'. Try different keywords or browse our categories."
                    response['suggestions'] = [cat.name for cat in Category.objects.all()[:5]]
            else:
                response['message'] = "What specific product are you looking for? You can search by name, brand, or category."
        
        elif intent == 'category_browse':
            categories = Category.objects.all()
            response['message'] = "Here are our available categories:"
            response['suggestions'] = [cat.name for cat in categories]
            response['actions'] = ['show_categories']
        
        elif intent == 'price_inquiry':
            price_range = self.extract_price_range(message)
            if price_range:
                products = Product.objects.filter(is_active=True)
                if 'min_price' in price_range:
                    products = products.filter(price__gte=price_range['min_price'])
                if 'max_price' in price_range:
                    products = products.filter(price__lte=price_range['max_price'])
                
                response['message'] = f"Here are products in your price range:"
                response['products'] = ProductSerializer(products[:10], many=True).data
                response['actions'] = ['show_products']
            else:
                response['message'] = "What's your budget? I can show you products in any price range."
        
        elif intent == 'cart_inquiry':
            response['message'] = "Let me check your cart for you."
            response['actions'] = ['show_cart']
        
        elif intent == 'help':
            response['message'] = """I can help you with:
            • Finding products by name, category, or description
            • Filtering by price range
            • Adding items to your cart
            • Checking your cart contents
            • Product recommendations
            
            Just tell me what you're looking for!"""
            response['suggestions'] = [
                "Find smartphones",
                "Show products under $100",
                "Electronics category",
                "What's popular?"
            ]
        
        elif intent == 'goodbye':
            response['message'] = "Thank you for shopping with us! Feel free to ask if you need anything else."
        
        else:
            # Try to search anyway if the message contains product-like terms
            search_terms = self.extract_search_terms(message)
            if search_terms:
                products = self.search_products(search_terms)
                if products.exists():
                    response['message'] = f"I found some products that might interest you:"
                    response['products'] = ProductSerializer(products, many=True).data
                    response['actions'] = ['show_products']
                else:
                    response['message'] = "I'm not sure what you're looking for. Can you be more specific?"
            else:
                response['message'] = "I'm not sure how to help with that. Try asking about products, prices, or your cart."
                response['suggestions'] = [
                    "Find products",
                    "Browse categories",
                    "Check cart",
                    "Help"
                ]
        
        return response 