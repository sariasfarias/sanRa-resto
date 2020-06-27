from django.conf.urls import url, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'restaurant', views.RestaurantViewSet)
router.register(r'restaurant/(?P<restaurant_id>[0-9]+)/menuitem', views.MenuItemViewSet)
router.register(r'restaurant/(?P<restaurant_id>[0-9]+)/reserveByHour', views.ReserveByHourViewSet)
router.register(r'restaurant/(?P<restaurant_id>[0-9]+)/reservation', views.ReservationViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url('', include(router.urls)),
    url('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]