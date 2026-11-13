from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ["id", "name", "total_marks", "marks_obtained", "percentage", "date"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter a student name.")
        return value

    def validate(self, attrs):
        total_marks = attrs.get("total_marks", getattr(self.instance, "total_marks", None))
        marks_obtained = attrs.get("marks_obtained", getattr(self.instance, "marks_obtained", None))
        if total_marks is not None and total_marks <= 0:
            raise serializers.ValidationError({"total_marks": "Must be greater than zero."})
        if total_marks is not None and marks_obtained is not None and marks_obtained > total_marks:
            raise serializers.ValidationError({"marks_obtained": "Cannot exceed total marks."})
        return attrs

    def get_percentage(self, student):
        return round(student.marks_obtained * 100 / student.total_marks, 2)
