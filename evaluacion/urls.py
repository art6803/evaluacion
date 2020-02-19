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


from django.conf.urls import  url, handler400, handler403,  handler500  #handler404,
from django.contrib import admin
from django.conf import settings

from eval import views
import cuadros.views
from django.conf.urls.static import static


handler400 = 'eval.views.bad_request'
handler403 = 'eval.views.permission_denied'
#handler404 = 'eval.views.page_not_found'
handler500 = 'eval.views.server_error'

admin.autodiscover()

SITE_ID = 1 

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.ingresar),
    url(r'^main/', views.main),
    url(r'^menu/', views.menu),
    url(r'^ingresar/$', views.ingresar),
    url(r'^salir/$',views.cerrar),
    url(r'^cerrar/$', views.cerrar),
    url(r'^titulo/$',views.titulo),
    url(r'^configurar/$',views.configurar),

    url(r'^central/$',views.central),
    url(r'^indesp/$',views.indesp),
    url(r'^indesp_ver/$',views.indesp_ver),
    url(r'^indesp_copiar/$',views.indesp_copiar),
    url(r'^modindesp/$',views.modindesp),
    url(r'^borrindesp/$',views.borrindesp),

    url(r'^indgen/$',views.indgen),
    url(r'^modindgen/$',views.dataindgen),
    url(r'^borrindgen/$',views.borrindgen),
    url(r'^guardaindgen/$',views.guardaindgen),

    url(r'^cargos/$',views.cargos),
    url(r'^ver_cargo/$',views.ver_cargo),
    url(r'^guardar_cargo/$',views.guardar_cargo),
    url(r'^seleccionar_usuario_ie/$',views.seleccionar_usuario_ie),
    url(r'^usuarios/$',views.usuarios),
    url(r'^usuario/$',views.usuario),
    url(r'^usuario_email/$',views.usuario_email),
    url(r'^borrar_usuario/$',views.borrar_usuario),
    url(r'^d_usr/$',views.d_usr),
    url(r'^seleccionar_usuario/$',views.seleccionar_usuario),
    url(r'^guardar_usuario/$',views.guardar_usuario),
    url(r'^usuario_clv/$',views.cambia_clave),
   # url(r'^password_change_done/$',views.ingresar),
    url(r'^faddeval_usuario/$',views.faddeval_usuario),
    url(r'^fdeleval_usuario/$',views.fdeleval_usuario),
   # url(r'^addusuariosel/$',views.addusuariosel),


    url(r'^areas/$',views.areas),
    url(r'^area/$',views.dataarea),
    url(r'^borrar_area/$',views.borrararea),
    url(r'^areastrabaj/$',views.areastrabaj),
    url(r'^areastrabajlst/$',views.areastrabajlst),
    url(r'^areatrabajadfm/$',views.areatrabajadfm),
    url(r'^areatrabjquitar/$',views.areatrabjquitar),

    url(r'^evaluador/$',views.evaluador),
    url(r'^evaluar/$',views.evaluar),
    url(r'^eval/$',views.evaluacion),
    url(r'^evalcuadro/$',cuadros.views.evalcuadro),
    url(r'^addeval/$',views.addeval),
    url(r'^addevalcuad/$',cuadros.views.addeval),
    url(r'^addeval_a/$',views.addeval_a),
    url(r'^printeval/$',views.printeval),
    url(r'^printeval_a/$',views.printeval_a),
    url(r'^printevalcuadro/$',cuadros.views.printeval),
    url(r'^vercpl/$',cuadros.views.vercpl),
    url(r'^imprimircpl/$', cuadros.views.imprimircpl),

    url(r'^a/$',views.ayuda),
    url(r'^sa/$',views.gayuda),

    url(r'^indcuad/$',cuadros.views.indicadores),
    url(r'^modindcuad/$',cuadros.views.indicadoresmod),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
