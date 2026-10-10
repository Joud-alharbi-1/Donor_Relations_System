"""
decorators.py — عزل البيانات حسب الدور
يُستخدم على أي view خاص ببوابة المانح أو المستفيد، للتأكد من:
1. المستخدم مسجّل دخول وله الدور الصحيح.
2. جلب جهته (donor أو beneficiary) تلقائياً وإرفاقها بالـ request،
   عشان الـ view يفلتر بيانات هذي الجهة فقط دون غيرها.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def donor_required(view_func):
    """
    يسمح فقط لمستخدم دوره donor وله جهة مانحة مرتبطة بحسابه.
    يرفق الجهة كـ request.donor عشان الـ view يستخدمها مباشرة.
    """
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role.name != "donor" or request.user.donor is None:
            raise PermissionDenied("هذا الحساب غير مرتبط بجهة مانحة")
        request.donor = request.user.donor
        return view_func(request, *args, **kwargs)
    return wrapper


def beneficiary_required(view_func):
    """
    يسمح فقط لمستخدم دوره beneficiary وله جهة مستفيدة مرتبطة بحسابه.
    يرفق الجهة كـ request.beneficiary عشان الـ view يستخدمها مباشرة.
    """
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role.name != "beneficiary" or request.user.beneficiary is None:
            raise PermissionDenied("هذا الحساب غير مرتبط بجهة مستفيدة")
        request.beneficiary = request.user.beneficiary
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """
    يسمح فقط لمستخدم دوره manager (الإداري) بالوصول للوحة الإدارية.
    """
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role.name != "manager":
            raise PermissionDenied("هذا الحساب غير مخوّل بالوصول للوحة الإدارية")
        return view_func(request, *args, **kwargs)
    return wrapper