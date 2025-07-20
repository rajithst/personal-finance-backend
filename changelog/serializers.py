from rest_framework import serializers

from changelog.models import ChangeLog


class ChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeLog
        fields = [
            'id', 'changed_by', 'action', 'section', 'object_id', 'changelog', 'timestamp'
        ]

    changed_by = serializers.SerializerMethodField(method_name='get_changed_by')

    def get_changed_by(self, obj):
        if obj.user:
            return obj.user.first_name + ' ' + obj.user.last_name
        return 'Unknown User'
