from django.db import models

class Room(models.Model):
    title = models.CharField(max_length=50, default="DEFAULT TITLE")
    description = models.CharField(max_length=500, default="DEFAULT DESCRIPTION")
    coordinates = models.CharField(max_length=32, default="()")
    n_to = models.IntegerField(blank=True, null=True)
    s_to = models.IntegerField(blank=True, null=True)
    e_to = models.IntegerField(blank=True, null=True)
    w_to = models.IntegerField(blank=True, null=True)
    elevation = models.IntegerField(default=0)
    terrain = models.CharField(max_length=32, default="NORMAL")

    def exits(self):
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