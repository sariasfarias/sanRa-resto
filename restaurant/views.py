from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Guest, Manager, Table, MenuItem, Restaurant, Visit, Reservation, Friendship, ReservedTables, \
    ReserveByHour
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime as dt
import datetime
import pytz
from django.db import transaction
from datetime import datetime, timedelta, date

# Homepage
from .serializers import RestaurantSerializer, MenuItemSerializer, ReserveByHourSerializer, ReservationSerializer


def index(request):
    return render(request, 'restaurant/index.html')


# User login
def login(request):
    if request.method == 'POST':
        # collecting form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        # checking for user first
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # check if it is quest or manager
                # search for guest
                guest = Guest.objects.all()
                for g in guest:
                    if g.user == user:
                        auth_login(request, user)
                        return HttpResponseRedirect(reverse('restaurant:guest', args=(g.id,)))
                # search for manager
                managers = Manager.objects.all()
                for m in managers:
                    if m.user == user:
                        auth_login(request, user)
                        # return HttpResponseRedirect(reverse('restaurant:manager', args=(m.id,)))
                        return HttpResponseRedirect(reverse('restaurant:restaurants-list'))
            else:
                return render(request, 'restaurant/index.html', {
                    'error_message': "Account is not activated!"
                })
        else:
            return render(request, 'restaurant/index.html', {
                'error_message': "Wrong Email address or Password!"
            })


# User logout
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('restaurant:index'))


# User register form
def register(request):
    return render(request, 'restaurant/register.html')


