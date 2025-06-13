from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChatbotView.as_view(), name='chatbot-home'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('api/chat/message/', views.ChatMessageView.as_view(), name='chat-message'),
    path('api/chat/session/', views.ChatSessionView.as_view(), name='chat-session'),
] 