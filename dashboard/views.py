from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    subscriptions = request.user.subscriptions.all()
    context = {
        "subscription_count": subscriptions.count(),
        "active_subscription_count": subscriptions.filter(sub_status=True).count(),
        "upcoming_subscriptions": subscriptions.filter(sub_status=True).order_by(
            "sub_next"
        )[:5],
    }
    return render(request, "dashboard/dashboard.html", context)
