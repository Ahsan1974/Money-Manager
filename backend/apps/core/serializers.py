from rest_framework import serializers

from apps.core.models import Notification, Person, Tag, UserProfile


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "notes", "created_at"]
        read_only_fields = ["created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "message", "link", "is_read", "created_at"]
