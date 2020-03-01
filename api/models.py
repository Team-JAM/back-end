from django.db import models

class Room(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=50, default="DEFAULT TITLE")
    description = models.CharField(max_length=500, default="DEFAULT DESCRIPTION")
    x_coord = models.IntegerField(default=0)
    y_coord = models.IntegerField(default=0)
    n_to = models.IntegerField(blank=True, null=True)
    s_to = models.IntegerField(blank=True, null=True)
    e_to = models.IntegerField(blank=True, null=True)
    w_to = models.IntegerField(blank=True, null=True)
    elevation = models.IntegerField(default=0)
    terrain = models.CharField(max_length=32, default="NORMAL")

    def connect_rooms(self, destinationRoom, direction):
        destinationRoomID = destinationRoom.id
        try:
            destinationRoom = Room.objects.get(id=destinationRoomID)
        except Room.DoesNotExist:
            print("That room does not exist")
        else:
            if direction == "n":
                self.n_to = destinationRoomID
                destinationRoom.s_to = self.id
            elif direction == "s":
                self.s_to = destinationRoomID
                destinationRoom.n_to = self.id
            elif direction == "e":
                self.e_to = destinationRoomID
                destinationRoom.w_to = self.id
            elif direction == "w":
                self.w_to = destinationRoomID
                destinationRoom.e_to = self.id
            else:
                print("Invalid direction")
                return
            self.save()
            destinationRoom.save()

    def get_exits(self):
        exits = []
        if self.n_to is not None:
            exits.append("n")
        if self.s_to is not None:
            exits.append("s")
        if self.e_to is not None:
            exits.append("e")
        if self.w_to is not None:
            exits.append("w")
        return exits

    def init_exits(self, exit_list):
        # -1 signifies unexplored room, otherwise null if direction does not exist
        if 'n' in exit_list:
            self.n_to = -1
        if 's' in exit_list:
            self.s_to = -1
        if 'e' in exit_list:
            self.e_to = -1
        if 'w' in exit_list:
            self.w_to = -1
        self.save()