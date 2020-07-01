from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from restaurant.models import Restaurant, MenuItem, Reservation, ReserveByHour


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'url', 'username', 'email', 'groups']


class RestaurantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'address', 'picture',
                  'open_lunch', 'open_dinner', 'close_dinner', 'close_lunch']


class MenuItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'restaurant']


class ReserveByHourSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ReserveByHour
        fields = ['id', 'capacity', 'capacity_free', 'currently_free', 'date', 'restaurant']


class ReservationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'coming', 'leaving', 'full_name', 'restaurant', 'number_guest', 'capacity']
