from django.conf.urls import url
from . import api

urlpatterns = [
    url('map', api.map),
]