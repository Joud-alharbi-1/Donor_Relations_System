# Donor Relations Management System

A system for managing grants and relationships between donor organizations and beneficiary entities at King Abdulaziz University, developed for the Donor Relations Department.

The system was built as a proof of concept and consists of four parts:

1. **Public website** — an informational site with a grant-acceptance journey, donor tier information, and contact/suggestion forms.
2. **Donor portal** — lets each donor view their grants, beneficiaries, impact reports, and donation history.
3. **Beneficiary portal** — lets each beneficiary manage received grants: beneficiary counts, in-kind items, and impact report uploads.
4. **Admin panel** — an internal dashboard for staff to manage donors, beneficiaries, and grants.

## Tech Stack

- Django (backend framework)
- MySQL (database)
- Tailwind CSS (via CDN)
- Alpine.js (frontend interactivity)
- Python 3.14

## Prerequisites

- Python 3.14 or newer
- A running MySQL server, with an empty database named `drms_db`

## Setup

Clone the repository:

```
git clone https://github.com/Joud-alharbi-1/Donor_Relations_System.git
```

Enter the project folder:

```
cd Donor_Relations_System
```

Create a virtual environment:

```
python -m venv venv
```

Activate it:

```
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Create a `.env` file in the project root with your database credentials:

```
DB_NAME=drms_db
DB_USER=root
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=3306
```

Build the database tables:

```
python manage.py migrate
```

Create a superuser account (for internal use via Django Admin only — see **Access & Roles** below):

```
python manage.py createsuperuser
```

Run the server:

```
python manage.py runserver
```

The system will be available at `http://127.0.0.1:8000`.

## Access & Roles

The system has three user roles — donor, beneficiary, and admin (manager) — each with an isolated login flow:

- **Role gateway:** `http://127.0.0.1:8000/accounts/portal-login/` — presents three cards, one per role, each leading to its own dedicated login page.
- **Donor and beneficiary accounts** log in through the gateway and are taken to their respective portal.
- **Admin (manager) accounts** log in through the gateway and are taken to the internal admin panel at `/admin-panel/`.
- **Django Admin** (`/admin/`) is a separate, technical-only entry point used for direct database management (via the superuser account created above). It is independent of the three-role login system and is not linked from anywhere in the user-facing site.

## Project Structure

- **accounts** — users, roles, and the login/logout flow for all three roles
- **entities** — donor and beneficiary organizations
- **grants** — grants and their related data (in-kind items, beneficiary counts, visits, impact reports, news and announcements)
- **pages** — the public website (home, grant acceptance, contact/suggestions)
- **portal** — the donor and beneficiary portals
- **admin_panel** — the internal admin dashboard

## Notes

- The `.env` file is not committed to the repository; it holds sensitive database credentials.
- Some content (donor tier definitions and their benefits, contact information) is defined as constants in the code rather than stored in the database.
- Grant submission and suggestion forms on the public site are sent via email and are not stored in the database.
- Uploaded files (donor logos, impact reports, item attachments) are stored under the local `media/` directory during development.
