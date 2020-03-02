from api.models import Room
import json

Room.objects.all().delete()

room_data = json.load(open('util/rooms.json', 'r'))

# create new rooms
for room in room_data:
    r = room_data[room]
    coords = r['coordinates'].strip(['(', ')'])
    new_room = Room(id=r['room_id'])
    new_room.title = r['title']
    new_room.description = r['description']
    new_room.x_coord = r['x_coord']
    new_room.y_coord = r['y_coord']
    new_room.elevation = r['elevation']
    new_room.terrain = r['terrain']
    new_room.save()

# connect rooms together
all_rooms = Room.objects.all()

for room in all_rooms:
    for e in room_data[f"{room.id}"]['exits']:
        new_room.connect_rooms(r['exits'][e], e)