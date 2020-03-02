from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import *
from rest_framework.decorators import api_view
import json

@csrf_exempt
@api_view(['GET'])
def map(request):
    rooms = Room.objects.all()
    x_max = 19
    y_max = 9
    grid = [[0]*x_max for i in range(y_max)]
    for room in rooms:
        grid[room.y_coord][room.x_coord] = room.toJSON()
    return JsonResponse({'map': grid}, safe=True)