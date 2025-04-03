from . import views
from django.urls import path

urlpatterns = [
    path('welcome/', views.welcome, name='welcome'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('reset/', views.reset, name='reset'),
    
    path('home/',views.home, name='home'),
    path('search/',views.search, name='search'),
    path('product',views.product, name='product'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('logout/', views.logout_view, name='logout')
    
]