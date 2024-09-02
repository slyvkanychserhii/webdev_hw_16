from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken


class JWTAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Получаем токены из куков
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        # Проверка наличия и валидности access-токена
        if access_token:
            try:
                # Проверяем access-токен
                # Если токен истёк или имеет другой вид проблемы, 
                # попытка создать объект AccessToken выбросит исключение.
                AccessToken(access_token)
                # Когда в middleware добавляется строка 
                # request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}', 
                # она имитирует ситуацию, как будто клиент отправил запрос с этим заголовком.
                # DRF автоматически обрабатывает этот заголовок на этапе аутентификации, 
                # извлекая токен для проверки подлинности пользователя.
                # Класс JWTAuthentication из rest_framework_simplejwt отвечает за обработку 
                # заголовка Authorization, который начинается с Bearer.
                # Когда JWTAuthentication видит заголовок Authorization: Bearer <access_token>, он:
                # - Извлекает токен из заголовка.
                # - Декодирует его и проверяет подпись.
                # - Извлекает информацию о пользователе из токена (например, user_id).
                # - Аутентифицирует пользователя, ассоциируя его с объектом request.user.
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            except TokenError:
                # Если access-токен недействителен, проверяем refresh-токен
                if refresh_token:
                    try:
                        # Проверяем и декодируем refresh-токен
                        refresh_token_obj = RefreshToken(refresh_token)
                        # Создаем новый access-токен
                        new_access_token = refresh_token_obj.access_token
                        request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                        request.new_access_token = new_access_token
                    except TokenError:
                        pass
        else:
            # Если нет access-токена, но есть refresh-токен, создаем новый access-токен
            if refresh_token:
                try:
                    # Проверяем и декодируем refresh-токен
                    refresh_token_obj = RefreshToken(refresh_token)
                    # Создаем новый access-токен
                    new_access_token = refresh_token_obj.access_token
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                    request.new_access_token = new_access_token
                except TokenError:
                    pass

    def process_response(self, request, response):
        # Если был создан новый access-токен, добавляем его в куки
        if hasattr(request, 'new_access_token'):
            new_access_token = request.new_access_token
            new_access_token_exp = new_access_token['exp']
            new_access_token_exp = timezone.datetime.fromtimestamp(
                new_access_token_exp,
                tz=timezone.get_current_timezone())
            response.set_cookie(
                'access_token', new_access_token,
                expires=new_access_token_exp, httponly=True)
        return response
