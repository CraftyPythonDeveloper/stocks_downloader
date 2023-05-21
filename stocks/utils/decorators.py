from django.http import JsonResponse


def allowed_methods(methods: list = None):
    if not methods:
        methods = ["GET"]

    def inner(func):
        def wrapper(request):
            if request.method.lower() in [method.lower() for method in methods]:
                data = func(request)
                return data
            return JsonResponse({"message": "Method not allowed"})

        return wrapper

    return inner
