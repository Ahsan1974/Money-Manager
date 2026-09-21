from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import AccountViewSet, InvestmentViewSet, TransferViewSet
from apps.ai.views import ConversationViewSet, assistant_ask, assistant_confirm
from apps.analytics.views import analytics_view, health_view, net_worth_view, yearly_view
from apps.bills.views import BillViewSet, SubscriptionViewSet
from apps.budgets.views import BudgetViewSet
from apps.core.views import (
    LoginView,
    NotificationViewSet,
    PersonViewSet,
    TagViewSet,
    bootstrap,
    calculator_view,
    change_password,
    dashboard,
    disable_pin,
    global_search,
    insights_view,
    logout_view,
    me,
    parse_entry,
    register,
    safe_to_spend_view,
    set_pin,
    verify_pin,
)
from apps.debts.views import DebtViewSet, LendingViewSet
from apps.goals.views import GoalViewSet
from apps.reports.views import (
    backup_view,
    export_view,
    import_commit,
    import_preview,
    import_upload,
    report_pdf,
    restore_view,
)
from apps.transactions.views import CategoryViewSet, TransactionViewSet

admin.site.site_header = "MONEA"
admin.site.site_title = "MONEA admin"

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("transfers", TransferViewSet, basename="transfer")
router.register("investments", InvestmentViewSet, basename="investment")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")
router.register("goals", GoalViewSet, basename="goal")
router.register("bills", BillViewSet, basename="bill")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("debts", DebtViewSet, basename="debt")
router.register("lending", LendingViewSet, basename="lending")
router.register("tags", TagViewSet, basename="tag")
router.register("people", PersonViewSet, basename="person")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("ai/conversations", ConversationViewSet, basename="ai-conversation")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/bootstrap/", bootstrap),
    path("api/auth/register/", register),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/logout/", logout_view),
    path("api/auth/change-password/", change_password),
    path("api/auth/me/", me),
    path("api/auth/pin/set/", set_pin),
    path("api/auth/pin/verify/", verify_pin),
    path("api/auth/pin/disable/", disable_pin),
    path("api/dashboard/", dashboard),
    path("api/safe-to-spend/", safe_to_spend_view),
    path("api/insights/", insights_view),
    path("api/search/", global_search),
    path("api/parse/", parse_entry),
    path("api/calculator/", calculator_view),
    path("api/analytics/", analytics_view),
    path("api/analytics/yearly/", yearly_view),
    path("api/analytics/health/", health_view),
    path("api/net-worth/", net_worth_view),
    path("api/ai/ask/", assistant_ask),
    path("api/ai/confirm/", assistant_confirm),
    path("api/import/upload/", import_upload),
    path("api/import/<int:pk>/preview/", import_preview),
    path("api/import/<int:pk>/commit/", import_commit),
    path("api/export/", export_view),
    path("api/reports/pdf/", report_pdf),
    path("api/backup/", backup_view),
    path("api/backup/restore/", restore_view),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
