from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


@login_required
def dashboard(request):
    subscriptions = request.user.subscriptions.all()
    context = {
        "today": timezone.localdate(),
        "subscription_count": subscriptions.count(),
        "active_subscription_count": subscriptions.filter(sub_status=True).count(),
        "trial_count": subscriptions.filter(
            sub_status=True,
            trial_status=True,
        ).count(),
        "paid_count": subscriptions.filter(
            sub_status=True,
            trial_status=False,
        ).count(),
        "active_trials": subscriptions.filter(
            sub_status=True,
            trial_status=True,
            trial_end__isnull=False,
        ).order_by("trial_end")[:5],
        "upcoming_subscriptions": subscriptions.filter(
            sub_status=True,
            trial_status=False,
            sub_next__isnull=False,
        ).order_by("sub_next")[:5],
        "recent_subscriptions": subscriptions.order_by("-created_at")[:4],
    }
    return render(request, "dashboard/dashboard.html", context)
