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


class Cargose(models.Model):
    id = models.AutoField(primary_key=True, default=-1)
    nombre = models.CharField(max_length=50, blank=True)


class Ayuda(models.Model):
    id = models.AutoField(primary_key=True, default=-1)
    item = models.IntegerField(null=False, blank=False, default=0)
    alto = models.IntegerField(null=False, blank=False, default=0)
    largo = models.IntegerField(null=False, blank=False, default=0)
    texto = models.CharField(max_length=500, blank=True)
    imagen = models.CharField(max_length=50, blank=True)


class UCargo(models.Model):
    id = models.AutoField(primary_key=True, default=-1)
    noexp = models.CharField(max_length=7, blank=True, unique=True)
    nombre = models.CharField(max_length=48, blank=True)


class Cargo(models.Model):
    id = models.AutoField(primary_key=True, default=-1)
    nombre = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["nombre"]


class Areas(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=48, blank=True)


class Data_User(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    noexp = models.CharField(max_length=7, blank=True, unique=True)
    cid = models.CharField(max_length=11, blank=True)
    nombre = models.CharField(max_length=48, blank=True)
    categoria = models.CharField(max_length=1, blank=False, default='T')
    # T->Tecnicos, O->Operarios, S->Servicio, C->Cuadros, D->Directivos
    cargo = models.ForeignKey(Cargo, null=False, blank=False)
    area = models.ForeignKey(Areas, null=False, blank=False)
    uid = models.CharField(max_length=60, blank=True)
    evaluador = models.BooleanField(default=False)
    evaluado = models.BooleanField(default=False)
    cpl = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    activo = models.BooleanField(default=False)


class Arbol_eval(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    evaluador = models.CharField(max_length=7, blank=True)
    evaluado_exp = models.CharField(max_length=7, blank=True, unique=True)


class Ind_Gen(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=70, blank=True)
    peso = models.FloatField(blank=True)

    # area = models.ForeignKey(Areas, null=False,  blank=False, default=-1)

    class Meta:
        ordering = ["nombre"]


class Ind_Esp(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=500, blank=True)
    peso = models.FloatField(max_length=3, blank=True)
    orden = models.IntegerField(null=False, blank=False, default=0)
    ind_gen = models.ForeignKey(Ind_Gen, null=False, blank=False)
    usuario = models.ForeignKey(Data_User, null=False, blank=False, default=0)

    class Meta:
        ordering = ["orden"]


class Usuario_Ind(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Data_User, null=False, blank=False, default=0)
    i_esp = models.ForeignKey(Ind_Esp, blank=False)


class EvalEncab(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    usuario = models.ForeignKey(Data_User, null=False, blank=False, default=0)
    mes = models.IntegerField(null=False, blank=False, default=1)
    aaa = models.IntegerField(null=False, blank=False, default=2017)
    observ = models.CharField(max_length=50000, null=False, blank=False, default='-')
    valor = models.IntegerField(null=False, blank=False, default=0)
    autoeval = models.BooleanField(default=True)


class Ind_A(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=500, blank=True)
    orden = models.IntegerField(null=False, blank=False, default=0)

    class Meta:
        ordering = ["orden"]


class Evaluacion_a(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    encab = models.ForeignKey(EvalEncab, null=False, blank=False, default=-1)
    indaa = models.ForeignKey(Ind_A, null=False, blank=False, default=-1)
    eval = models.CharField(max_length=500, null=False, blank=False, default='-')


class Evaluacion(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    encab = models.ForeignKey(EvalEncab, null=False, blank=False, default=-1)
    ind_esp = models.ForeignKey(Ind_Esp, null=False, blank=False, default=-1)
    eval = models.CharField(max_length=2, null=False, blank=False, default='-')


class Parametros(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    nombre = models.CharField(max_length=50, null=False, blank=False, default='-')
    valor = models.CharField(max_length=500, null=False, blank=False, default='-')
