from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import NetWorthSnapshot
from apps.analytics.services import analytics_overview, health_indicators, yearly_review
from apps.core.services.dashboard import serialize_decimal
from apps.core.services.networth import compute_net_worth, snapshot_net_worth


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics_view(request):
    today = timezone.localdate()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)
    return Response(serialize_decimal(analytics_overview(request.user, year, month)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def yearly_view(request):
    today = timezone.localdate()
    year = int(request.query_params.get("year") or today.year)
    return Response(serialize_decimal(yearly_review(request.user, year)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health_view(request):
    today = timezone.localdate()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)
    return Response(serialize_decimal(health_indicators(request.user, year, month)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def net_worth_view(request):
    snapshot_net_worth(request.user)
    data = compute_net_worth(request.user)
    history = list(
        NetWorthSnapshot.objects.filter(user=request.user).order_by("snapshot_date").values(
            "snapshot_date", "assets", "liabilities", "net_worth"
        )
    )
    data["history"] = [
        {
            "date": row["snapshot_date"].isoformat(),
            "assets": str(row["assets"]),
            "liabilities": str(row["liabilities"]),
            "net_worth": str(row["net_worth"]),
        }
        for row in history
    ]
    return Response(serialize_decimal(data))
