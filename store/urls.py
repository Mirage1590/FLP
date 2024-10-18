from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.start, name='item_list'),
    path('login/', views.custom_login, name='custom_login'),
    path('register/', views.custom_register, name='custom_register'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('shop/', views.shop, name='shop'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('shoes/', views.shoe_list, name='shoe_list'),
    path('shoes/', views.shoe_all, name='shoe_all'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)