# run this script in the django shell to create rooms
# copy and paste in sections (separted by comments)

from api.models import Room
import json

Room.objects.all().delete()

room_data = json.load(open('util/rooms.json', 'r'))

# create new rooms
for room in room_data:
    r = room_data[room]
    new_room = Room(id=r['id'])
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
        room.connect_rooms(room_data[f"{room.id}"]['exits'][e], e)
