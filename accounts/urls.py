from django.urls import path
from . import views

urlpatterns = [
    path("portal-login/", views.role_login_view, name="role_login"),
    path("portal-login/donor/", views.role_login_view, {"role": "donor"}, name="login_donor_page"),
    path("portal-login/beneficiary/", views.role_login_view, {"role": "beneficiary"}, name="login_beneficiary_page"),
    path("portal-login/manager/", views.role_login_view, {"role": "manager"}, name="login_manager_page"),
    path("logout/", views.logout_view, name="logout"),
]