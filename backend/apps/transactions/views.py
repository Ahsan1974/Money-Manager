import django_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.services.images import compress_image, make_thumbnail
from apps.core.services.ledger import delete_transaction
from apps.core.services.ocr import get_ocr_provider
from apps.transactions.models import Category, Receipt, Transaction
from apps.transactions.serializers import CategorySerializer, ReceiptSerializer, TransactionSerializer


class TransactionFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name="transaction_date", lookup_expr="gte")
    to_date = django_filters.DateFilter(field_name="transaction_date", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    tag = django_filters.NumberFilter(field_name="tags__id")

    class Meta:
        model = Transaction
        fields = ["account", "category", "transaction_type", "status", "payment_method"]


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = None

    def get_queryset(self):
        qs = Category.objects.filter(user=self.request.user)
        if self.action == "list":
            return qs.filter(parent__isnull=True).prefetch_related("children")
        return qs

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.is_system and not category.parent_id:
            return Response({"error": "System categories can be renamed but not removed."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        ids = request.data.get("ids") or []
        for index, pk in enumerate(ids):
            Category.objects.filter(user=request.user, pk=pk).update(sort_order=index)
        return Response({"ok": True})


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filterset_class = TransactionFilter
    search_fields = ["merchant", "description", "notes"]
    ordering_fields = ["transaction_date", "amount", "created_at"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("account", "category")
            .prefetch_related("receipts", "tags")
        )

    def perform_destroy(self, instance):
        delete_transaction(instance)

    @action(detail=True, methods=["post"], url_path="receipt")
    def attach_receipt(self, request, pk=None):
        tx = self.get_object()
        uploaded = request.FILES.get("image")
        if not uploaded:
            return Response({"error": "Please attach an image."}, status=400)
        compressed = compress_image(uploaded)
        uploaded.seek(0)
        thumb = make_thumbnail(uploaded)
        receipt = Receipt.objects.create(
            user=request.user,
            transaction=tx,
            original_name=getattr(uploaded, "name", ""),
        )
        receipt.image.save(compressed.name, compressed, save=False)
        receipt.thumbnail.save("thumb.jpg", thumb, save=True)
        ocr = get_ocr_provider().extract(receipt.image)
        receipt.ocr_payload = {
            "merchant": ocr.merchant,
            "date": ocr.date,
            "total": ocr.total,
            "line_items": ocr.line_items,
            "raw_text": ocr.raw_text,
            "message": ocr.message,
            "available": ocr.available,
            "provider": ocr.provider,
        }
        receipt.save(update_fields=["ocr_payload"])
        return Response(ReceiptSerializer(receipt, context={"request": request}).data, status=201)

    @action(detail=False, methods=["post"], url_path="ocr")
    def ocr_preview(self, request):
        uploaded = request.FILES.get("image")
        if not uploaded:
            return Response({"error": "Please attach an image."}, status=400)
        result = get_ocr_provider().extract(uploaded)
        return Response(
            {
                "merchant": result.merchant,
                "date": result.date,
                "total": result.total,
                "line_items": result.line_items,
                "raw_text": result.raw_text,
                "message": result.message,
                "available": result.available,
                "provider": result.provider,
                "needs_review": True,
            }
        )
