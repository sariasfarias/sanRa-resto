from django.contrib import admin
from .models import Restaurant, MenuItem, Table, Guest, Manager, Friendship, Reservation, ReservedTables, Visit, \
    ReserveByHour

admin.site.register(Restaurant)
admin.site.register(MenuItem)

# admin.site.register(Guest)
admin.site.register(Manager)
admin.site.register(Reservation)
# admin.site.register(Friendship)
# admin.site.register(ReserveByHour)
# changing order of fields for reservation
'''class ReservationAdmin(admin.ModelAdmin):
    fields = ['restaurant', 'coming', 'leaving']
    
    
admin.site.register(Reservation, ReservationAdmin)


# changing order of fields for visit
class VisitAdmin(admin.ModelAdmin):
    fields = ['guest', 'reservation', 'ending_time', 'confirmed', 'grade']


admin.site.register(Visit, VisitAdmin)'''
