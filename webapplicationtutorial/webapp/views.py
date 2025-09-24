from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
import copy
import json
from dateutil.relativedelta import relativedelta
from functools import wraps


from .forms import  UserAdminCreationForm, UserAdminChangeForm, AgencyForm, PolicyForm, CustomerForm, CarrierForm
from .models import Agency, Customer, Policy, Carrier
from .forms import CustomerForm
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# Create your views here.
NAV_ITEMS = [    # This is where the side navbar Items are defined.
    {'label': 'Dashboard', 'url': 'dashboard', 'icon': 'bi-speedometer2'},
    {'label': 'Customers', 'url': 'customer_search', 'icon': 'bi-people-fill'},
    
    {
        'label': 'Settings',
        'url': '#',
        'icon': 'bi-gear',
        'children': [ # This is where the dropdown items are defined for the Settings menu.
            {'label': 'Agency Information', 'url': 'agency_settings'},
            {'label': 'Manage Users', 'url': 'user_list', 'admin_only': True},
            {'label': 'Manage Carriers', 'url': 'carrier_list'},


        ]
    },
]

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def superuser_required(view_func):
    """Decorator for views that checks that the user is a superuser."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_nav_items(request):
    """Returns a copy of NAV_ITEMS, filtered for the current user's permissions."""
    nav_items = copy.deepcopy(NAV_ITEMS)
    if not request.user.is_superuser:
        for item in nav_items:
            if 'children' in item:
                item['children'] = [child for child in item['children'] if not child.get('admin_only')]
    return nav_items

@login_required
def dashboard(request):
    
    context = {
        'title': 'Dashboard',
        'active_page': 'dashboard',
        'nav_items': get_nav_items(request),
        
    }
    return render(request, 'webapp/dashboard.html', context)


@login_required
@superuser_required
def user_list(request):
    """Displays a list of all users for admins."""
    users = User.objects.all().order_by('username')
    context = {
        'title': 'Manage Users',
        'active_page': 'settings',
        'nav_items': get_nav_items(request),
        'users': users,
    }
    return render(request, 'webapp/user_list.html', context)

@login_required
@superuser_required
def user_form(request, user_id=None):
    """Handles creating and editing a user."""
    if user_id:
        user = get_object_or_404(User, pk=user_id)
        title = f'Edit User: {user.username}'
        FormClass = UserAdminChangeForm
    else:
        user = None
        title = 'Create New User'
        FormClass = UserAdminCreationForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=user)
        if form.is_valid():
            new_user = form.save() # This handles password creation for new users
            messages.success(request, f"User '{new_user.username}' saved successfully.")
            return redirect('user_list')
    else:
        form = FormClass(instance=user)

    context = {
        'title': title,
        'active_page': 'settings',
        'nav_items': get_nav_items(request),
        'form': form,
        'user_instance': user,
    }
    return render(request, 'webapp/user_form.html', context)

@login_required
def agency_settings(request):
    """
    A view to edit the singleton Agency Information model.
    """
    # Use get_or_create to ensure the singleton object exists.
    agency, created = Agency.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = AgencyForm(request.POST, request.FILES, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, "Agency information updated successfully.")
            return redirect('agency_settings')
    else:
        form = AgencyForm(instance=agency)
        
    context = {
        'title': 'Agency Information',
        'active_page': 'settings',
        'nav_items': get_nav_items(request),
        'form': form,
    }
    return render(request, 'webapp/agency_settings.html', context)

