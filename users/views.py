from django.http import JsonResponse

def temp_home(request):
    return JsonResponse({'message': 'Users app is working'})
