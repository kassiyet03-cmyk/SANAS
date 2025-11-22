from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contact/', views.contact, name='contact'),
    re_path(r'^product/(?P<slug>[\w-]+)/$', views.product_detail, name='product_detail'),

    # Admin Panel URLs
    path('panel/', views.panel_dashboard, name='panel_dashboard'),
    path('panel/login/', views.panel_login, name='panel_login'),
    path('panel/logout/', views.panel_logout, name='panel_logout'),
    path('panel/items/', views.panel_items, name='panel_items'),
    path('panel/items/add/', views.panel_item_add, name='panel_item_add'),
    path('panel/items/<int:item_id>/edit/', views.panel_item_edit, name='panel_item_edit'),
    path('panel/items/<int:item_id>/delete/', views.panel_item_delete, name='panel_item_delete'),
    path('panel/categories/', views.panel_categories, name='panel_categories'),
]
