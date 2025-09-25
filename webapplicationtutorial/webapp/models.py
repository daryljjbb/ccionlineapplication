from django.db import models
from django.utils import timezone
import os
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation


class Agency(models.Model):
    """
    A singleton model to store the agency's own information.
    We will use pk=1 as the single instance.
    """
    name = models.CharField(max_length=200, default="My Insurance Agency")
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='agency_logos/', null=True, blank=True, help_text="Optional: Upload your agency's logo.")

    class Meta:
        verbose_name_plural = "Agency Information"

    def __str__(self):
        return self.name
    
class Customer(models.Model):
    """Represents a customer, who can be an individual or a company."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospect', 'Prospect'),
    ]
    SOURCE_CHOICES = [
        ('walk_in', 'Walk-in'),
        ('transfer', 'Transfer'),
        ('pending', 'Pending'),
        ('referral', 'Referral'),
        ('web', 'Web'),
        ('other', 'Other'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, help_text="Customer's primary email.")
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='prospect')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='pending', blank=True)
    notes = models.TextField(blank=True, help_text="Internal sticky note for the customer.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Carrier(models.Model):
    """Represents an insurance carrier."""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class Policy(models.Model):
    """Represents an insurance policy."""
    POLICY_TYPE_CHOICES = [
        ('auto', 'Auto'),
        ('home', 'Homeowners'),
        ('life', 'Life'),
        ('health', 'Health'),
        # You can add other insurance types here
    ]
    POLICY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='policies')
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT, related_name='policies', null=True, blank=True)
    policy_number = models.CharField(max_length=50, unique=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    effective_date = models.DateField()
    expiration_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="The base premium from the carrier (sum of coverages).")
    agency_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=POLICY_STATUS_CHOICES, default='pending')
    # Use a JSONField to store policy-type-specific details.
    # This gives you flexibility for different insurance industries.
    # For an 'auto' policy, you could store:
    # {'vin': '...', 'make': '...', 'model': '...', 'year': ...}
    details = models.JSONField(default=dict, blank=True, help_text="Stores industry-specific policy details.")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_policies')
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_premium(self):
        """Calculates the total amount for the policy (premium + fees)."""
        return self.premium_amount + self.agency_fee

    def __str__(self):
        return f"Policy {self.policy_number} for {self.customer}"

    @property
    def total_customer_cost(self):
        """Return total_customer_cost as Decimal if present in details, else None."""
        raw = self.details.get('total_customer_cost') if isinstance(self.details, dict) else None
        if raw in (None, ''):
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return None

    @total_customer_cost.setter
    def total_customer_cost(self, value):
        """Set total_customer_cost in details JSON. Accept Decimal or numeric/string."""
        if not isinstance(self.details, dict):
            self.details = {}
        if value is None:
            self.details['total_customer_cost'] = None
            return
        try:
            dec = Decimal(value)
            # store as string to keep JSON serialization predictable
            self.details['total_customer_cost'] = str(dec)
        except (InvalidOperation, ValueError):
            # on invalid input, store None
            self.details['total_customer_cost'] = None
