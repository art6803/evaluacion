#!/usr/bin/python
# -*- coding: utf8 -*-

# Evaluacion de trabajadores
#
# Copyright (C) 2020 Arturo Castillo Alpizar <art6803@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.



from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser

from eval.models import EvalEncab



class Ind_Cuadro(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=900, blank=True)
    peso = models.FloatField(blank=True)
    orden = models.IntegerField(null=False, blank=False, default=0)

    # area = models.ForeignKey(Areas, null=False,  blank=False, default=-1)

    class Meta:
        ordering = ["orden"]


class EvaluacionCuadro(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    encab = models.ForeignKey(EvalEncab, null=False, blank=False, default=-1)
    indicador = models.ForeignKey(Ind_Cuadro, null=False, blank=False, default=-1)
    eval = models.CharField(max_length=2, null=False, blank=False, default='-')


