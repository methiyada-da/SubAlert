from django.urls import path

from .views import (
    SubscriptionContinuePaidView,
    SubscriptionCreateView,
    SubscriptionDeactivateView,
    SubscriptionDeleteView,
    SubscriptionDetailView,
    SubscriptionListView,
    SubscriptionUpdateView,
)


app_name = "subscriptions"

urlpatterns = [
    path("", SubscriptionListView.as_view(), name="list"),
    path("add/", SubscriptionCreateView.as_view(), name="create"),
    path("<int:sub_id>/", SubscriptionDetailView.as_view(), name="detail"),
    path("<int:sub_id>/edit/", SubscriptionUpdateView.as_view(), name="update"),
    path(
        "<int:sub_id>/continue-paid/",
        SubscriptionContinuePaidView.as_view(),
        name="continue_paid",
    ),
    path(
        "<int:sub_id>/deactivate/",
        SubscriptionDeactivateView.as_view(),
        name="deactivate",
    ),
    path("<int:sub_id>/delete/", SubscriptionDeleteView.as_view(), name="delete"),
]
