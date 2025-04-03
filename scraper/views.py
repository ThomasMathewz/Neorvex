from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Product,Review,Wishlist
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse
from datetime import datetime,timedelta
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from datetime import datetime
from .scraping import ScrapeFL
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from itertools import zip_longest

def welcome(request):
    if request.method == 'POST':
        action = request.POST.get('')
        if action == 'signup':
            return redirect('signup')
        elif action == 'login':
            return redirect('login')
    return render(request, 'welcome.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists() :
           return render(request, 'signup.html', {'error_message': 'Username '})

        new_user = User.objects.create(username=username, email=email)
        hashed_password = make_password(password)

        new_user.password = hashed_password
        new_user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

        return redirect('home')  # Redirect to the desired page after signup (e.g., home page)

    return render(request, 'signup.html')

def user_login(request):
    if request.method == 'POST':
        print("Request method is POST") 
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user with the provided username and password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # If authentication is successful, log in the user
            login(request, user)
            return redirect('home')  
        else:
            # If authentication fails, render the login page again with an error message
            return render(request, 'login.html', {'error_message': 'Invalid username or password\n try again'})
    
    # If the request method is not POST, render the login page
    return render(request, 'login.html')


def reset(request):
    return render(request, 'reset.html')

@login_required
def home(request):
    if request.method == 'POST':
        Product.objects.all().delete()
        Review.objects.all().delete()
        # Process the form data
        search_query = request.POST.get('search_query')
        ScrapeFL().scrapeProduct(search_query)
        # Redirect to the search results page
        return redirect('search')
    return render(request, 'home.html')


@login_required
def search(request):
    #display result from database models
    products = Product.objects.all().order_by('predicted_rating')
    context = {'products': products}
    if request.method == 'POST':
        # Process the form data
        pid = request.POST.get('PID')
        try:
            product = Product.objects.get(PID=pid)
            if request.user.is_authenticated:
                Wishlist.objects.create(
                    user=request.user,
                    PID=product.PID,
                    title=product.title,
                    link=product.url,
                    specifications=product.specifications,
                    predicted_rating=product.predicted_rating
                )
            else:
                # Handle the case where the user is not logged in
                return HttpResponse('You must be logged in to add to wishlist')
        except Product.DoesNotExist:
            # Handle the case where no product is found with the given PID
            return HttpResponse('Product not found')
    return render(request, 'search.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('welcome')

@login_required
def product(request):
    return render(request, 'product.html')

@login_required
def wishlist(request):
    #display result from database models
    products = Product.objects.all().order_by('predicted_rating')
    context = {'products': products}
    if request.method == 'POST':
        # Process the form data
        pid = request.POST.get('PID')
        try:
            if request.user.is_authenticated:
                Wishlist.objects.filter(PID=pid).delete()
            else:
                # Handle the case where the user is not logged in
                return HttpResponse('You must be logged in to add to wishlist')
        except Product.DoesNotExist:
            # Handle the case where no product is found with the given PID
            return HttpResponse('Product not found')
    return render(request, 'wishlist.html', context)