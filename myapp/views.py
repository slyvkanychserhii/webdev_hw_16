from django.contrib.auth import authenticate
from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import status, views, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from . import models
from . import serializers
from . import permissions


class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'previous_link': self.get_previous_link(),
            'next_link': self.get_next_link(),
            'results': data
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer

    # http://127.0.0.1:8000/api/categories/count_tasks/
    @action(detail=False, methods=['get'])
    def count_tasks(self, request):
        tasks_by_category = models.Category.objects.annotate(
            task_count=Count('tasks'))
        data = [
            {
                "category_id": category.id,
                "category_name": category.name,
                "task_count": category.task_count
            }
            for category in tasks_by_category
        ]
        return Response(data)


class SubTaskListCreateView(generics.ListCreateAPIView):
    queryset = models.SubTask.objects.all()
    serializer_class = serializers.SubTaskSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Фильтрация по полям status и deadline_lt:
    # http://127.0.0.1:8000/api/subtasks/?status=1
    # http://127.0.0.1:8000/api/subtasks/?deadline__lt=2024-09-27T00:00:00Z
    # http://127.0.0.1:8000/api/subtasks/?deadline__gt=2024-09-27T00:00:00Z
    filterset_fields = {
        'status': ['exact'],
        'deadline': ['exact', 'gt', 'lt'],
    }
    # Поиск по полям title и description:
    # http://127.0.0.1:8000/api/subtasks/?search=subtask_name
    search_fields = ['title', 'description']
    # Сортировка по полю created_at:
    # http://127.0.0.1:8000/api/subtasks/?ordering=created_at
    # Сортировка по полю created_at (по убыванию):
    # http://127.0.0.1:8000/api/subtasks/?ordering=-created_at
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SubTaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.SubTask.objects.all()
    serializer_class = serializers.SubTaskSerializer
    permission_classes = [permissions.IsOwnerOrReadOnly]


class TaskListCreateView(generics.ListCreateAPIView):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Фильтрация по полям status и deadline_lt:
    # http://127.0.0.1:8000/api/tasks/?status=1
    # http://127.0.0.1:8000/api/tasks/?deadline__lt=2024-09-27T00:00:00Z
    # http://127.0.0.1:8000/api/tasks/?deadline__gt=2024-09-27T00:00:00Z
    filterset_fields = {
        'status': ['exact'],
        'deadline': ['exact', 'gt', 'lt'],
    }
    # Поиск по полям title и description:
    # http://127.0.0.1:8000/api/tasks/?search=task_name
    search_fields = ['title', 'description']
    # Сортировка по полю created_at:
    # http://127.0.0.1:8000/api/tasks/?ordering=created_at
    # Сортировка по полю created_at (по убыванию):
    # http://127.0.0.1:8000/api/tasks/?ordering=-created_at
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    permission_classes = [permissions.IsOwnerOrReadOnly]


class TaskStatisticsView(views.APIView):
    def get(self, request):
        data = {}
        data['tasks'] = models.Task.objects.count()
        tasks_by_status = models.Task.objects.values(
            'status').annotate(task_count=Count('*'))
        data['tasks_by_status'] = [
            {
                "status": models.StatusType(status['status']).label,
                "tasks_count": status['task_count']
            }
            for status in tasks_by_status
        ]
        data['tasks_lt_now'] = models.Task.objects.filter(
            deadline__lt=timezone.now()).count()
        return Response(data, status=status.HTTP_200_OK)


class UserSubTaskListView(generics.ListAPIView):
    serializer_class = serializers.SubTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.SubTask.objects.filter(owner=self.request.user)


class UserTaskListView(generics.ListAPIView):
    serializer_class = serializers.TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.Task.objects.filter(owner=self.request.user)


# authentication


class SignupView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.SignupSerializer

    def post(self, request, *args,  **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh_token = RefreshToken.for_user(user)
            refresh_token_str = str(refresh_token)
            refresh_token_exp = refresh_token['exp']
            refresh_token_exp = timezone.datetime.fromtimestamp(
                refresh_token_exp,
                tz=timezone.get_current_timezone())
            access_token = refresh_token.access_token
            access_token_str = str(access_token)
            access_token_exp = access_token['exp']
            access_token_exp = timezone.datetime.fromtimestamp(
                access_token_exp,
                tz=timezone.get_current_timezone())
            data = {
                'username': user.username,
                'email': user.email,
                'refresh_token': refresh_token_str,
                'access_token': access_token_str}
            response = Response(data=data, status=status.HTTP_201_CREATED)
            response.set_cookie(
                'refresh_token',
                refresh_token_str,
                expires=refresh_token_exp,
                httponly=True)
            response.set_cookie(
                'access_token',
                access_token_str,
                expires=access_token_exp,
                httponly=True)
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SigninView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.SigninSerializer

    def post(self, request, *args,  **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh_token = RefreshToken.for_user(user)
            refresh_token_str = str(refresh_token)
            refresh_token_exp = refresh_token['exp']
            refresh_token_exp = timezone.datetime.fromtimestamp(
                refresh_token_exp,
                tz=timezone.get_current_timezone())
            access_token = refresh_token.access_token
            access_token_str = str(access_token)
            access_token_exp = access_token['exp']
            access_token_exp = timezone.datetime.fromtimestamp(
                access_token_exp,
                tz=timezone.get_current_timezone())
            data = {
                'username': user.username,
                'email': user.email,
                'refresh_token': refresh_token_str,
                'access_token': access_token_str}
            response = Response(data=data, status=status.HTTP_200_OK)
            response.set_cookie(
                'refresh_token',
                refresh_token_str,
                expires=refresh_token_exp,
                httponly=True)
            response.set_cookie(
                'access_token',
                access_token_str,
                expires=access_token_exp,
                httponly=True)
            return response
        else:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def signout(request):
    response = Response(status=status.HTTP_204_NO_CONTENT)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
