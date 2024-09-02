from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from . import models


def validate_deadline(value):
    if value < timezone.now():
        raise serializers.ValidationError(
            "The deadline cannot be in the past")
    return value


class CategorySerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        name = validated_data.get('name')
        if models.Category.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                'A category with this name already exists')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        pk = instance.pk
        if models.Category.objects.filter(name=name).exclude(pk=pk).exists():
            raise serializers.ValidationError(
                'A category with this name already exists')
        return super().update(instance, validated_data)

    class Meta:
        model = models.Category
        fields = '__all__'


class SubTaskSerializer(serializers.ModelSerializer):
    deadline = serializers.DateTimeField(
        required=False,
        validators=[validate_deadline])

    class Meta:
        model = models.SubTask
        fields = '__all__'
        read_only_fields = ['created_at', 'owner']


class TaskSerializer(serializers.ModelSerializer):
    deadline = serializers.DateTimeField(
        required=False,
        validators=[validate_deadline])
    sub_tasks = SubTaskSerializer(
        read_only=True,
        many=True)

    class Meta:
        model = models.Task
        fields = '__all__'
        read_only_fields = ['created_at', 'owner']


# authentication


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''))
        return user


class SigninSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
