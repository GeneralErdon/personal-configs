"""
                 ____  _                           _   _       __      _     _ 
                |  _ \(_) __ _ _ __   __ _  ___   | | | |_ __  / _| ___| | __| |
                | | | | |/ _` | '_ \ / _` |/ _ \  | | | | '_ \| |_ / _ \ |/ _` |
                | |_| | | (_| | | | | (_| | (_) | | |_| | | | |  _|  __/ | (_| |
                |____/|_|\__,_|_| |_|\__, |\___/   \___/|_| |_|_|  \___|_|\__,_|
                                     |___/                                      

Este archivo contiene la configuración para Django Unfold, una biblioteca de interfaz de usuario
para el panel de administración de Django.

Aquí se definen las configuraciones específicas de Django Unfold, incluyendo:

- UNFOLD: Un diccionario con las configuraciones principales de Unfold.
- JAZZMIN_SETTINGS: Configuraciones adicionales para personalizar la apariencia del panel de administración.

Ajusta estas configuraciones según las necesidades específicas de tu proyecto y la apariencia
deseada para tu panel de administración.
"""
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Configuración principal de Django Unfold
UNFOLD = {
    "SITE_TITLE": "Alfanar",
    "SITE_HEADER": "Alfanar Admin Site",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("assets/alfanar_energia_logo-removebg-preview.png"),
        "dark": lambda request: static("assets/alfanar_energia_logo-removebg-preview.png"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("assets/alfanar_energia_logo-removebg-preview.png"),
        "dark": lambda request: static("assets/alfanar_energia_logo-removebg-preview.png"),
    },
    "SITE_SYMBOL": "people",  # HR-related icon
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    # "ENVIRONMENT": "alfanar_hr.utils.get_environment",
    # "DASHBOARD_CALLBACK": "alfanar_hr.utils.dashboard_callback",
    # "LOGIN": {
    #     "image": lambda request: static("assets/login_background.jpg"),
    #     "redirect_after": lambda request: reverse_lazy("admin:index"),
    # },
    # "STYLES": [
    #     lambda request: static("css/alfanar_admin.css"),
    # ],
    # "SCRIPTS": [
    #     lambda request: static("js/alfanar_admin.js"),
    # ],
    "COLORS": {
        "primary": {
            "50": "236 253 245",
            "100": "209 250 229",
            "200": "167 243 208",
            "300": "110 231 183",
            "400": "52 211 153",
            "500": "16 185 129",
            "600": "5 150 105",
            "700": "4 120 87",
            "800": "6 95 70",
            "900": "6 78 59",
            "950": "2 44 34",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "es": "🇪🇸",
            }
        }
    },
    "SIDEBAR":{
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("HR Management"),
                "icon": "manage_accounts",
                "collapsible": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    # {
                    #     "title": _("Employees"),
                    #     "icon": "people",
                    #     "link": reverse_lazy("admin:employees_employee_changelist"),
                    # },
                    # {
                    #     "title": _("Departments"),
                    #     "icon": "account_tree",
                    #     "link": reverse_lazy("admin:company_department_changelist"),
                    # },
                ],
            },
            {
                "title": _("Company Management"),
                "icon": "business",
                "collapsible": True,
                "items": [
                    {
                        "title": _("Companies"),
                        "icon": "business",
                        "link": reverse_lazy("admin:company_company_changelist"),
                    },
                    {
                        "title": _("Departments"),
                        "icon": "account_tree",
                        "link": reverse_lazy("admin:company_department_changelist"),
                    },
                    {
                        "title": _("Titles"),
                        "icon": "badge",
                        "link": reverse_lazy("admin:company_title_changelist"),
                    },
                    {
                        "title": _("Legal Organizations"),
                        "icon": "description",
                        "link": reverse_lazy("admin:company_legalorg_changelist"),
                    },
                ],
            },
            {
                "title": _("Vacation Management"),
                "icon": "beach_access",
                "collapsible": True,
                "items": [
                    # {
                    #     "title": _("Vacation Requests"),
                    #     "icon": "event_available",
                    #     "link": reverse_lazy("admin:vacation_vacation_changelist"),
                    # },
                    {
                        "title": _("Vacation Periods"),
                        "icon": "date_range",
                        "link": reverse_lazy("admin:vacation_vacationperiod_changelist"),
                    },
                    {
                        "title": _("Non-Working Days"),
                        "icon": "event_busy",
                        "link": reverse_lazy("admin:vacation_noworkingcalendar_changelist"),
                    },
                    {
                        "title": _("Vacation Defaults"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:vacation_vacationrecorddefaults_changelist"),
                    }
                ],
            },
            # {
            #     "title": _("Payment"),
            #     "icon": "payments",
            #     "collapsible": True,
            #     "items": [
            #         # {
            #         #     "title": _("Employee Banks"),
            #         #     "icon": "account_balance",
            #         #     "link": reverse_lazy("admin:payment_bank_changelist"),
            #         # },
            #     ],
            # },
            {
                "title": _("Users and Permissions"),
                "icon": "settings",
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:users_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
            {
                "title": _("Employee Management"),
                "icon": "people",
                "collapsible": True,
                "items": [
                    {
                        "title": _("Employees"),
                        "icon": "person",
                        "link": reverse_lazy("admin:employees_employee_changelist"),
                    },
                    {
                        "title": _("Nationalities"),
                        "icon": "flag",
                        "link": reverse_lazy("admin:employees_nationality_changelist"),
                    },
                    {
                        "title": _("Company Employees"),
                        "icon": "business_center",
                        "link": reverse_lazy("admin:employees_companyemployee_changelist"),
                    },
                    {
                        "title": _("Employee Status"),
                        "icon": "assignment_ind",
                        "link": reverse_lazy("admin:employees_status_changelist"),
                    },
                    {
                        "title": _("Emergency Contacts"),
                        "icon": "contact_phone",
                        "link": reverse_lazy("admin:employees_emergencycontact_changelist"),
                    },
                    {
                        "title": _("Terminations"),
                        "icon": "cancel",
                        "link": reverse_lazy("admin:employees_termination_changelist"),
                    },
                    {
                        "title": _("Evaluations"),
                        "icon": "star_rate",
                        "link": reverse_lazy("admin:employees_evaluation_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "vacation.vacation",
            ],
            "items": [
                {
                    "title": _("Pending Requests"),
                    "link": "/api/v1/admin/vacation/vacation/?status__exact=P",
                },
                {
                    "title": _("Approved Requests"),
                    "link": "/api/v1/admin/vacation/vacation/?status__exact=A",
                },
                {
                    "title": _("Rejected Requests"),
                    "link": "/api/v1/admin/vacation/vacation/?status__exact=R",
                },
            ],
        },
    ],
}

# You need to implement these functions in alfanar_hr/utils.py
"""
def get_environment(request):
    # Implement logic to determine the current environment
    return ["Production", "danger"]  # or ["Development", "warning"], etc.

def dashboard_callback(request, context):
    # Add custom data to the dashboard context
    context.update({
        "total_employees": Employee.objects.count(),
        "pending_vacations": Vacation.objects.filter(status='P').count(),
        # Add more relevant data for your dashboard
    })
    return context
"""
