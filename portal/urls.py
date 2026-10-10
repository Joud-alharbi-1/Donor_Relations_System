from django.urls import path
from . import views

urlpatterns = [
    path("donor/", views.donor_dashboard, name="donor_dashboard"),
    path("donor/beneficiaries/", views.donor_beneficiaries, name="donor_beneficiaries"),
    path("beneficiary/", views.beneficiary_dashboard, name="beneficiary_dashboard"),
    path("beneficiary/donors/", views.beneficiary_donors, name="beneficiary_donors"),
]