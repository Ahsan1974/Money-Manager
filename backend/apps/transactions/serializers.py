from rest_framework import serializers

from apps.core.models import Tag
from apps.core.services.images import compress_image, make_thumbnail
from apps.core.services.ledger import create_transaction, delete_transaction, update_transaction
from apps.transactions.models import Category, Receipt, Transaction


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "icon",
            "color",
            "kind",
            "sort_order",
            "is_system",
            "children",
        ]
        read_only_fields = ["is_system"]

    def get_children(self, obj):
        if obj.parent_id:
            return []
        qs = obj.children.all().order_by("sort_order", "name")
        return CategorySerializer(qs, many=True).data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "image", "thumbnail", "original_name", "ocr_payload", "created_at"]
        read_only_fields = ["thumbnail", "ocr_payload", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", many=True, queryset=Tag.objects.all(), required=False
    )
    receipts = ReceiptSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "account_name",
            "category",
            "category_name",
            "category_icon",
            "category_color",
            "amount",
            "transaction_type",
            "merchant",
            "description",
            "transaction_date",
            "notes",
            "currency",
            "status",
            "payment_method",
            "transfer",
            "tag_ids",
            "receipts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["transfer", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["tag_ids"].queryset = Tag.objects.filter(user=request.user)

    def validate_account(self, account):
        if account.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Account not found.")
        return account

    def validate_tag_ids(self, tags):
        user = self.context["request"].user
        for tag in tags:
            if tag.user_id != user.id:
                raise serializers.ValidationError("Tag not found.")
        return tags

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        tx = create_transaction(user=self.context["request"].user, **validated_data)
        if tags:
            tx.tags.set(tags)
        return tx

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        if tags is not None:
            validated_data["tag_ids"] = [tag.id for tag in tags]
        return update_transaction(instance, **validated_data)
