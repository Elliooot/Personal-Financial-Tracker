"""
URL configuration for personal_finance_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from finance import views
from finance.views import detail_view, statistics_view, management_view, delete_transaction_view, add_category

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('detail/', views.detail_view, name='detail'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('management/', views.management_view, name='management'),
    path('delete-transaction/', delete_transaction_view, name='delete_transaction'),
    path('add-category/', add_category, name='add_category'),
    path('delete-category/', views.delete_category_view, name='delete_category'),
    path('update-transaction/', views.update_transaction_view, name='update_transaction'),
]
