from webapp.models import Agency

def agency(request):
    """
    Context processor to add agency information to the context.
    """
    agency_instance = Agency.objects.first()  # Assuming only one agency instance
    return {'agency': agency_instance}
