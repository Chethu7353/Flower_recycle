from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core import api_views, views

router = DefaultRouter()
router.register("temples", api_views.TempleViewSet, basename="api-temple")
router.register("flowers", api_views.FlowerViewSet, basename="api-flower")
router.register("submissions", api_views.FlowerSubmissionViewSet, basename="api-submission")
router.register("collections", api_views.CollectionRecordViewSet, basename="api-collection")

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Allauth accounts (OAuth, social account login)
    path("accounts/", include("allauth.urls")),

    # 1. Public Welcome Page & Authentication
    path("", views.welcome, name="welcome"),
    path("home/", views.welcome, name="home"),
    path("login/", views.role_login, name="login"),
    path("login/temple/", views.role_login, {"role": "temple"}, name="login_temple"),
    path("login/collector/", views.role_login, {"role": "collector"}, name="login_collector"),
    path("login/admin/", views.role_login, {"role": "admin"}, name="login_admin"),
    path("logout/", views.logout_view, name="logout"),

    # 2. Temple Owner Module
    path("temple/dashboard/", views.temple_dashboard, name="temple_dashboard"),
    path("temple/submit/", views.temple_submit_flower, name="temple_submit_flower"),
    path("temple/profile/", views.temple_profile, name="temple_profile"),
    path("temple/submissions/<int:pk>/", views.temple_submission_detail, name="temple_submission_detail"),

    # 3. SONPK Collector Module
    path("collector/dashboard/", views.collector_dashboard, name="collector_dashboard"),
    path("collector/submissions/", views.collector_submissions_list, name="collector_submissions_list"),
    path("collector/collect/<int:pk>/", views.collector_record_collection, name="collector_record_collection"),

    # 4. Admin Department Module
    path("admin-dept/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dept/users/", views.admin_users_list, name="admin_users_list"),
    path("admin-dept/users/create/", views.admin_user_create, name="admin_user_create"),
    path("admin-dept/users/<int:pk>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("admin-dept/users/<int:pk>/toggle-status/", views.admin_user_toggle_status, name="admin_user_toggle_status"),
    path("admin-dept/temples/", views.admin_temples_list, name="admin_temples_list"),
    path("admin-dept/temples/create/", views.admin_temple_create, name="admin_temple_create"),
    path("admin-dept/temples/<int:pk>/edit/", views.admin_temple_edit, name="admin_temple_edit"),
    path("admin-dept/temples/<int:pk>/", views.admin_temple_detail, name="admin_temple_detail"),
    path("admin-dept/submissions/", views.admin_submissions_list, name="admin_submissions_list"),
    path("admin-dept/collections/", views.admin_collections_list, name="admin_collections_list"),

    # REST APIs
    path("api/auth/register/", api_views.RegisterAPIView.as_view(), name="api_register"),
    path("api/auth/login/", api_views.LoginAPIView.as_view(), name="api_login"),
    path("api/auth/logout/", api_views.LogoutAPIView.as_view(), name="api_logout"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/dashboard/statistics/", api_views.DashboardStatsAPIView.as_view(), name="api_dashboard_stats"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
