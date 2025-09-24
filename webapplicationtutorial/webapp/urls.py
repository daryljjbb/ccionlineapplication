from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/agency/', views.agency_settings, name='agency_settings'),
    path('settings/users/', views.user_list, name='user_list'),
    path('settings/users/create/', views.user_form, name='user_create'),
    path('settings/users/<int:user_id>/edit/', views.user_form, name='user_edit'),
    path('settings/carriers/', views.carrier_list, name='carrier_list'),
    path('customers/search/', views.customer_search, name='customer_search'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', views.edit_customer, name='edit_customer'),
    path('customers/<int:customer_id>/policies/select-type/', views.select_policy_type, name='select_policy_type'),
    path('customers/<int:customer_id>/policies/create/<str:policy_type>/', views.create_policy, name='create_policy'),
    path('policies/<int:policy_id>/', views.policy_detail, name='policy_detail'),
    path('policies/<int:policy_id>/edit/', views.edit_policy, name='edit_policy'),
]