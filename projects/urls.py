from django.urls import path
from . import views

urlpatterns = [
    # Home and browsing
    path('', views.HomeView.as_view(), name='home'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('project/<slug:slug>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category_projects'),
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Cart functionality
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:project_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]
