from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import *
from rest_framework.decorators import api_view
from util.queue import Queue
import json

@csrf_exempt
@api_view(['GET'])
def map(request):
    rooms = Room.objects.all()
    x_max = 26
    y_max = 31
    grid = [[0]*x_max for i in range(y_max)]
    for room in rooms:
        grid[room.y_coord][room.x_coord] = room.to_json()
    return JsonResponse({'map': grid}, safe=True)

@csrf_exempt
@api_view(['POST'])
def get_directions(request):
    """
    Return a list containing the shortest path from
    starting_room to destination_room.
    """
    data = json.loads(request.body)
    starting_room = data['starting_room']
    destination_room = data['destination_room']

    # Create an empty queue
    queue = Queue()
    # Add a path for starting_room_id to the queue
    # paths will contain tuple of (direction, room_id)
    queue.enqueue([(None, starting_room)])
    # Create an empty set to store visited rooms
    visited = set()
    while queue.size() > 0:
        # Dequeue the first path
        path = queue.dequeue()
        # Grab the last room from the path
        room = path[-1][1]
        # If room is the desination, return the path
        if room == destination_room:
            return path[1:]
        # If it has not been visited...
        if room not in visited:
            # Mark it as visited
            visited.add(room)
            # Then add a path all neighbors to the back of the queue
            current_room = Room.objects.get(id=room)
            adjacent_rooms = []
            if current_room.n_to:
                adjacent_rooms.append(('n', current_room.n_to))
            if current_room.s_to:
                adjacent_rooms.append(('s', current_room.n_to))
            if current_room.e_to:
                adjacent_rooms.append(('e', current_room.n_to))
            if current_room.w_to:
                adjacent_rooms.append(('w', current_room.n_to))
            for next_room in adjacent_rooms:
                queue.enqueue(path + [next_room])
