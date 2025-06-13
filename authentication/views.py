from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class LoginView(TemplateView):
    template_name = 'auth/login.html'
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('chatbot-home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, self.template_name)

class RegisterView(TemplateView):
    template_name = 'auth/register.html'
    
    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, self.template_name)
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, self.template_name)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'auth/profile.html'
    login_url = '/auth/login/'
