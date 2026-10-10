from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add-donor/", views.add_donor, name="add_donor"),
    path("donors/", views.donor_management, name="donor_management"),
    path("donors/<str:donor_id>/", views.donor_portal, name="donor_portal"),
    path("beneficiaries/", views.beneficiary_management, name="beneficiary_management"),
    path("beneficiaries/<str:beneficiary_id>/", views.beneficiary_portal, name="beneficiary_portal"),
    path("grant-management/", views.grant_management, name="grant_management"),
    path("grants/<str:grant_id>/upload-report/", views.upload_grant_report, name="upload_grant_report"),
]
