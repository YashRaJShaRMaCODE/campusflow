from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "total_marks", "marks_obtained", "date"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter a student name.")
        return value

    def validate(self, attrs):
        total_marks = attrs.get("total_marks")
        marks_obtained = attrs.get("marks_obtained")
        if total_marks is not None and total_marks <= 0:
            raise serializers.ValidationError({"total_marks": "Must be greater than zero."})
        if total_marks is not None and marks_obtained is not None and marks_obtained > total_marks:
            raise serializers.ValidationError({"marks_obtained": "Cannot exceed total marks."})
        return attrs
