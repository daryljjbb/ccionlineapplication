from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Agency, Customer,Policy, Carrier

admin.site.register(Agency)
admin.site.register(Customer)
admin.site.register(Policy)


