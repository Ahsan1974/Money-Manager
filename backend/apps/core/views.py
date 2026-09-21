from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Account
from apps.bills.models import Bill, Subscription
from apps.core.models import Notification, Person, Tag, UserProfile
from apps.core.serializers import NotificationSerializer, PersonSerializer, TagSerializer
from apps.core.services.calculators import (
    budget_split,
    convert_currency,
    debt_payoff,
    loan_payment,
    percentage_of,
    savings_projection,
)
from apps.core.services.dashboard import build_dashboard, serialize_decimal
from apps.core.services.insights import generate_insights
from apps.core.services.nl import parse_natural_language
from apps.core.services.recurring import generate_due_notifications, refresh_bill_statuses
from apps.core.services.safe_to_spend import calculate_safe_to_spend
from apps.goals.models import SavingsGoal
from apps.transactions.models import Category, Transaction


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name", required=False)
    currency = serializers.CharField(source="profile.currency", read_only=True)
    currency_symbol = serializers.CharField(source="profile.currency_symbol", read_only=True)
    theme = serializers.CharField(source="profile.theme", read_only=True)
    hide_balance = serializers.BooleanField(source="profile.hide_balance", read_only=True)
    pin_enabled = serializers.BooleanField(source="profile.pin_enabled", read_only=True)
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)
    needs_setup = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "display_name",
            "currency",
            "currency_symbol",
            "theme",
            "hide_balance",
            "pin_enabled",
            "avatar",
            "needs_setup",
        ]

    def get_needs_setup(self, obj):
        return not Account.objects.filter(user=obj).exists()


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "first_name",
            "display_name",
            "avatar",
            "currency",
            "currency_symbol",
            "theme",
            "hide_balance",
            "pin_enabled",
            "lock_after_minutes",
            "emergency_reserve",
            "savings_reserve",
            "obligation_horizon_days",
            "include_upcoming_bills",
            "include_debt_payments",
            "include_goal_reserves",
            "daily_spending_period_days",
            "notify_bills",
            "notify_budgets",
            "notify_subscriptions",
            "notify_goals",
            "notify_unusual",
            "ai_enabled",
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if user_data:
            for key, value in user_data.items():
                setattr(instance.user, key, value)
            instance.user.save()
        return super().update(instance, validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    remember = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user, context=self.context).data
        data["remember"] = attrs.get("remember", True)
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def bootstrap(request):
    return Response({"needs_registration": not User.objects.exists()})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    if User.objects.exists():
        return Response(
            {"error": "This personal workspace already has an owner."},
            status=status.HTTP_403_FORBIDDEN,
        )
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    display_name = (request.data.get("display_name") or username).strip()
    if len(username) < 3:
        return Response({"error": "Choose a username with at least 3 characters."}, status=400)
    if len(password) < 8:
        return Response({"error": "Use a password with at least 8 characters."}, status=400)
    user = User.objects.create_user(username=username, password=password, first_name=display_name)
    user.profile.display_name = display_name
    user.profile.save()
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    token = request.data.get("refresh")
    if token:
        try:
            RefreshToken(token).blacklist()
        except Exception:
            pass
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get("current_password") or ""
    new = request.data.get("new_password") or ""
    if not request.user.check_password(current):
        return Response({"error": "Current password is incorrect."}, status=400)
    try:
        validate_password(new, request.user)
    except Exception as exc:
        return Response({"error": "Please choose a stronger password.", "details": [str(e) for e in exc.error_list] if hasattr(exc, "error_list") else [str(exc)]}, status=400)
    request.user.set_password(new)
    request.user.save()
    return Response({"ok": True})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "GET":
        return Response(ProfileSerializer(profile).data)
    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_pin(request):
    pin = str(request.data.get("pin") or "")
    if len(pin) != 4 or not pin.isdigit():
        return Response({"error": "PIN must be 4 digits."}, status=400)
    profile = request.user.profile
    profile.pin_hash = make_password(f"pin:{pin}")
    profile.pin_enabled = True
    profile.save(update_fields=["pin_hash", "pin_enabled"])
    return Response({"ok": True, "pin_enabled": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_pin(request):
    pin = str(request.data.get("pin") or "")
    profile = request.user.profile
    if not profile.pin_enabled or not profile.pin_hash:
        return Response({"error": "PIN lock is not enabled."}, status=400)
    if not check_password(f"pin:{pin}", profile.pin_hash):
        return Response({"error": "Incorrect PIN."}, status=400)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def disable_pin(request):
    password = request.data.get("password") or ""
    if not request.user.check_password(password):
        return Response({"error": "Password is incorrect."}, status=400)
    profile = request.user.profile
    profile.pin_enabled = False
    profile.pin_hash = ""
    profile.save(update_fields=["pin_enabled", "pin_hash"])
    return Response({"ok": True, "pin_enabled": False})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    year_i = int(year) if year else None
    month_i = int(month) if month else None
    refresh_bill_statuses(request.user)
    generate_due_notifications(request.user)
    payload = build_dashboard(request.user, year_i, month_i)
    payload["insights"] = generate_insights(request.user)
    return Response(serialize_decimal(payload))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def safe_to_spend_view(request):
    return Response(serialize_decimal(calculate_safe_to_spend(request.user)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def insights_view(request):
    return Response(generate_insights(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def parse_entry(request):
    text = request.data.get("text") or ""
    result = parse_natural_language(request.user, text)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_search(request):
    q = (request.query_params.get("q") or "").strip()
    if len(q) < 1:
        return Response({"transactions": [], "accounts": [], "bills": [], "subscriptions": [], "goals": [], "categories": []})
    user = request.user
    txs = Transaction.objects.filter(user=user).filter(
        Q(merchant__icontains=q) | Q(description__icontains=q) | Q(notes__icontains=q)
    ).select_related("account", "category")[:8]
    return Response(
        {
            "transactions": [
                {
                    "id": tx.id,
                    "merchant": tx.merchant or tx.description,
                    "amount": str(tx.amount),
                    "date": tx.transaction_date.isoformat(),
                    "type": tx.transaction_type,
                }
                for tx in txs
            ],
            "accounts": list(Account.objects.filter(user=user, name__icontains=q).values("id", "name", "current_balance")[:6]),
            "bills": list(Bill.objects.filter(user=user, name__icontains=q).values("id", "name", "amount", "due_date")[:6]),
            "subscriptions": list(Subscription.objects.filter(user=user, name__icontains=q).values("id", "name", "price")[:6]),
            "goals": list(SavingsGoal.objects.filter(user=user, name__icontains=q).values("id", "name", "current_amount", "target_amount")[:6]),
            "categories": list(Category.objects.filter(user=user, name__icontains=q).values("id", "name", "icon", "color")[:6]),
        }
    )


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PersonViewSet(viewsets.ModelViewSet):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    pagination_class = None

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"ok": True})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        note = self.get_object()
        note.is_read = True
        note.save(update_fields=["is_read"])
        return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def calculator_view(request):
    kind = request.data.get("kind")
    payload = request.data.get("payload") or {}
    try:
        if kind == "savings":
            data = savings_projection(
                payload.get("monthly_contribution"),
                payload.get("months"),
                payload.get("annual_rate_pct") or 0,
            )
        elif kind == "budget":
            data = budget_split(payload.get("income"), payload.get("allocations") or {})
        elif kind == "loan":
            data = loan_payment(payload.get("principal"), payload.get("annual_rate_pct") or 0, payload.get("months"))
        elif kind == "debt_payoff":
            data = debt_payoff(payload.get("balance"), payload.get("annual_rate_pct") or 0, payload.get("monthly_payment"))
        elif kind == "percent":
            data = percentage_of(payload.get("part"), payload.get("whole"))
        elif kind == "fx":
            data = convert_currency(payload.get("amount"), payload.get("rate") or 1)
        else:
            return Response({"error": "Unknown calculator."}, status=400)
    except Exception:
        return Response({"error": "Please enter valid numbers."}, status=400)
    return Response(serialize_decimal(data))