@login_required
def customer_search(request):
    """
    Renders the customer search page and handles AJAX requests for the
    customer list to enable fast, client-side searching.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        customers = Customer.objects.all().values('id', 'first_name', 'last_name', 'email', 'status')
        return JsonResponse(list(customers), safe=False)

    return render(request, 'webapp/customer_search.html', {
        'title': 'Customer Search',
        'active_page': 'customer_search',
        'nav_items': get_nav_items(request),
    })

@login_required
def create_customer(request):
    """
    Handles the creation of a new customer via a model form.
    """
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer}' created successfully!")
            return redirect('customer_search')
    else:
        form = CustomerForm()

    return render(request, 'webapp/create_customer.html', {
        'title': 'Create Customer',
        'active_page': 'customer_search',
        'form': form,
        'nav_items': get_nav_items(request),
    })

@login_required
def customer_detail(request, customer_id):
    """
    Displays the details for a specific customer, including their
    policies, invoices, and suspense items.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    policies = customer.policies.all().order_by('-effective_date')

    # Fetch related items, ordered by most recent




    context = {
        'title': f'Customer Details: {customer}',
        'active_page': 'customer_search',
        'nav_items': get_nav_items(request),
        'customer': customer,
        'policies': policies,


    }
    return render(request, 'webapp/customer_detail.html', context)

@login_required
def edit_customer(request, customer_id):
    """
    Handles editing an existing customer.
    """
    customer = get_object_or_404(Customer, pk=customer_id)

    # Create a deep copy to avoid modifying the global NAV_ITEMS constant
    nav_items = get_nav_items(request)
    # Find the 'Customers' link and modify it to be a "Back" link
    for item in nav_items:
        if item.get('url') == 'customer_search':
            item['label'] = 'Back to Customer'
            item['icon'] = 'bi-arrow-left-circle'
            item['href'] = reverse('customer_detail', args=[customer.id])
            if 'url' in item: del item['url']
            break
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer) # This allows editing of existing instance
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer '{customer}' updated successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'webapp/edit_customer.html', {
        'title': f'Edit Customer: {customer}',
        'active_page': 'customer_search',
        'form': form,
        'customer': customer,
        'nav_items': nav_items,
    })
@login_required
def carrier_list(request):
    """
    Manages insurance carriers.
    - Handles AJAX requests to fetch all carriers for client-side searching.
    - Handles POST requests to create a new carrier.
    - Renders the carrier management page.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        carriers = Carrier.objects.all().order_by('name').values('id', 'name', 'is_active')
        return JsonResponse(list(carriers), safe=False)

    if request.method == 'POST':
        form = CarrierForm(request.POST)
        if form.is_valid():
            carrier = form.save()
            messages.success(request, f"Carrier '{carrier.name}' added successfully.")
            return redirect('carrier_list')
        # If form is not valid, it will be re-rendered with errors below
    else:
        form = CarrierForm(initial={'is_active': True})

    context = {
        'title': 'Manage Carriers',
        'active_page': 'settings',
        'nav_items': get_nav_items(request),
        'form': form,
    }
    return render(request, 'webapp/carrier_list.html', context)


@login_required
def select_policy_type(request, customer_id):
    """
    Renders a page for the user to select the type of policy to create.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    
    # Create a deep copy to avoid modifying the global NAV_ITEMS constant
    nav_items = get_nav_items(request)
    # Find the 'Customers' link and modify it to be a "Back" link
    for item in nav_items:
        if item.get('url') == 'customer_search':
            item['label'] = 'Back to Customer'
            item['icon'] = 'bi-arrow-left-circle'
            item['href'] = reverse('customer_detail', args=[customer.id])
            if 'url' in item:
                del item['url']
            break
    policy_types = Policy.POLICY_TYPE_CHOICES
    context = {
        'title': 'Select Policy Type',
        'active_page': 'customer_search',
        'nav_items': nav_items,
        'customer': customer,
        'policy_types': policy_types,
    }
    return render(request, 'webapp/select_policy_type.html', context)

