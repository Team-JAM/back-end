from django.conf.urls import url
from . import api

urlpatterns = [
    url('map', api.map),
    url('get_directions', api.get_directions),
    url('well', api.well)
]