def registration(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        # check password equality
        if password1 == password2:
            users = User.objects.all()
            for u in users:
                if u.username == username:
                    return render(request, 'restaurant/register.html', context={
                        'error_message': "User already exists!"
                    })
            # user does not exist, create new
            new_user = User.objects.create_user(username, username, password1)
            new_user.is_staff = False
            new_user.is_active = False
            new_user.is_superuser = False
            new_user.save()
            # create activation link
            new_user_id = str(new_user.id)
            link = "http://127.0.0.1:8000/restaurant/activation/" + new_user_id + "/"
            message_text = "Click on the following link to complete your registration\n\n" + link
            # sending email
            send_mail('Restaurant - Profile Activation', message_text, 'vdragan1993@gmail.com', [new_user.username],
                      fail_silently=False)
            # creating guest object
            new_guest = Guest.objects.create(user=new_user)
            new_user.save()
            print("Successful! Guest inserted: " + str(new_guest))

            # back on page
            return render(request, 'restaurant/register.html', context={
                'info_message': "Account created successfully. Email with activation link was sent!"
            })
        else:
            return render(request, 'restaurant/register.html', context={
                'error_message': "Password wasn't repeated correctly!"
            })


# User activation
def activation(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user is not None:
        user.is_active = True
        user.save()
        return render(request, 'restaurant/index.html', context={
            'info_message': "Account successfully activated!"
        })
    else:
        return render(request, 'restaurant/index.html', context={
            'error_message': "Error with activation link!"
        })


"""Manager pages"""


# Manager's default page
@login_required(login_url='/')
def manager(request, manager_id, restaurant_id):
    this_manager = get_object_or_404(Manager, pk=manager_id)
    restaurant = Restaurant.objects.get(pk=restaurant_id)
    return render(request, 'restaurant/manager.html', {
        'manager': this_manager,
        'restaurant': restaurant,
    })


# Manager's profile page
@login_required(login_url='/')
def profiling(request, manager_id):
    this_manager = get_object_or_404(Manager, pk=manager_id)
    return render(request, 'restaurant/manager_profile.html', {
        'manager': this_manager
    })


# Update Manager's profile
@login_required(login_url='/')
def updating(request, manager_id):
    this_manager = get_object_or_404(Manager, pk=manager_id)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        updated_manager = Manager.objects.get(pk=manager_id)
        # update profile
        updated_user = updated_manager.user
        if first_name:
            updated_user.first_name = first_name
            updated_user.save()
        if last_name:
            updated_user.last_name = last_name
            updated_user.save()

        username = request.POST.get('username')
        if username:
            updated_user.username = username
            updated_user.save()

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password2:
            if password1 == password2:
                # update password if changed
                if password1 != '':
                    updated_user.set_password(password1)
                    updated_user.save()
            else:
                return render(request, 'restaurant/manager_profile.html', context={
                    'manager': this_manager,
                    'error_message': "New password wasn't repeated correctly!"
                })
        print("Success! Updated Manager: " + str(updated_manager))
        return HttpResponseRedirect(reverse('restaurant:profiling', args=(manager_id,)))


# Manager's page for menu setting
@login_required(login_url='/')
def menu(request, restaurant_id, manager_id):
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=this_restaurant)
    this_manager = Manager.objects.get(pk=manager_id)
    return render(request, 'restaurant/menu.html', {
        'manager': this_manager,
        'restaurant': this_restaurant,
        'menu': menu_items
    })


# Deleting menu item from restaurant
@login_required(login_url='/')
def remove(request, item_id, restaurant_id, manager_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    item.delete()
    return HttpResponseRedirect(reverse('restaurant:menu', args=(restaurant_id, manager_id,)))


# Insert menu item for restaurant
@login_required(login_url='/')
def insert(request, restaurant_id, manager_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price'))
        this_restaurant = Restaurant.objects.get(pk=restaurant_id)

        mi = MenuItem.objects.create(name=name, description=description, price=price, restaurant=this_restaurant)
        mi.save()
        print("Success. Inserted MenuItem: " + str(mi))

        return HttpResponseRedirect(reverse('restaurant:menu', args=(restaurant_id, manager_id,)))


# show edit menu item for restaurant
@login_required(login_url='/')
def edit(request, item_id, restaurant_id, manager_id):
    this_item = get_object_or_404(MenuItem, pk=item_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_manager = get_object_or_404(Manager, pk=manager_id)
    menu_items = MenuItem.objects.filter(restaurant=this_restaurant)
    return render(request, 'restaurant/menuedit.html', context={
        'manager': this_manager,
        'restaurant': this_restaurant,
        'menu': menu_items,
        'edition': this_item
    })


# save edited data
@login_required(login_url='')
def saveedition(request, item_id, restaurant_id, manager_id):
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_manager = get_object_or_404(Manager, pk=manager_id)
    this_item = get_object_or_404(MenuItem, pk=item_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price'))
        edit_item = MenuItem.objects.get(pk=item_id)
        edit_item.name = name
        edit_item.description = description
        edit_item.price = price
        edit_item.save()
        print("Success! Edited MenuItem: " + str(edit_item))
        return HttpResponseRedirect(reverse('restaurant:menu', args=(restaurant_id, manager_id,)))


# class for sitting schedule setting
class Place:
    def __init__(self, row, column, name):
        self.row = row
        self.column = column
        self.name = name


# Setting sitting schedule
@login_required(login_url='/')
def tables(request, restaurant_id, manager_id):
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    if this_restaurant.is_ready:
        return HttpResponseRedirect(reverse('restaurant:manager', args=(manager_id,)))
    else:
        rows = range(1, this_restaurant.rows + 1)
        cols = range(1, this_restaurant.columns + 1)
        places = []
        for i in rows:
            for j in cols:
                name = (i - 1) * this_restaurant.columns + j
                places.append(Place(i, j, name))
        max_tables = this_restaurant.tables
        this_manager = Manager.objects.get(pk=manager_id)
        return render(request, 'restaurant/tables.html', {
            'manager': this_manager,
            'restaurant': this_restaurant,
            'rows': rows,
            'columns': cols,
            'tables': max_tables,
            'places': places
        })


# Setup table schedule
@login_required(login_url='/')
def setup(request, restaurant_id, manager_id):
    # prepare data for going back
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_manager = get_object_or_404(Manager, pk=manager_id)
    r_rows = range(1, this_restaurant.rows + 1)
    r_cols = range(1, this_restaurant.columns + 1)
    r_places = []
    for i in r_rows:
        for j in r_cols:
            r_name = (i - 1) * this_restaurant.columns + j
            r_places.append(Place(i, j, r_name))

    if this_restaurant.is_ready:
        return HttpResponseRedirect(reverse('restaurant:manager', args=(manager_id,)))
    else:
        rows = range(1, this_restaurant.rows + 1)
        cols = range(1, this_restaurant.columns + 1)
        places = range(1, this_restaurant.tables + 1)
        tables_order = []
        tables_numbers = []
        if request.method == 'POST':
            for p in r_places:
                table_name = request.POST.get(str(p.name))
                # if inserted
                if table_name != '':
                    table_num = int(table_name)
                    # check for repeat
                    if table_num in tables_numbers:
                        message = "Please set " + str(this_restaurant.tables) + " different tables!"
                        return render(request, 'restaurant/tables.html', {
                            'manager': this_manager,
                            'restaurant': this_restaurant,
                            'rows': r_rows,
                            'columns': r_cols,
                            'tables': this_restaurant.tables,
                            'places': r_places,
                            'error_message': message
                        })
                    else:
                        r = p.row
                        c = p.column
                        tables_order.append(Place(r, c, table_num))
                        tables_numbers.append(table_num)
            # check for number of tables
            if len(tables_order) == this_restaurant.tables:
                # before inserting tables, see for duplicates

                # inserting tables
                for t in range(0, len(tables_order)):
                    r = tables_order[t].row
                    c = tables_order[t].column
                    n = tables_order[t].name
                    # inserting table
                    new_table = Table.objects.create(number=n, row=r, column=c, currently_free=True,
                                                     restaurant=this_restaurant)
                    new_table.save()
                    print("Success. Inserted Table: " + str(new_table))
                # restaurant is now ready
                update_restaurant = Restaurant.objects.get(pk=restaurant_id)
                update_restaurant.is_ready = True
                update_restaurant.save()
                print("Success. Updated Restaurant: " + str(update_restaurant))
                return HttpResponseRedirect(reverse('restaurant:manager', args=(manager_id,)))
            else:
                message = "Please set " + str(this_restaurant.tables) + " tables!"
                return render(request, 'restaurant/tables.html', {
                    'manager': this_manager,
                    'restaurant': this_restaurant,
                    'places': r_places,
                    'error_message': message
                })


"""User pages"""


# Guest's default page
@login_required(login_url='/')
def guest(request, guest_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    right_now = timezone.now()
    visits = Visit.objects.filter(guest=this_guest).filter(confirmed=True).filter(ending_time__lte=right_now)
    return render(request, 'restaurant/guest.html', context={
        'guest': this_guest,
        'visits': visits
    })


# Rating visit view
@login_required(login_url='/')
def rate(request, guest_id, visit_id):
    this_visit = get_object_or_404(Visit, pk=visit_id)
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_reservation = this_visit.reservation
    # searching for friends visits
    friends_visits = Visit.objects.filter(reservation=this_reservation).filter(confirmed=True).exclude(guest=this_guest)
    count = len(friends_visits)
    # show page
    return render(request, 'restaurant/rating.html', context={
        'guest': this_guest,
        'visit': this_visit,
        'friends': friends_visits,
        'count': count
    })


# Process rate
@login_required(login_url='/')
def rating(request, guest_id, visit_id):
    if request.method == 'POST':
        this_rating = int(request.POST.get('rating'))
        this_visit = Visit.objects.get(pk=visit_id)
        this_visit.grade = this_rating
        this_visit.save()
        print("Success! Rated: " + str(this_visit))
        return HttpResponseRedirect(reverse('restaurant:guest', args=(guest_id,)))


# User friends
@login_required(login_url='/')
def friends(request, guest_id):
    # search for friendships where guest is user
    this_guest = get_object_or_404(Guest, pk=guest_id)
    # get number of friends
    friends_list = get_friends_list(this_guest)
    # calculate number of visits for every friend
    number_of_visits = []
    right_now = timezone.now()
    for ff in friends_list:
        number = len(Visit.objects.filter(guest=ff).filter(confirmed=True).filter(ending_time__lte=right_now))
        number_of_visits.append(number)
    friends_send = zip(friends_list, number_of_visits)
    return render(request, 'restaurant/friends.html', context={
        'guest': this_guest,
        'friends': friends_send
    })


# Search for friends
@login_required(login_url='/')
def search(request, guest_id):
    # find user
    this_guest = get_object_or_404(Guest, pk=guest_id)
    # select other users
    all_guests = Guest.objects.all().exclude(pk=guest_id)
    # find list of friends
    friends_list = get_friends_list(this_guest)
    # users for rendering
    if request.method == 'POST':
        query = request.POST.get('name').lower()
        render_users = []
        for g in all_guests:
            if g not in friends_list:
                # search for name and surname
                if (query in g.user.first_name.lower()) or (query in g.user.last_name.lower()):
                    render_users.append(g)
        # prepare data for resend
        number_of_visits = []
        right_now = timezone.now()
        for ff in friends_list:
            number = len(Visit.objects.filter(guest=ff).filter(confirmed=True).filter(ending_time__lte=right_now))
            number_of_visits.append(number)
        friends_send = zip(friends_list, number_of_visits)
        if len(render_users) == 0:
            return render(request, 'restaurant/friends.html', context={
                'guest': this_guest,
                'friends': friends_send,
                'error_message': "No Users with given First Name and/or Last Name!"
            })
        else:
            return render(request, 'restaurant/friends.html', context={
                'guest': this_guest,
                'friends': friends_send,
                'connections': render_users
            })


# Make new friendship
@login_required(login_url='/')
def connect(request, guest_id, connection_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    new_friend = get_object_or_404(Guest, pk=connection_id)
    new_friendship = Friendship.objects.create(user=this_guest, friend=new_friend)
    new_friendship.save()
    print("Success! New Friendship: " + str(new_friendship))
    return HttpResponseRedirect(reverse('restaurant:friends', args=(guest_id,)))


# Remove friend
@login_required(login_url='/')
def disconnect(request, guest_id, friend_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_friend = get_object_or_404(Guest, pk=friend_id)
    # first search friendships where guest is user
    user_friendship = Friendship.objects.filter(user=this_guest)
    for f in user_friendship:
        if f.friend == this_friend:
            f.delete()
            print("Success! Friendship deleted!")
            return HttpResponseRedirect(reverse('restaurant:friends', args=(guest_id,)))
    # now search friendships where guest is friend
    friend_friendship = Friendship.objects.filter(friend=this_guest)
    for f in friend_friendship:
        if f.user == this_friend:
            f.delete()
            print("Success! Friendship deleted!")
            return HttpResponseRedirect(reverse('restaurant:friends', args=(guest_id,)))


# User profile
@login_required(login_url='/')
def profile(request, guest_id):
    # search for guest
    this_guest = get_object_or_404(Guest, pk=guest_id)
    # get friends
    friends_list = get_friends_list(this_guest)
    # show
    return render(request, 'restaurant/profile.html', context={
        'guest': this_guest,
        'friends': friends_list
    })


# Update User profile info
@login_required(login_url='/')
def update(request, guest_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 == password2:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            address = request.POST.get('address')
            updated_guest = Guest.objects.get(pk=guest_id)
            updated_guest.address = address
            updated_guest.save()
            print("Success! Updated Guest: " + str(updated_guest))
            # update profile
            updated_user = updated_guest.user
            updated_user.first_name = first_name
            updated_user.last_name = last_name
            updated_user.save()
            # update password if changed
            if password1 != '':
                updated_user.set_password(password1)
                updated_user.save()
            print("Success! Updated User: " + str(updated_user))
            return HttpResponseRedirect(reverse('restaurant:profile', args=(guest_id,)))
        else:
            friends_list = get_friends_list(this_guest)
            return render(request, 'restaurant/profile.html', context={
                'guest': this_guest,
                'friends': friends_list,
                'error_message': "New password wasn't repeated correctly!"
            })


# Searching for friends on profile page
@login_required(login_url='/')
def searching(request, guest_id):
    # find user
    this_guest = get_object_or_404(Guest, pk=guest_id)
    # select other users
    all_guests = Guest.objects.all().exclude(pk=guest_id)
    # find list of friends
    friends_list = get_friends_list(this_guest)
    # users for rendering
    if request.method == 'POST':
        query = request.POST.get('name').lower()
        render_users = []
        for g in all_guests:
            if g not in friends_list:
                # search for name and surname
                if query in g.user.first_name.lower() or query in g.user.last_name.lower():
                    render_users.append(g)
        # prepare data for resend
        if len(render_users) == 0:
            return render(request, 'restaurant/profile.html', context={
                'guest': this_guest,
                'friends': friends_list,
                'search_error': "No Users with given First Name and/or Last Name!"
            })
        else:
            return render(request, 'restaurant/profile.html', context={
                'guest': this_guest,
                'friends': friends_list,
                'connections': render_users
            })


# get list of friends for given guest
def get_friends_list(this_guest):
    friendship_user = Friendship.objects.filter(user=this_guest)
    friendship_friend = Friendship.objects.filter(friend=this_guest)
    friends_list = []
    # selecting friends - friend
    for f in friendship_user:
        friend = f.friend
        if friend not in friends_list:
            friends_list.append(friend)
    # selecting friends - user
    for f in friendship_friend:
        friend = f.user
        if friend not in friends_list:
            friends_list.append(friend)
    return friends_list


# Display restaurant list with ratings
@login_required(login_url='/')
def restaurantlist(request, guest_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    restaurants = Restaurant.objects.filter(is_ready=True)
    restaurant_rate = []
    restaurant_friend_rate = []
    for r in restaurants:
        restaurant_rate.append(get_restaurant_rating(r))
        restaurant_friend_rate.append(get_restaurants_friends_rating(r, this_guest))
    restaurants_send = zip(restaurants, restaurant_rate, restaurant_friend_rate)
    return render(request, 'restaurant/restaurants_list.html', context={
        'guest': this_guest,
        'restaurants': restaurants_send
    })


# calculates restaurant's rating
def get_restaurant_rating(this_restaurant):
    list_of_visits = Visit.objects.filter(confirmed=True)
    s = 0
    c = 0
    for v in list_of_visits:
        if v.reservation.restaurant == this_restaurant:
            if v.grade is not None and v.grade >= 1:
                s += v.grade
                c += 1
    if c == 0:
        return 0
    else:
        r = s / c
        return round(r, 2)


# calculates restaurant's friends rating
def get_restaurants_friends_rating(this_restaurant, this_guest):
    guest_friends = get_friends_list(this_guest)
    all_visits = Visit.objects.filter(confirmed=True)
    list_of_visits = []
    for v in all_visits:
        if v.guest in guest_friends or v.guest == this_guest:
            list_of_visits.append(v)
    s = 0
    c = 0
    for v in list_of_visits:
        if v.reservation.restaurant == this_restaurant:
            if v.grade is not None and v.grade >= 1:
                s += v.grade
                c += 1
    if c == 0:
        return 0
    else:
        r = s / c
        return round(r, 2)


# shows restaurant's profile with menu
@login_required(login_url='/')
def restaurantmenu(request, guest_id, restaurant_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=this_restaurant)
    return render(request, 'restaurant/restaurant_menu.html', context={
        'restaurant': this_restaurant,
        'guest': this_guest,
        'items': menu_items
    })


# shows history of guest's reservations
@login_required(login_url='/')
def myreservations(request, guest_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_reservations = Reservation.objects.filter(guest=this_guest)
    return render(request, 'restaurant/my_reservations.html', context={
        'guest': this_guest,
        'reservations': this_reservations
    })


# reservation time
@login_required(login_url='/')
def reservationtime(request, guest_id, restaurant_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    return render(request, 'restaurant/reservation_time.html', context={
        'guest': this_guest,
        'restaurant': this_restaurant
    })


# setup reservation
@login_required(login_url='/')
def makereservation(request, guest_id, restaurant_id):
    # find guest and restaurant
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    # find all reservations for given restaurant
    all_reservations = Reservation.objects.filter(restaurant=this_restaurant)
    # process form
    if request.method == 'POST':
        # get date from form
        date_time = request.POST.get('datetime')
        if date_time == '':
            return render(request, 'restaurant/reservation_time.html', context={
                'guest': this_guest,
                'restaurant': this_restaurant,
                'error_message': "Please insert Date and Time"
            })
        coming = dt.strptime(date_time, '%d-%b-%Y %H:%M:%S')
        # localize to my timezone
        coming_time = pytz.utc.localize(coming)
        # time for comparison
        right_now = timezone.now()
        if coming_time < right_now:
            return render(request, 'restaurant/reservation_time.html', context={
                'guest': this_guest,
                'restaurant': this_restaurant,
                'error_message': "It's impossible to reserve in the past!"
            })
        else:
            # get duration time
            duration = int(request.POST.get('duration'))
            # calculate ending time
            ending_time = coming_time + timedelta(0, hours=duration)
            # filter reservations with same time like new reservation
            taken_tables = 0
            for r in all_reservations:
                # revisar las horas que van a estar en el local
                # si no se pasa del maximo
                # en cada hora
                # descontar de la capacidad disponible para esa hora
                # SINO
                # mostrar en que hora esta full y pedirles hacer otra reserva

                if are_overlap(coming_time, ending_time, r):
                    if this_restaurant.capacity_reserved - r.number_guest < 0:
                        this_restaurant.capacity_reserved -= r.number_guest
            if taken_tables == this_restaurant.tables:
                return render(request, 'restaurant/reservation_time.html', context={
                    'guest': this_guest,
                    'restaurant': this_restaurant,
                    'error_message': "No available tables for given reservation period!"
                })
            else:
                # get all restaurant tables
                all_restaurant_tables = Table.objects.filter(restaurant=this_restaurant)
                # get reserved tables
                all_reserved_tables = []
                for r in all_reservations:
                    if are_overlap(coming_time, ending_time, r):
                        rt = reserved_tables_from_reservation(r)
                        if rt is not None:
                            for rrtt in rt:
                                all_reserved_tables.append(rrtt)
                # check if table is reserved or not
                for single_table in all_restaurant_tables:
                    if single_table in all_reserved_tables:
                        single_table.currently_free = False
                        single_table.save()
                    else:
                        single_table.currently_free = True
                        single_table.save()
                # tables are ready
                rows = range(1, this_restaurant.rows + 1)
                columns = range(1, this_restaurant.columns + 1)
                # create new reservation object
                new_reservation = Reservation.objects.create(coming=coming_time, duration=duration, guest=this_guest,
                                                             restaurant=this_restaurant)
                new_reservation.save()
                print("Success! Created Reservation: " + str(new_reservation))
                created_reservation = Reservation.objects.get(pk=new_reservation.id)
                render_tables = Table.objects.filter(restaurant=this_restaurant)
                return render(request, 'restaurant/reservation_tables.html', context={
                    'guest': this_guest,
                    'restaurant': this_restaurant,
                    'reservation': created_reservation,
                    'tables': render_tables,
                    'rows': rows,
                    'columns': columns
                })


# check if two reservation periods overlap
def are_overlap(coming_time, ending_time, this_reservation):
    reservation_start = this_reservation.coming
    reservation_end = this_reservation.leaving
    if coming_time <= reservation_start <= ending_time:
        return True
    else:
        if coming_time <= reservation_end <= ending_time:
            return True
        else:
            if reservation_start <= coming_time <= reservation_end:
                return True
            else:
                if reservation_start <= ending_time <= reservation_end:
                    return True
                else:
                    return False


# get number of tables from reservation
def get_tables_from_reservation(this_reservation):
    reserved_tables = ReservedTables.objects.filter(reservation=this_reservation)
    if reserved_tables is not None:
        return len(reserved_tables)
    else:
        return 0


# get table object from reservation
def reserved_tables_from_reservation(this_reservation):
    rt = ReservedTables.objects.filter(reservation=this_reservation)
    if rt is not None:
        ret_val = []
        for r in rt:
            ret_val.append(r.table)
        return ret_val
    else:
        return None


# reserving tables
@login_required(login_url='/')
@transaction.atomic
def reservetables(request, guest_id, restaurant_id, reservation_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_reservation = get_object_or_404(Reservation, pk=reservation_id)
    this_tables = Table.objects.filter(restaurant=this_restaurant)
    selected_tables = []
    if request.method == 'POST':
        for t in this_tables:
            if request.POST.get(str(t.id)):
                selected_tables.append(t)
        if len(selected_tables) == 0:
            delete_reservation = Reservation.objects.get(pk=reservation_id)
            delete_reservation.delete()
            print("Deleted Reservation!!!")
            return render(request, 'restaurant/reservation_time.html', context={
                'guest': this_guest,
                'restaurant': this_restaurant,
                'error_message': "Unsuccessful Reservation! Tables weren't selected!"
            })
        # try to reserve tables
        try:
            with transaction.atomic():
                for t in selected_tables:
                    reserve_new_table = ReservedTables.objects.create(reservation=this_reservation, table=t)
                    reserve_new_table.save()
                    print("Success! Reserved table: " + str(t))
        # someonte reserve the table meanwhile
        except:
            delete_reservation = Reservation.objects.get(pk=reservation_id)
            delete_reservation.delete()
            print("Deleted Reservation!!!")
            return render(request, 'restaurant/reservation_time.html', context={
                'guest': this_guest,
                'restaurant': this_restaurant,
                'error_message': "Unsuccessful Reservation! Selected tables are already reserved!"
            })

        # if everything was fine create new visit object
        stops = this_reservation.get_finishing_time()
        new_visit = Visit.objects.create(ending_time=stops, confirmed=True, reservation=this_reservation,
                                         guest=this_guest)
        new_visit.save()
        print("Success! Created new visit: " + str(new_visit))
        list_of_friends = get_friends_list(this_guest)
        return render(request, 'restaurant/reservation_friends.html', context={
            'guest': this_guest,
            'restaurant': this_restaurant,
            'reservation': this_reservation,
            'friends': list_of_friends
        })


@login_required(login_url='')
def invitefriends(request, guest_id, restaurant_id, reservation_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_reservation = get_object_or_404(Reservation, pk=reservation_id)
    # get friends list
    friend_list = get_friends_list(this_guest)
    selected_friends = []
    if request.method == 'POST':
        # collect friends
        for f in friend_list:
            if request.POST.get(str(f.id)):
                selected_friends.append(f)
        # if there is no selected friends, send to my reservations
        if len(selected_friends) == 0:
            return HttpResponseRedirect(reverse('restaurant:myreservations', args=(guest_id,)))
        else:
            # send mail invitations and create visit objects
            stops = this_reservation.get_finishing_time()
            for this_friend in selected_friends:
                print("Working for: " + str(this_friend))
                friend_guest = get_object_or_404(Guest, pk=this_friend.id)
                new_visit = Visit.objects.create(ending_time=stops, confirmed=False, reservation=this_reservation,
                                                 guest=friend_guest)
                new_visit.save()
                print("Success! Created new visit: " + str(new_visit))
                # send_mail
                message_text = "You got an invitation to visit Restaurant. Login and follow link to see more:\n\n"
                link_text = "http://127.0.0.1:8000/restaurant/showinvitation/" + str(
                    friend_guest.id) + "/" + reservation_id + "/" + str(new_visit.id) + "/"
                text_to_send = message_text + link_text
                send_mail('Restaurant - Invitation', text_to_send, 'vdragan1993@gmail.com',
                          [friend_guest.user.username],
                          fail_silently=False)
                print("Success! Mail sent to: " + str(friend_guest))
            # all finished
            return HttpResponseRedirect(reverse('restaurant:myreservations', args=(guest_id,)))


@login_required(login_url='/')
def showinvitation(request, guest_id, reservation_id, visit_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_reservation = get_object_or_404(Reservation, pk=reservation_id)
    this_visit = get_object_or_404(Visit, pk=visit_id)
    right_now = timezone.now()
    if right_now > this_visit.ending_time:
        return render(request, 'restaurant/reservation_confirm.html', context={
            'guest': this_guest,
            'reservation': this_reservation,
            'visit': this_visit,
            'show': False,
            'error_message': "Time's up!"
        })
    else:
        if this_visit.confirmed:
            return render(request, 'restaurant/reservation_confirm.html', context={
                'guest': this_guest,
                'reservation': this_reservation,
                'visit': this_visit,
                'show': False,
                'info_message': "Invitation already confirmed!"
            })
        else:
            return render(request, 'restaurant/reservation_confirm.html', context={
                'guest': this_guest,
                'reservation': this_reservation,
                'visit': this_visit,
                'show': True
            })


@login_required(login_url='/')
def acceptinvitation(request, guest_id, reservation_id, visit_id):
    this_guest = get_object_or_404(Guest, pk=guest_id)
    this_reservation = get_object_or_404(Reservation, pk=reservation_id)
    this_visit = get_object_or_404(Visit, pk=visit_id)
    new_visit = Visit.objects.get(pk=visit_id)
    new_visit.confirmed = True
    new_visit.save()
    print("Success! Confirmed Visit: " + str(this_visit))
    return render(request, 'restaurant/reservation_confirm.html', context={
        'guest': this_guest,
        'reservation': this_reservation,
        'visit': this_visit,
        'info_message': "Invitation Accepted!"
    })


class ManagerListView(ListView):
    model = Restaurant
    template_name = "choose_restaurant.html"

    @login_required(login_url='/')
    def get_success_url(self):
        return HttpResponseRedirect(reverse('restaurant:manager', args=(self.request.user.id,)))

    @login_required(login_url='/')
    def get_queryset(self):
        return Manager.objects.filter(user=self.request.user)


# Display restaurant list with ratings
@login_required(login_url='/')
def managerrestaurantlist(request):
    manager = Manager.objects.filter(user=request.user).last()
    restaurants = Manager.objects.filter(user=request.user)
    return render(request, 'choose_restaurant.html', context={
        'manager': manager,
        'restaurants': restaurants
    })


@login_required(login_url='/')
def manager_restaurant_reserv_list(request, manager_id, restaurant_id):
    this_manager = get_object_or_404(Manager, pk=manager_id)
    restaurant = Restaurant.objects.get(pk=restaurant_id)
    today = datetime.now().today()
    today += timedelta(hours=-3)

    # inicialization values
    open_dinner = None
    closed_dinner = None
    # get today open lunch
    open_lunch = today.replace(hour=restaurant.open_lunch.hour,
                               minute=restaurant.open_lunch.minute,
                               second=0, microsecond=0)
    # get today closed lunch
    closed_lunch = today.replace(hour=restaurant.close_lunch.hour,
                                 minute=restaurant.close_lunch.minute,
                                 second=0, microsecond=0)
    if restaurant.close_lunch < restaurant.open_lunch:
        closed_lunch += timedelta(days=1)

    reservation_list = None
    if today < closed_lunch + timedelta(hours=1):
        reservation_list = Reservation.objects.filter(restaurant=restaurant). \
            filter(coming__range=(open_lunch, closed_lunch)). \
            order_by('coming')
    else:
        open_lunch = None
        closed_lunch = None
        if restaurant.open_dinner and restaurant.close_dinner:
            # get today open dinner
            open_dinner = today.replace(hour=restaurant.open_dinner.hour,
                                        minute=restaurant.open_dinner.minute,
                                        second=0, microsecond=0)
            # get today closed dinner
            closed_dinner = today.replace(day=today.day, hour=restaurant.close_dinner.hour,
                                          minute=restaurant.close_dinner.minute,
                                          second=0, microsecond=0)
            if restaurant.close_dinner < restaurant.open_dinner:
                closed_dinner += timedelta(days=1)

            if today < closed_dinner + timedelta(hours=1):
                reservation_list = Reservation.objects.filter(restaurant=restaurant). \
                    filter(coming__range=(open_dinner, closed_dinner)). \
                    order_by('coming')

    return render(request, 'restaurant/reservation/reservation_list.html', {
        'manager': this_manager,
        'restaurant': restaurant,
        'reservation_list': reservation_list,
        'open_lunch': open_lunch,
        'closed_lunch': closed_lunch,
        'open_dinner': open_dinner,
        'closed_dinner': closed_dinner,
    })


@login_required(login_url='/')
def manager_restaurant_capacity(request, manager_id, restaurant_id):
    restaurant = Restaurant.objects.get(pk=restaurant_id)
    if request.method == 'POST':
        capacity = request.POST.get('capacity')
        capacity_percent = request.POST.get('capacity_percent')
        total_capacity = request.POST.get('total_capacity')
        capacity_reserved = total_capacity
        restaurant.capacity = capacity
        restaurant.capacity_percent = capacity_percent
        restaurant.total_capacity = total_capacity
        restaurant.capacity_reserved = capacity_reserved
        restaurant.save()

        reservation_by_hour_list = ReserveByHour.objects.filter(restaurant=restaurant)

        for reservation_by_hour in reservation_by_hour_list:
            reservation_by_hour.capacity_free = total_capacity - reservation_by_hour.capacity
            if reservation_by_hour.capacity_free < 0:
                reservation_by_hour.capacity_free = 0
            reservation_by_hour.save()

        return HttpResponseRedirect(reverse('restaurant:manager', args=(manager_id, restaurant_id)))


@login_required(login_url='/')
def manager_restaurant_capacity_view(request, manager_id, restaurant_id):
    this_restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    this_manager = Manager.objects.get(pk=manager_id)
    return render(request, 'restaurant/capacity.html', {
        'manager': this_manager,
        'restaurant': this_restaurant,
    })


@login_required(login_url='/')
def manager_navbar(request, manager_id, restaurant_id):
    this_manager = get_object_or_404(Manager, pk=manager_id)
    restaurant = Restaurant.objects.get(pk=restaurant_id)
    return render(request, 'restaurant/navbar_manager.html', {
        'manager': this_manager,
        'restaurant': restaurant,
    })


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all().order_by('name')
    serializer_class = RestaurantSerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().order_by('name')
    serializer_class = MenuItemSerializer

    def list(self, request, **kwargs):
        if kwargs['restaurant_id']:
            restaurant = Restaurant.objects.get(pk=kwargs['restaurant_id'])
            queryset = MenuItem.objects.filter(restaurant=restaurant).order_by('name')
            serializer = MenuItemSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data)


def get_local_schedule(selected_date, restaurant):
    if restaurant.close_dinner:
        closed_dinner = selected_date.replace(hour=restaurant.close_dinner.hour,
                                              minute=restaurant.close_dinner.minute,
                                              second=0, microsecond=0)
        if restaurant.close_dinner < restaurant.open_lunch:
            closed_dinner += timedelta(days=1)
        return [selected_date, closed_dinner]
    else:
        closed_dinner = selected_date.replace(hour=restaurant.close_lunch.hour,
                                              minute=restaurant.close_lunch.minute,
                                              second=0, microsecond=0)
        if restaurant.close_lunch < restaurant.open_lunch:
            closed_dinner += timedelta(days=1)
        return [selected_date, closed_dinner]


class ReserveByHourViewSet(viewsets.ModelViewSet):
    queryset = ReserveByHour.objects.all().order_by('coming')
    serializer_class = ReserveByHourSerializer

    def list(self, request, **kwargs):
        selected_date = datetime.strptime(request.GET['selected_date'], '%Y-%m-%dT%H:%M:%SZ')
        if selected_date:
            if kwargs['restaurant_id']:
                restaurant = Restaurant.objects.get(pk=kwargs['restaurant_id'])
                schedule = get_local_schedule(selected_date, restaurant)
                insert_hour(schedule, restaurant)
                queryset = ReserveByHour.objects.filter(restaurant=restaurant). \
                    filter(date__range=(schedule[0], schedule[1])).order_by('date')
                serializer = ReserveByHourSerializer(queryset, many=True, context={'request': request})
                return Response(serializer.data)


def insert_hour(schedule, restaurant):
    coming = schedule[0]

    open_lunch = schedule[0].replace(hour=restaurant.open_lunch.hour, minute=restaurant.open_lunch.minute,
                                     second=0, microsecond=0)
    closed_lunch = schedule[0].replace(hour=restaurant.close_lunch.hour, minute=restaurant.close_lunch.minute,
                                       second=0, microsecond=0)
    if restaurant.open_dinner and restaurant.close_dinner:
        open_dinner = schedule[0].replace(hour=restaurant.open_dinner.hour, minute=restaurant.open_dinner.minute,
                                          second=0, microsecond=0)
        closed_dinner = schedule[0].replace(hour=restaurant.close_dinner.hour, minute=restaurant.close_dinner.minute,
                                            second=0, microsecond=0)
    if coming < closed_lunch:
        insert_files(open_lunch, closed_lunch, restaurant)
    if restaurant.open_dinner and restaurant.close_dinner:
        insert_files(open_dinner, closed_dinner, restaurant)


def insert_files(init, closed, restaurant):
    while init <= closed:
        if not ReserveByHour.objects.filter(restaurant=restaurant).filter(date=init):
            reservation_hour = ReserveByHour(
                capacity=0,
                capacity_free=restaurant.capacity,
                currently_free=True,
                restaurant=restaurant,
                date=init,
            )
            reservation_hour.save()
        init += timedelta(minutes=30)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by('coming')
    serializer_class = ReservationSerializer

    def list(self, request, **kwargs):
        if kwargs['restaurant_id']:
            restaurant = Restaurant.objects.get(pk=kwargs['restaurant_id'])
            right_now = datetime.now()
            right_now = right_now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = Reservation.objects.filter(restaurant=restaurant).filter(coming__gte=right_now)
            serializer = ReservationSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data)

    def create(self, request, **kwargs):
        new_reservation = request.data
        restaurant = Restaurant.objects.get(pk=kwargs['restaurant_id'])
        coming = datetime.strptime(new_reservation['coming'], '%Y-%m-%dT%H:%M:%SZ')
        leaving = datetime.strptime(new_reservation['leaving'], '%Y-%m-%dT%H:%M:%SZ')

        # reservation_list_day = ReserveByHour.objects.filter(date__gte=coming, date__lt=leaving)

        right_now = datetime.now()
        right_now += timedelta(hours=-3)
        if coming < right_now:
            return Response("La reserva no puede ser anterior al día de hoy",
                            status=status.HTTP_400_BAD_REQUEST
                            )

        # obtener llegada y salida
        reservation_day_coming = coming
        # today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        # get today open lunch
        open_lunch = reservation_day_coming.replace(hour=restaurant.open_lunch.hour,
                                                    minute=restaurant.open_lunch.minute,
                                                    second=0, microsecond=0)
        # get today closed lunch
        closed_lunch = reservation_day_coming.replace(hour=restaurant.close_lunch.hour,
                                                      minute=restaurant.close_lunch.minute,
                                                      second=0, microsecond=0)
        if restaurant.close_lunch < restaurant.open_lunch:
            closed_lunch += timedelta(days=1)

        # obtener llegada y salida
        reservation_day_leaving = leaving
        # get today open dinner
        if restaurant.open_dinner and restaurant.close_dinner:
            open_dinner = reservation_day_leaving.replace(hour=restaurant.open_dinner.hour,
                                                          minute=restaurant.open_dinner.minute,
                                                          second=0, microsecond=0)
            # get today closed dinner
            closed_dinner = reservation_day_leaving.replace(hour=restaurant.close_dinner.hour,
                                                            minute=restaurant.close_dinner.minute,
                                                            second=0, microsecond=0)
            if restaurant.close_dinner < restaurant.open_lunch:
                closed_dinner += timedelta(days=1)

        if coming < closed_lunch:
            if coming < open_lunch:
                return Response("Restaurant abre " + str(open_lunch.hour) + ":" + round_minute(open_lunch.minute) + " hs",
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            if restaurant.open_dinner and restaurant.close_dinner:
                if closed_dinner < coming:
                    return Response("Restaurant cierra " + str(closed_dinner.hour) + ":" + round_minute(closed_dinner.minute) + " hs",
                                    status=status.HTTP_400_BAD_REQUEST)
                elif coming < open_dinner:
                    return Response("Restaurant abre " + str(open_dinner.hour) + ":" + round_minute(open_dinner.minute) + " hs",
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                if open_lunch < coming:
                    return Response("Restaurant abre " + str(open_lunch.hour) + ":" + round_minute(open_lunch.minute) + " hs",
                                    status=status.HTTP_400_BAD_REQUEST)

        if restaurant.open_dinner and restaurant.close_dinner:
            if closed_dinner < leaving:
                return Response("Restaurant cierra " + str(closed_dinner.hour) + ":" + round_minute(closed_dinner.minute) + " hs",
                                status=status.HTTP_400_BAD_REQUEST)
        elif closed_lunch < leaving and open_lunch < coming:
            return Response("Restaurant cierra " + str(closed_lunch.hour) + ":" + round_minute(closed_lunch.minute) + " hs",
                            status=status.HTTP_400_BAD_REQUEST)

        init = coming
        active_reservation = True
        new_reservation_hour_list = []
        while init <= leaving:
            if ReserveByHour.objects.filter(restaurant=restaurant).filter(date=init):
                reservation_hour = ReserveByHour.objects.filter(restaurant=restaurant).filter(date=init)[0]
                if reservation_hour.capacity + new_reservation['number_guest'] <= restaurant.total_capacity:
                    reservation_hour.capacity += new_reservation['number_guest']
                    reservation_hour.capacity_free = restaurant.capacity - reservation_hour.capacity
                    if reservation_hour.capacity_free < 0:
                        reservation_hour.capacity_free = 0
                    reservation_hour.save()
                else:
                    active_reservation = False
            else:
                reservation_hour = ReserveByHour(
                    capacity=new_reservation['number_guest'],
                    capacity_free=restaurant.capacity - new_reservation['number_guest'],
                    currently_free=True,
                    restaurant=restaurant,
                    date=init,
                )
                new_reservation_hour_list.append(reservation_hour)
            init += timedelta(minutes=30)

        if active_reservation:
            for reservation_hour in new_reservation_hour_list:
                reservation_hour.save()
            return super().create(request)
        else:
            return Response("Capacidad llena, consulte en Disponibilidad otros horarios", status=status.HTTP_400_BAD_REQUEST)


def round_minute(minute):
    if minute < 10:
        return '0' + str(minute)
    return minute
