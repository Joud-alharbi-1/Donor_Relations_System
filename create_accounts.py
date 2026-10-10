from accounts.models import Role, User
from entities.models import Donor, Beneficiary

PASSWORD = "ChangeMe123!"

# 1) Roles (safe to re-run)
manager_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
donor_role, _ = Role.objects.get_or_create(name=Role.DONOR)
beneficiary_role, _ = Role.objects.get_or_create(name=Role.BENEFICIARY)

# 2) Admin account (full access to /admin/)
admin_user, created = User.objects.get_or_create(
    username="admin",
    defaults={
        "email": "admin@example.com",
        "role": manager_role,
        "is_staff": True,
        "is_superuser": True,
    },
)
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.role = manager_role
admin_user.set_password(PASSWORD)
admin_user.save()

# 3) Demo donor account (linked to a demo donor entity)
donor_entity, _ = Donor.objects.get_or_create(name_ar="جهة مانحة تجريبية")
donor_user, created = User.objects.get_or_create(
    username="donor1",
    defaults={"email": "donor1@example.com", "role": donor_role, "donor": donor_entity},
)
donor_user.role = donor_role
donor_user.donor = donor_entity
donor_user.set_password(PASSWORD)
donor_user.save()

# 4) Demo beneficiary account (linked to a demo beneficiary entity)
beneficiary_entity, _ = Beneficiary.objects.get_or_create(name_ar="جهة مستفيدة تجريبية", type="college")
beneficiary_user, created = User.objects.get_or_create(
    username="beneficiary1",
    defaults={"email": "beneficiary1@example.com", "role": beneficiary_role, "beneficiary": beneficiary_entity},
)
beneficiary_user.role = beneficiary_role
beneficiary_user.beneficiary = beneficiary_entity
beneficiary_user.set_password(PASSWORD)
beneficiary_user.save()

print("Three demo accounts created:")
print(f" admin        / {PASSWORD}")
print(f" donor1       / {PASSWORD}")
print(f" beneficiary1 / {PASSWORD}")

