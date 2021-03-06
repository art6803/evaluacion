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


from django import forms
from django.forms import ModelForm
from eval.models import Ind_Gen, Cargo, Data_User, Areas, Arbol_eval


class IndForm(ModelForm):

    class Meta:
        model = Ind_Gen
        fields = ['nombre', 'peso','id']


class LoginForm(forms.Form):

	user = forms.CharField(max_length=100)
	password = forms.CharField(widget=forms.PasswordInput())