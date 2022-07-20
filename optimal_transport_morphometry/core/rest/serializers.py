from rest_framework import serializers


class LimitOffsetSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)
