"""ues URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import include, url

from ues import views as ues_views
from users import views as user_views
from squads import views as squads_views
from material import views as mate_views

urlpatterns = [
    url(r'^$', ues_views.index),
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += [
    url(r'^users/', include([
        url(r'^logout/$', user_views.logout, name='users_logout'),
        url(r'^login/$', user_views.Login.as_view(), name='users_login'),
        url(r'^profile/$', user_views.Profile.as_view(), name='users_profile'),
        url(r'^register/$', user_views.Register.as_view(), name='users_register'),
        url(r'^userrating/$', user_views.get_user_rating_json, name='users_userrating'),
        url(r'^useraclist/$', user_views.get_user_ac_list_json, name='users_useraclist')
    ]))
]

urlpatterns += [
    url(r'^squads/', include([
        url(r'^(?P<squads_id>\d+)/$', squads_views.get_squads_info, name='squads_getinfo'),
        url(r'^(?P<squads_id>\d+)/usersinfo/$', squads_views.get_squads_users_info, name='squads_users_info'),
        url(r'^(?P<squads_id>\d+)/aclist/$', squads_views.get_squads_users_aclist, name='squads_users_aclist'),
        url(r'^(?P<squads_id>\d+)/usersrating/$', squads_views.get_squads_users_rating, name='squads_users_rating'),
    ]))
]

urlpatterns += [
    url(r'^material/', include([
        url(r'^problemrating/$', mate_views.get_problem_rating_json, name='mate_problemrating'),
        url(r'^problemclassify/$', mate_views.get_problem_classify_json, name='mate_problemclassify'),
    ]))
]

# urlpatterns = [
#     url(r'^ues/', include(urlpatterns))
# ]