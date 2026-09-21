from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers

from apps.ai.engine import chat, confirm_draft_transaction
from apps.ai.models import AIConversation, AIMessage


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ["id", "role", "content", "metadata", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = ["id", "title", "created_at", "updated_at", "messages"]


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    queryset = AIConversation.objects.all()
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user).prefetch_related("messages")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def message(self, request, pk=None):
        conversation = self.get_object()
        text = (request.data.get("message") or "").strip()
        if not text:
            return Response({"error": "Please enter a question."}, status=400)
        result = chat(request.user, text, conversation)
        return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assistant_ask(request):
    text = (request.data.get("message") or "").strip()
    if not text:
        return Response({"error": "Please enter a question."}, status=400)
    conversation_id = request.data.get("conversation_id")
    conversation = None
    if conversation_id:
        conversation = AIConversation.objects.filter(user=request.user, pk=conversation_id).first()
    return Response(chat(request.user, text, conversation))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assistant_confirm(request):
    draft = request.data.get("draft") or {}
    if not draft.get("account") or not draft.get("amount"):
        return Response({"error": "This draft is incomplete."}, status=400)
    tx = confirm_draft_transaction(request.user, draft)
    return Response({"ok": True, "transaction_id": tx.id})
