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
import time

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
    starting_room to destination_room. Expected values
    in the request are starting_room, destination_room, and token.
    """
    data = json.loads(request.body)
    starting_room = int(data['starting_room'])
    destination_room = int(data['destination_room'])
    # token = data['token']

    # Create an empty queue
    queue = Queue()
    # Add a path for starting_room_id to the queue
    # paths will contain tuple of (direction, room_id)
    queue.enqueue([(None, starting_room)])
    # Create an empty set to store visited rooms
    visited = set()
    while queue.size() > 0:
        # reorder the queue with dashes counting as a single step
        if queue.size() > 1:
            reorder_queue(queue)
        # Dequeue the first path
        path = queue.dequeue()
        # Grab the last room from the path
        room = path[-1][1]
        # If room is the desination, return the path
        if room == destination_room:
            path_directions = get_pathing(path)
            # travel(path_directions, token)
            # return JsonResponse({'message': "Travel completed."}, safe=True)
            return JsonResponse({'path': path[1:], 'path_directions': path_directions}, safe=True)
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
            # Add recall to room zero unless in or adjacent to room zero (fly instead)
            if room not in {0, 1, 2, 4, 10} and 0 not in visited:
                adjacent_rooms.append(('recall', 0))
            # Add room's warp counterpart to the list of adjacent rooms
            if room < 500 and (room + 500) not in visited:
                adjacent_rooms.append(('warp', room + 500))
            elif room >= 500 and (room - 500) not in visited:
                adjacent_rooms.append(('warp', room - 500))
            # Add adjecent rooms
            if current_room.n_to is not None and current_room.n_to not in visited:
                adjacent_rooms.append(('n', current_room.n_to))
            if current_room.s_to is not None and current_room.s_to not in visited:
                adjacent_rooms.append(('s', current_room.s_to))
            if current_room.e_to is not None and current_room.e_to not in visited:
                adjacent_rooms.append(('e', current_room.e_to))
            if current_room.w_to is not None and current_room.w_to not in visited:
                adjacent_rooms.append(('w', current_room.w_to))
            for next_room in adjacent_rooms:
                queue.enqueue(path + [next_room])
    return JsonResponse({'error': list(visited)}, safe=True)


def get_pathing(path):
    path_directions = []
    next_position = 1

    while next_position < len(path):

        # first, check for a warp command
        if path[next_position][0] == 'warp':
            path_directions.append(['warp'])
            next_position += 1
            continue

        # check for a recall command
        if path[next_position][0] == 'recall':
            path_directions.append(['recall'])
            next_position += 1
            continue

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

def reorder_queue(queue):
    # for each list in the queue
    for path in queue.queue:
        # calcuate the steps and append the number of steps
        steps = 0
        hops = 0
        next_position = 1
        direction = path[next_position][0]
        while next_position < len(path):
            if path[next_position][0] == direction:
                hops += 1
            else:
                break
            if hops > 2:
                next_position += hops
            else:
                next_position += 1
        steps += 1
        path.append(steps)
    # sort lists by last value (steps)
    queue.queue.sort(key=lambda path: path[-1])
    # remove the steps values
    for i in range(queue.size()):
        queue.queue[i] = queue.queue[i][:-1]
    return None

def travel(path_directions, token):
    # # initiate travel mode
    headers = {"Authorization": f"Token {token}"}
    # r = requests.get(base_url + "init/", headers=headers)
    # current_room_id = r.json()['room_id']
    # # set cooldown
    # time_for_next_action = time.time() + r.json()['cooldown']
    time_for_next_action = time.time()

    for instructions in path_directions:
        travel_mode = instructions[0]
        if travel_mode == 'fly' or travel_mode == 'move':
            payload = {'direction': instructions[1], 'next_room_id': instructions[2]}
        elif travel_mode == 'dash':
            payload = {'direction': instructions[1], 'num_rooms': instructions[2], 'next_room_ids': instructions[3]}
        elif travel_mode == 'recall':
            payload = {}
        
        # sleep for cooldown
        time.sleep(max(time_for_next_action - time.time(), 0))
        # move
        # breakpoint()
        r = requests.post(f'{base_url}adv/{travel_mode}/', headers=headers, json=payload)
        # breakpoint()
        # set cooldown
        time_for_next_action = time.time() + r.json()['cooldown']

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

@csrf_exempt
@api_view(['POST'])
def path_no_warp(request):
    """
    Return a list containing the shortest path from
    starting_room to destination_room. Expected values
    in the request are starting_room, destination_room, and token.
    """
    data = json.loads(request.body)
    starting_room = int(data['starting_room'])
    destination_room = int(data['destination_room'])
    # token = data['token']

    # Create an empty queue
    queue = Queue()
    # Add a path for starting_room_id to the queue
    # Avoids using recall - optimal for gathering treasure
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
            # if room 0 IS first step and starting room IS adjacent to room 0
            if path[1][1] == 0 and path[0][1] in {1, 2, 4, 10}:
                # add direction to room 0 from starting room
                if path[0][1] == 1:
                    path[1] = ('e', 0)
                if path[0][1] == 2:
                    path[1] = ('n', 0)
                if path[0][1] == 4:
                    path[1] = ('w', 0)
                if path[0][1] == 10:
                    path[1] = ('s', 0)
            return JsonResponse({'path': path[1:]}, safe=True)
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

