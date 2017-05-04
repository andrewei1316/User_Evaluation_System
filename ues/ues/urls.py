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
    url(r'^$', ues_views.index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
]

handler500 = 'ues.views.server_error_view'
handler404 = 'ues.views.page_not_found_view'


urlpatterns += [
    url(r'^users/', include([
        url(r'^logout/$', user_views.logout, name='users_logout'),
        url(r'^login/$', user_views.Login.as_view(), name='users_login'),
        url(r'^profile/$', user_views.Profile.as_view(), name='users_profile'),
        url(r'^register/$', user_views.Register.as_view(), name='users_register'),
        url(r'^usernames/$', user_views.get_all_user_name, name='users_allusername'),
        url(r'^userrating/$', user_views.get_user_rating_json, name='users_userrating'),
        url(r'^useraclist/$', user_views.get_user_ac_list_json, name='users_useraclist')
    ]))
]

urlpatterns += [
    url(r'^squads/', include([
        url(r'^new/$', squads_views.create_update_squads, name='squads_create_update'),
        url(r'^manage/$', squads_views.get_own_squads_info, name='squads_get_own_info'),
        url(r'^(?P<squads_id>\d+)/$', squads_views.get_squads_info, name='squads_getinfo'),
        url(r'^(?P<squads_id>\d+)/delete$', squads_views.delete_squads, name='squads_delete'),
        url(r'^(?P<squads_id>\d+)/usersinfo/$', squads_views.get_squads_users_info, name='squads_users_info'),
        url(r'^(?P<squads_id>\d+)/aclist/$', squads_views.get_squads_users_aclist, name='squads_users_aclist'),
        url(r'^(?P<squads_id>\d+)/usersrating/$', squads_views.get_squads_users_rating, name='squads_users_rating'),
        url(r'^squadsuser/', include([
            url(r'^edit/$', squads_views.update_squadsusers, name='squadsusers_update'),
            url(r'^self/$', squads_views.get_self_squads_info, name='squadsusers_getinfo'),
            url(r'^(?P<squadsusers_id>\d+)/delete/$', squads_views.delete_squadsusers, name='squadsusers_delete'),
        ]))
    ]))
]

urlpatterns += [
    url(r'^material/', include([
        url(r'^update/$', mate_views.update_material, name='mate_update'),
        url(r'^problemrating/$', mate_views.get_problem_rating_json, name='mate_problemrating'),
        url(r'^problemmaterial/$', mate_views.get_all_problem_material, name='mate_problemmaterial'),
        url(r'^problemclassify/$', mate_views.get_problem_classify_json, name='mate_problemclassify'),
    ]))
]

urlpatterns = [
    url(r'^ues/', include(urlpatterns))
]
