#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import template
register = template.Library()
from django.core.urlresolvers import reverse

@register.filter(name='edit_js_param')
def edit_js_param(squad):
    return "%d, '%s', '%s', '%s', '%s'" %(squad.id, squad.name, squad.create_user,
        squad.description, reverse('squads_users_info', kwargs={'squads_id': squad.id}))

@register.filter(name='delete_js_param')
def delete_js_param(squad):
    return "'%s'" % (reverse('squads_delete', kwargs={'squads_id': squad.id}), )

@register.filter(name='edit_squads_user_param')
def edit_squads_user_param(squads_user):
    squad = squads_user.squads
    return "%d, '%s', '%s', '%s', '%s', '%s'" %(squads_user.id, squad.name, squad.create_user, squads_user.name,
        squads_user.nickname, reverse('squadsusers_update'))

@register.filter(name='delete_squads_user_param')
def delete_squads_user_param(squads_user):
    return "'%s'" % (reverse('squadsusers_delete', kwargs={'squadsusers_id': squads_user.id}), )

@register.filter(name='edit_classify_param')
def edit_classify_param(material):
    repo = material.repo
    label = material.label
    classify = []
    for cla in material.classify.all():
        classify.append(int(cla.id))
    return '"%s", "%s", "%s"' % (repo, label, classify)


