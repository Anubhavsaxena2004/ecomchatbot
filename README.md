# E-commerce Chatbot

A Django-based e-commerce chatbot application that provides an interactive shopping experience through natural language conversations.

## Features

- Interactive chat interface for product search and recommendations
- Advanced product filtering and sorting
- Product comparison functionality
- Shopping cart management
- User authentication and profile management
- Responsive design for all devices

## Prerequisites

- Python 3.8+
- MySQL 5.7+
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ecommerce_chatbot.git
cd ecommerce_chatbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the database:
   - Create a MySQL database
   - Update database settings in `ecommerce_chatbot/settings.py`

5. Run migrations:
```bash
python manage.py migrate
```

6. Populate the database with mock data:
```bash
python scripts/populate_db.py
```

7. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Products
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get product details
- `GET /api/products/search/` - Search products
- `POST /api/products/{id}/add-to-cart/` - Add product to cart

### Categories
- `GET /api/categories/` - List all categories
- `GET /api/categories/{id}/` - Get category details

### Cart
- `GET /api/cart/` - Get cart details
- `POST /api/cart/{id}/update-item/` - Update cart item
- `POST /api/cart/{id}/remove-item/` - Remove item from cart
- `POST /api/cart/{id}/clear/` - Clear cart

## Project Structure

```
ecommerce_chatbot/
├── ecommerce_chatbot/      # Project settings
├── products/              # Products app
│   ├── models.py         # Database models
│   ├── views.py          # API views
│   ├── serializers.py    # API serializers
│   └── urls.py           # URL configuration
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── auth/            # Authentication templates
│   └── chatbot/         # Chatbot templates
├── static/              # Static files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Images
└── scripts/            # Utility scripts
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 