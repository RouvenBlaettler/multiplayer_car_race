"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from game.views import game_view, game_lobby, create_game, join_game

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', game_lobby, name='game_lobby'),
    path('create/', create_game, name='create_game'),
    path('join/<int:game_id>/', join_game, name='join_game'),
    path('game/<int:game_id>/', game_view, name='game_view'),
]
