"""Root URL configuration for the ER Triage project.

The project file wires two things: the Django admin, and the `triage` app's own
URLs (included under the root). Lesson 6 adds one more `include()` line here for
the new `dashboard` app.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("triage.urls")),
    # Lesson 6 adds the dashboard app's URLs here:
    # path("dashboard/", include("dashboard.urls")),
]
