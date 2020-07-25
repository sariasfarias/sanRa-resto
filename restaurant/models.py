from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

"""
Models for restaurant representation
"""


class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    is_ready = models.BooleanField(default=False)
    capacity = models.IntegerField(default=0, null=True, blank=True)
    capacity_percent = models.IntegerField(default=0, null=True, blank=True)
    total_capacity = models.IntegerField(default=0, null=True, blank=True)
    open_lunch = models.TimeField(null=True, blank=True)
    close_lunch = models.TimeField(null=True, blank=True)
    open_dinner = models.TimeField(null=True, blank=True)
    close_dinner = models.TimeField(null=True, blank=True)
    picture = models.CharField(max_length=500, null=True, blank=True)
    telephone = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


# Representing restaurant's menu item
class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    price = models.FloatField(default=0)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ReserveByHour(models.Model):
    capacity = models.IntegerField(default=0)
    capacity_free = models.IntegerField(default=0)
    currently_free = models.BooleanField(default=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.restaurant) + " " + str(self.capacity)+ " "+ str(self.hour)


# Representing restaurant's table
class Table(models.Model):
    number = models.IntegerField()
    row = models.IntegerField()
    column = models.IntegerField()
    people = models.IntegerField(default=0)
    currently_free = models.BooleanField(default=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.restaurant) + " " + str(self.number)


"""
Models for users representation
"""


class Guest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=200, null=True, blank=True)
    name =  models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class Manager(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user.username) + " " + str(self.restaurant.name)


# Friendship between two different users
class Friendship(models.Model):
    user = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="creator")
    friend = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="friend")
    started = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        first_person = self.user.user.get_full_name()
        second_person = self.friend.user.get_full_name()
        return first_person + " and " + second_person


"""
Models for restaurant functionality
"""


class Reservation(models.Model):
    coming = models.DateTimeField()
    leaving = models.DateTimeField(null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    number_guest = models.IntegerField(default=0)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    capacity = models.IntegerField(default=0)
    dni = models.CharField(max_length=20, null=True, blank=True)
    cellphone = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        person = self.full_name
        place = self.restaurant.name
        time = self.coming
        cellphone = ""
        if self.cellphone is not None:
            cellphone = " - " + self.cellphone
        return person + " en " + place + " a las " + str(time) + cellphone
    
    '''def get_finishing_time(self):
        return self.coming + datetime.timedelta(hours=self.duration)
    '''


class ReservedTables(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.reservation) + " table: " + str(self.table)


class Visit(models.Model):
    ending_time = models.DateTimeField('ending time')
    grade = models.IntegerField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.reservation) + " ending: " + str(self.ending_time) + " for: " + str(self.guest)

    def has_ended(self):
        if self.confirmed:
            return timezone.now() > self.ending_time
        else:
            return False