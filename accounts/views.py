from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages



@login_required
def logout_view(request):
    logout(request)
    return redirect("role_login")

def role_login_view(request, role=None):
    # صفحة دخول مخصّصة لدور معيّن (وصلنا لها من رابط مباشر مثل /accounts/portal-login/donor/)
    if role:
        if request.method == "POST":
            posted_role = request.POST.get("role", role)
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.role.name == posted_role:
                    login(request, user)
                    if posted_role == "manager":
                        return redirect("dashboard")
                    elif posted_role == "donor":
                        return redirect("donor_dashboard")
                    else:
                        return redirect("beneficiary_dashboard")
                else:
                    messages.error(request, "wrong_role")
            else:
                messages.error(request, "invalid_credentials")

        return render(request, "accounts/role_login_page.html", {"active_role": role})

    # صفحة اختيار نوع الحساب (الكروت الثلاثة)
    if request.method == "POST":
        role = request.POST.get("role", "")
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role.name == role:
                login(request, user)
                if role == "manager":
                    return redirect("dashboard")
                elif role == "donor":
                    return redirect("donor_dashboard")
                else:
                    return redirect("beneficiary_dashboard")
            else:
                messages.error(request, "wrong_role")
        else:
            messages.error(request, "invalid_credentials")

        # لو صار خطأ، نرجّع نفس الصفحة مع تفعيل نفس الكرت اللي اختاره
        return render(request, "accounts/portal_select.html", {"active_role": role})

    return render(request, "accounts/portal_select.html", {"active_role": ""})