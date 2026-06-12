"""URL routes for the triage app.

Each route maps a URL to a view and gives it a *name* (the second argument to
`path`). Templates and `redirect()` calls refer to these names, never to the raw
URL string — so you can change a URL in one place.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.doctor_queue_view, name="doctor_queue"),
    path("triage/new", views.nurse_form_view, name="nurse_form"),
    path("triage/<int:event_id>/confirm", views.triage_confirmation_view, name="triage_confirmation"),
    path("triage/<int:event_id>", views.patient_detail_view, name="patient_detail"),
]