@login_required
def create_policy(request, customer_id, policy_type):
    """
    Handles the creation of a new policy for a specific customer.
    It renders the correct template based on policy_type and handles
    the dynamic form submission.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    
    # Create a deep copy to avoid modifying the global NAV_ITEMS constant
    nav_items = get_nav_items(request)
    # Find the 'Customers' link and modify it to be a "Back" link
    for item in nav_items:
        if item.get('url') == 'customer_search':
            item['label'] = 'Back to Customer'
            item['icon'] = 'bi-arrow-left-circle'
            item['href'] = reverse('customer_detail', args=[customer.id])
            if 'url' in item:
                del item['url']
            break
    
    # Determine which template to use
    template_map = {
        'auto': 'webapp/create_auto_policy.html',
        'home': 'webapp/create_home_policy.html',
    }
    template_name = template_map.get(policy_type)
    if not template_name:
        messages.error(request, "Invalid policy type specified.")
        return redirect('customer_detail', customer_id=customer.id)

    if request.method == 'POST':
        form = PolicyForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.customer = customer
            policy.policy_type = policy_type
            if request.user.is_authenticated:
                policy.created_by = request.user

            # --- Auto Policy Details Parsing ---
            if policy_type == 'auto':
                vehicles_data = []
                i = 0
                while f'vehicle-{i}-vin' in request.POST:
                    vehicle_data = {
                        'year': request.POST.get(f'vehicle-{i}-year'),
                        'make': request.POST.get(f'vehicle-{i}-make'),
                        'model': request.POST.get(f'vehicle-{i}-model'),
                        'vin': request.POST.get(f'vehicle-{i}-vin'),
                        'coverages': []
                    }
                    j = 0
                    while f'vehicle-{i}-coverage-{j}-name' in request.POST:
                        coverage_data = {
                            'name': request.POST.get(f'vehicle-{i}-coverage-{j}-name'),
                            'limit': request.POST.get(f'vehicle-{i}-coverage-{j}-limit'),
                            'premium': request.POST.get(f'vehicle-{i}-coverage-{j}-premium')
                        }
                        vehicle_data['coverages'].append(coverage_data)
                        j += 1
                    vehicles_data.append(vehicle_data)
                    i += 1
                policy.details = {'vehicles': vehicles_data}
            
            elif policy_type == 'home':
                policy.details = {
                    'property_address': request.POST.get('property_address'),
                    'year_built': request.POST.get('year_built'),
                    'square_footage': request.POST.get('square_footage'),
                    'coverages': {
                        'dwelling': {'limit': request.POST.get('dwelling_limit'), 'premium': request.POST.get('dwelling_premium')},
                        'other_structures': {'limit': request.POST.get('other_structures_limit'), 'premium': request.POST.get('other_structures_premium')},
                        'personal_property': {'limit': request.POST.get('personal_property_limit'), 'premium': request.POST.get('personal_property_premium')},
                        'loss_of_use': {'limit': request.POST.get('loss_of_use_limit'), 'premium': request.POST.get('loss_of_use_premium')},
                        'personal_liability': {'limit': request.POST.get('personal_liability_limit'), 'premium': request.POST.get('personal_liability_premium')},
                        'medical_payments': {'limit': request.POST.get('medical_payments_limit'), 'premium': request.POST.get('medical_payments_premium')},
                    },
                    'deductible': request.POST.get('deductible'),
                    'wind_deductible': request.POST.get('wind_deductible'),
                }
            
            policy.save()
            messages.success(request, f"Policy '{policy.policy_number}' created successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = PolicyForm()

    context = {
        'title': f'Create {policy_type.capitalize()} Policy',
        'active_page': 'customer_search',
        'nav_items': nav_items,
        'customer': customer,
        'form': form
    }
    return render(request, template_name, context)


@login_required
def policy_detail(request, policy_id):
    """
    Displays the details for a specific policy.
    """
    policy = get_object_or_404(Policy, pk=policy_id)
    customer = policy.customer

    # Create a deep copy to avoid modifying the global NAV_ITEMS constant
    nav_items = get_nav_items(request)
    # Find the 'Customers' link and modify it to be a "Back" link
    for item in nav_items:
        if item.get('url') == 'customer_search':
            item['label'] = 'Back to Customer'
            item['icon'] = 'bi-arrow-left-circle'
            item['href'] = reverse('customer_detail', args=[customer.id])
            if 'url' in item:
                del item['url']
            break

    context = {
        'title': f'Policy Details: {policy.policy_number}',
        'active_page': 'customer_search', # to keep customer nav active
        'nav_items': nav_items,
        'policy': policy,
    }
    return render(request, 'webapp/policy_detail.html', context)

@login_required
def edit_policy(request, policy_id):
    """
    Handles editing an existing policy.
    """
    policy = get_object_or_404(Policy, pk=policy_id)
    customer = policy.customer
    policy_type = policy.policy_type

    # Create a deep copy to avoid modifying the global NAV_ITEMS constant
    nav_items = get_nav_items(request)
    # Find the 'Customers' link and modify it to be a "Back" link
    for item in nav_items:
        if item.get('url') == 'customer_search':
            item['label'] = 'Back to Policy'
            item['icon'] = 'bi-arrow-left-circle'
            item['href'] = reverse('policy_detail', args=[policy.id])
            if 'url' in item:
                del item['url']
            break

    # Determine which template to use
    template_map = {
        'auto': 'webapp/edit_auto_policy.html',
        'home': 'webapp/edit_homeowner_policy.html',
    }
    template_name = template_map.get(policy_type)
    if not template_name:
        messages.error(request, "Cannot edit policy of this type.")
        return redirect('policy_detail', policy_id=policy.id)

    if request.method == 'POST':
        form = PolicyForm(request.POST, instance=policy)
        if form.is_valid():
            policy_instance = form.save(commit=False)
            # Start with existing details and update them
            details = policy_instance.details
            if not isinstance(details, dict):
                details = {}

            # --- Auto Policy Details Parsing ---
            if policy_type == 'auto':
                vehicles_data = []
                i = 0
                while f'vehicle-{i}-vin' in request.POST:
                    vehicle_data = {
                        'year': request.POST.get(f'vehicle-{i}-year'),
                        'make': request.POST.get(f'vehicle-{i}-make'),
                        'model': request.POST.get(f'vehicle-{i}-model'),
                        'vin': request.POST.get(f'vehicle-{i}-vin'),
                        'coverages': []
                    }
                    j = 0
                    while f'vehicle-{i}-coverage-{j}-name' in request.POST:
                        coverage_data = {
                            'name': request.POST.get(f'vehicle-{i}-coverage-{j}-name'),
                            'limit': request.POST.get(f'vehicle-{i}-coverage-{j}-limit'),
                            'premium': request.POST.get(f'vehicle-{i}-coverage-{j}-premium')
                        }
                        vehicle_data['coverages'].append(coverage_data)
                        j += 1
                    vehicles_data.append(vehicle_data)
                    i += 1
                details['vehicles'] = vehicles_data
            
            elif policy_type == 'home':
                home_details = {
                    'property_address': request.POST.get('property_address'),
                    'year_built': request.POST.get('year_built'),
                    'square_footage': request.POST.get('square_footage'),
                    'coverages': {
                        'dwelling': {'limit': request.POST.get('dwelling_limit'), 'premium': request.POST.get('dwelling_premium')},
                        'other_structures': {'limit': request.POST.get('other_structures_limit'), 'premium': request.POST.get('other_structures_premium')},
                        'personal_property': {'limit': request.POST.get('personal_property_limit'), 'premium': request.POST.get('personal_property_premium')},
                        'loss_of_use': {'limit': request.POST.get('loss_of_use_limit'), 'premium': request.POST.get('loss_of_use_premium')},
                        'personal_liability': {'limit': request.POST.get('personal_liability_limit'), 'premium': request.POST.get('personal_liability_premium')},
                        'medical_payments': {'limit': request.POST.get('medical_payments_limit'), 'premium': request.POST.get('medical_payments_premium')},
                    },
                    'deductible': request.POST.get('deductible'),
                    'wind_deductible': request.POST.get('wind_deductible'),
                }
                details.update(home_details)

            policy_instance.details = details
            policy_instance.save()
            messages.success(request, f"Policy '{policy.policy_number}' updated successfully!")
            return redirect('policy_detail', policy_id=policy.id)
    else:
        form = PolicyForm(instance=policy)

    context = {
        'title': f'Edit {policy_type.capitalize()} Policy',
        'active_page': 'customer_search',
        'nav_items': nav_items,
        'customer': customer,
        'policy': policy,
        'form': form,
        'policy_details_json': json.dumps(policy.details)
    }
    return render(request, template_name, context)
