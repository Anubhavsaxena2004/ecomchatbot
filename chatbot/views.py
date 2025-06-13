from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatSession, ChatMessage, SearchQuery
from .chatbot_engine import ChatbotEngine
import json

# Create your views here.

class ChatbotView(TemplateView):
    template_name = 'chatbot/chatbot.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class ChatView(TemplateView):
    template_name = 'chatbot/chat.html'

class ChatSessionView(APIView):
    def get(self, request):
        # Get or create chat session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        session, created = ChatSession.objects.get_or_create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            defaults={'is_active': True}
        )
        
        # Get recent messages
        messages = session.messages.all()[:50]
        
        return Response({
            'session_id': str(session.id),
            'messages': [
                {
                    'type': msg.message_type,
                    'content': msg.content,
                    'metadata': msg.metadata,
                    'timestamp': msg.timestamp.isoformat()
                } for msg in messages
            ]
        })
    
    def post(self, request):
        # Reset chat session
        session_key = request.session.session_key
        if session_key:
            ChatSession.objects.filter(session_key=session_key).update(is_active=False)
        
        return Response({'message': 'Chat session reset'})

class ChatMessageView(APIView):
    def post(self, request):
        message_content = request.data.get('message', '')
        session_id = request.data.get('session_id')
        
        if not message_content:
            return Response(
                {'error': 'Message content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                return Response(
                    {'error': 'Invalid session ID'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            session, created = ChatSession.objects.get_or_create(
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key,
                defaults={'is_active': True}
            )
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message_content
        )
        
        # Process with chatbot engine
        chatbot = ChatbotEngine()
        bot_response = chatbot.process_message(message_content)
        
        # Save bot response
        bot_message = ChatMessage.objects.create(
            session=session,
            message_type='bot',
            content=bot_response['message'],
            metadata={
                'intent': bot_response['intent'],
                'products': bot_response['products'],
                'suggestions': bot_response['suggestions'],
                'actions': bot_response['actions']
            }
        )
        
        # Log search query if it was a search
        if bot_response['intent'] in ['search_product', 'price_inquiry']:
            SearchQuery.objects.create(
                session=session,
                query=message_content,
                results_count=len(bot_response['products'])
            )
        
        return Response({
            'session_id': str(session.id),
            'user_message': {
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'bot_response': {
                'content': bot_message.content,
                'metadata': bot_message.metadata,
                'timestamp': bot_message.timestamp.isoformat()
            }
        })
