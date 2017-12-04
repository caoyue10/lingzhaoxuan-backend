from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^init', views.init, name='init'),
    url(r'^getImage', views.get_image, name='get_image'),
]
