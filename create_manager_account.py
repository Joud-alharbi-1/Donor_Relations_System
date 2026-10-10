from accounts.models import Role, User

PASSWORD = "ChangeMe123!"

manager_role, _ = Role.objects.get_or_create(name=Role.ADMIN)

user, created = User.objects.get_or_create(
    username="admin_demo",
    defaults={"email": "admin@example.com", "role": manager_role},
)
user.role = manager_role
user.set_password(PASSWORD)
user.save()

print("Manager account created:" if created else "Manager account updated:")
print(" username: admin_demo")
print(f" password: {PASSWORD}")

