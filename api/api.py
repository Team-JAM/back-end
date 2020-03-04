from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import *
from rest_framework.decorators import api_view
from util.queue import Queue
from decouple import config
from util.ls8 import decode
import json
import requests

import pusher

pusher_client = pusher.Pusher(
  app_id=config('PUSHER_APP_ID'),
  key=config('PUSHER_KEY'),
  secret=config('PUSHER_SECRET'),
  cluster=config('PUSHER_CLUSTER'),
  ssl=True
)

# example pusher trigger - channel - event - JSON data
# pusher_client.trigger(f'channel-{token}', 'move', {'room_id': room_id})

base_url = 'https://lambda-treasure-hunt.herokuapp.com/api/'

@csrf_exempt
@api_view(['GET'])
def map(request):
    rooms = Room.objects.all().order_by('id')
    x_max = 32
    y_max = 32
    offset = 45
    grid = [[None]*x_max for i in range(y_max)]
    dark_grid = [[None]*x_max for i in range(y_max)]
    rooms_json = {}
    for i in range(500):
        room = rooms[i]
        grid[room.y_coord - offset][room.x_coord - offset] = room.to_json(offset)
        rooms_json[room.id] = room.to_json(offset)
    for i in range(500, 1000):
        room = rooms[i]
        dark_grid[room.y_coord - offset][room.x_coord - offset] = room.to_json(offset)
        rooms_json[room.id] = room.to_json(offset)
    
    return JsonResponse({'map': grid, 'dark_map': dark_grid, 'rooms': rooms_json}, safe=True)

@csrf_exempt
@api_view(['POST'])
def get_directions(request):
    """
    Return a list containing the shortest path from
    starting_room to destination_room.
    """
    data = json.loads(request.body)
    starting_room = int(data['starting_room'])
    destination_room = int(data['destination_room'])

    # Create an empty queue
    queue = Queue()
    # Add a path for starting_room_id to the queue
    # Add a second option that recalls to room zero first
    # paths will contain tuple of (direction, room_id)
    queue.enqueue([(None, starting_room)])
    queue.enqueue([(None, starting_room), (None, 0)])
    # Create an empty set to store visited rooms
    visited = set()
    while queue.size() > 0:
        # Dequeue the first path
        path = queue.dequeue()
        # Grab the last room from the path
        room = path[-1][1]
        # If room is the desination, return the path
        if room == destination_room:
            path_directions = get_pathing(path)
            return JsonResponse({'path': path_directions}, safe=True)
        # If it has not been visited...
        if room not in visited:
            # Mark it as visited
            visited.add(room)
            # Then add a path all neighbors to the back of the queue
            try:
                current_room = Room.objects.get(id=room)
            except Room.DoesNotExist:
                return JsonResponse({'error': f"Room {room} does not exist", 'path': path}, safe=True)
            adjacent_rooms = []
            if current_room.n_to is not None:
                adjacent_rooms.append(('n', current_room.n_to))
            if current_room.s_to is not None:
                adjacent_rooms.append(('s', current_room.s_to))
            if current_room.e_to is not None:
                adjacent_rooms.append(('e', current_room.e_to))
            if current_room.w_to is not None:
                adjacent_rooms.append(('w', current_room.w_to))
            for next_room in adjacent_rooms:
                queue.enqueue(path + [next_room])
    return JsonResponse({'error': list(visited)}, safe=True)


def get_pathing(path):
    path_directions = []
    next_position = 1

    # check if room zero is first step and starting room not adjacent to room 0
    if path[1][1] == 0 and path[0][1] not in {1, 2, 4, 10}:
        # if so, start with recall
        path_directions.append(['recall'])
        next_position += 1

    while next_position < len(path):

        # check if there are enough steps for a dash
        direction = path[next_position][0]
        hops = 0
        for i in range(next_position , len(path)):
            if path[i][0] == direction:
                hops += 1
            else:
                break
        if hops > 2:
            next_room_ids = [str(path[i][1]) for i in range(next_position, next_position + hops)]
            dash = ('dash', direction, str(hops), ','.join(next_room_ids))
            path_directions.append(dash)
            next_position += hops
            continue

        # check if flying is called for (next room is not a cave)
        try:
            next_room = Room.objects.get(id=path[next_position][1])
        except Room.DoesNotExist:
            return JsonResponse({'error': f"Room {next_room} does not exist", 'path': path}, safe=True)
        # if no, move; if so, fly
        path[next_position] = list(path[next_position])
        path[next_position][1] = str(path[next_position][1])
        if next_room.terrain == 'CAVE':
            path_directions.append(['move'] + path[next_position])
        else:
            path_directions.append(['fly'] + path[next_position])
        next_position += 1
        
    
    return path_directions

@csrf_exempt
@api_view(['POST'])
def well(request):
    data = json.loads(request.body)
    token = data['token']
    headers = {"Authorization": f"Token {token}"}

    # examine well
    payload = {"name": "well"}
    r = requests.post(base_url + 'adv/examine/', headers=headers, json=payload)

    description = r.json()['description']

    _, message = description.split('\n\n')

    with open('util/wishing_well.ls8', 'w') as f:
        f.write(message)

    # decode message
    message = decode()

    return JsonResponse({'message': message, 'room': r.json() }, safe=True)
