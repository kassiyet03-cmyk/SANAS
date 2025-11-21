from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    re_path(r'^product/(?P<slug>[\w-]+)/$', views.product_detail, name='product_detail'),
]
