from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import SubscriptionForm
from .models import Subscription


class OwnedSubscriptionMixin(LoginRequiredMixin):
    model = Subscription
    context_object_name = "subscription"
    pk_url_kwarg = "sub_id"

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionListView(LoginRequiredMixin, ListView):
    model = Subscription
    context_object_name = "subscriptions"
    template_name = "subscriptions/subscription_list.html"

    def get_queryset(self):
        queryset = Subscription.objects.filter(user=self.request.user)
        query = self.request.GET.get("q", "").strip()
        mode = self.request.GET.get("mode", "")

        if query:
            queryset = queryset.filter(
                Q(sub_name__icontains=query)
                | Q(sub_plan__icontains=query)
                | Q(sub_category__icontains=query)
                | Q(sub_platform__icontains=query)
            )
        if mode == "trial":
            queryset = queryset.filter(trial_status=True)
        elif mode == "paid":
            queryset = queryset.filter(trial_status=False)

        return queryset.order_by(
            "-sub_status",
            "sub_next",
            "sub_name",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_subscriptions = Subscription.objects.filter(user=self.request.user)
        context["active_count"] = all_subscriptions.filter(sub_status=True).count()
        context["inactive_count"] = all_subscriptions.filter(sub_status=False).count()
        context["result_count"] = context["subscriptions"].count()
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_mode"] = self.request.GET.get("mode", "")
        return context


class SubscriptionCreateView(LoginRequiredMixin, CreateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = "subscriptions/subscription_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "เพิ่มบริการสำเร็จ")
        return response

    def get_success_url(self):
        return reverse("subscriptions:list")


class SubscriptionDetailView(OwnedSubscriptionMixin, DetailView):
    template_name = "subscriptions/subscription_detail.html"


class SubscriptionUpdateView(OwnedSubscriptionMixin, UpdateView):
    form_class = SubscriptionForm
    template_name = "subscriptions/subscription_form.html"
    success_message = "แก้ไขบริการสำเร็จ"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

    def get_success_url(self):
        return reverse(
            "subscriptions:detail",
            kwargs={"sub_id": self.object.sub_id},
        )


class SubscriptionContinuePaidView(SubscriptionUpdateView):
    success_message = "เปลี่ยนเป็นบริการแบบชำระเงินสำเร็จ"

    def get_queryset(self):
        return super().get_queryset().filter(trial_status=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["force_service_mode"] = SubscriptionForm.MODE_PAID
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["conversion_mode"] = True
        return context

    def form_valid(self, form):
        form.instance.sub_status = True
        return super().form_valid(form)


class SubscriptionDeactivateView(LoginRequiredMixin, View):
    def post(self, request, sub_id):
        subscription = get_object_or_404(
            Subscription,
            sub_id=sub_id,
            user=request.user,
        )
        subscription.sub_status = False
        subscription.save(update_fields=["sub_status", "updated_at"])
        messages.success(request, "หยุดติดตามบริการนี้แล้ว")
        return redirect("subscriptions:detail", sub_id=subscription.sub_id)


class SubscriptionDeleteView(OwnedSubscriptionMixin, DeleteView):
    template_name = "subscriptions/subscription_confirm_delete.html"
    success_url = reverse_lazy("subscriptions:list")

    def form_valid(self, form):
        messages.success(self.request, "ลบบริการสำเร็จ")
        return super().form_valid(form)
