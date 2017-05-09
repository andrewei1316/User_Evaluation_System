#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

from material.models import BackgroundKnowledge
from core.classify.verify.verify import PROBLEM_CLASSIFY


def main():
    new_know = {}
    know = BackgroundKnowledge.objects.all().values_list('label', flat=True)
    for cla in PROBLEM_CLASSIFY['Pku']:
        new_know[cla] = []
        for label in PROBLEM_CLASSIFY['Pku'][cla]:
            if str(label) not in know:
                new_know[cla].append(label)

    with open("tmp_data.py", 'wb') as file:
        file.write("PROBLEM_CLASSIFY = {\n")
        file.write("'Pku': {\n")
        for cla in new_know:
            file.write("u'%s': [" % (cla.encode("utf-8"), ))
            for label in new_know[cla]:
                file.write('%d, ' % (label, ))
            file.write('],\n')
        file.write('},\n}\n')
        file.close()


