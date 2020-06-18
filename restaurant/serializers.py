from django.contrib.auth.models import User
from rest_framework import serializers

from restaurant.models import Restaurant, MenuItem, Reservation


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class RestaurantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'address']


class MenuItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'restaurant']


class ReserveByHourSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['capacity', 'currently_free', 'hour', 'restaurant']


class ReservationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Reservation
        fields = ['coming', 'duration', 'guest', 'restaurant', 'number_guest']
