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




from decimal import *

import datetime
import win32security
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.context_processors import csrf


import codecs

from eval.models import Ind_Gen, Cargo, Data_User, Areas, Arbol_eval, Ind_Esp, Ind_A, Evaluacion, \
    Evaluacion_a, Ayuda, EvalEncab, Parametros
from reporte.rcls import Report
from reporte import Syllabification

pagusuarios = 0

def bad_request(request):
    response = render_to_response( '400.html', context_instance=RequestContext(request)    )
    response.status_code = 400
    return response


def permission_denied(request):
    response = render_to_response( '403.html', context_instance=RequestContext(request)    )
    response.status_code = 403
    return response


def page_not_found(request):
    response = render_to_response( '404.html', context_instance=RequestContext(request)    )
    response.status_code = 404
    return response


def server_error(request):
    response = render_to_response( '500.html', context_instance=RequestContext(request)    )
    response.status_code = 500
    return response


@login_required(login_url='/ingresar')
def menu(request):
    return render_to_response('menu.html', {})


def autenticar(username, password):
    domain = 'CIMEX'
    try:
        token = win32security.LogonUser(
            username,
            domain,
            password,
            win32security.LOGON32_LOGON_NETWORK,
            win32security.LOGON32_PROVIDER_DEFAULT)
        autenticado = bool(token)
    except:
        autenticado = None

    return autenticado


def ingresar(request):
    request.session.clear_expired()

    if request.method == 'POST':
       # formulario = AuthenticationForm(request.POST)
        #if formulario.is_valid:
        winid = request.POST['username']
        winid = winid.strip()
        if winid.find('\\') >= 0:
            winid = winid[winid.find('\\') + 1:]
        if winid.find('/') >= 0:
            winid = winid[winid.find('/') + 1:]
        if winid.find('@') >= 0:
            winid = winid[:winid.find('@')]

        clave = request.POST['password']

        #acceso = autenticar(username=winid, password=clave)

        acceso = True


        if acceso:
            usuario = Data_User.objects.get(uid=winid)
            usuario = usuario.noexp
            usr = User.objects.get(username=usuario)
            #usr.set_password(clave)
            #usr.save()
            acceso = authenticate(username=usuario, password=clave)

        if acceso is not None:
            if acceso.is_active:
                login(request, acceso)
                request.session['username'] = usuario
                request.session.set_expiry(3000)

                usr = User.objects.get(username=usuario)
                data = Data_User.objects.get(noexp=usuario)
                c = {}
                c.update(csrf(request))
                c['user'] = usuario
                c['usuario'] = usuario
                c['noexp'] = usuario
                c['STATIC_URL'] = '/static/'

                if usr.is_superuser:
                    return HttpResponseRedirect('/main/')
                else:
                    return HttpResponseRedirect('/evaluador/?exp=' + usuario)
            else:
                return render_to_response('noactivo.html', context_instance=RequestContext(request))
        else:
            return render_to_response('nousuario.html', context_instance=RequestContext(request))
    #else:
    #    formulario = AuthenticationForm()
    c = {}
    c.update(csrf(request))
    c['STATIC_URL'] = '/static/'

    usrl = Data_User.objects.filter(activo=True)
    if len(usrl) == 0:
        #aqui
        area = Areas.objects.filter(nombre='Nueva Area')
        if len(area) == 0:
            area = Areas.objects.create(nombre='Nueva Area')
            area.save()
        cargo = Cargo.objects.filter(nombre='Nuevo Cargo')
        if len(cargo) == 0:
            cargo = Cargo.objects.create(nombre='Nuevo Cargo')
            cargo.save()
        area = Areas.objects.get(nombre='Nueva Area')
        cargo = Cargo.objects.get(nombre='Nuevo Cargo')
        Usuario = Data_User.objects.create(noexp='12345', cid='11111111111', nombre='Nuevo Usuario', activo=True, \
                                               categoria='E', uid='12345', evaluador=True, \
                                               evaluado=False, admin=True, cargo=cargo, area=area, cpl= False)
        Usuario.save()


        usr = User.objects.create(username = '12345', is_superuser = True,
                                  first_name = '12345', last_name = 'Nuevo Usuario',
                                  email = 'a@b.c', is_staff = True, is_active = True)
        usr.set_password('12345')
        usr.save()
        transaction.commit()
        c['username'] = '12345'
        c['password'] = '12345'







    return render_to_response('ingresar.html', c)


@login_required(login_url='/ingresar')
def cerrar(request):
    del request.session['username']
    logout(request)
    return HttpResponseRedirect('/')


@login_required(login_url='/ingresar')
def inicio(request):
    if request.user.is_authenticated():
        username = request.user.username
        uid = request.user.id
        usr1 = User.objects.get(pk=uid)
        return render_to_response('frames.html', {'STATIC_URL': '/static/'})


@login_required(login_url='/ingresar')
def main(request):
    if request.user.is_authenticated():
        request.session.cycle_key()
        userexp = request.user.username
        #uid = request.user.id
        oevaluador = Data_User.objects.get(noexp=userexp)

        esevaluador = len(Arbol_eval.objects.filter(evaluador=oevaluador.noexp)) > 0

        c = {}
        c['STATIC_URL'] = '/static/'
        c['evaluador'] = oevaluador
        c['esevaluador'] = esevaluador

        return render_to_response('frames.html', c)



@login_required(login_url='/ingresar')
def evaluador(request):
    if request.method == 'GET':
        userexp = request.GET.get('exp')
        data = []
        evaluador = {}
        evaluadospor(userexp, data, evaluador)

        c = {}
        c.update(csrf(request))
        c['sujetos'] = data
        c['evaluador'] = evaluador
        c['STATIC_URL'] = '/static/'
        return render_to_response('evalua.html', c)


@login_required(login_url='/ingresar')
def evaluar(request):
    if request.method == 'GET':
        userexp = request.GET.get('exp')
        evaluadorexp = request.GET.get('evaluador')
        evaluador = Data_User.objects.get(noexp=evaluadorexp)
        evaluado = Data_User.objects.get(noexp=userexp)
        evaldata = Evaluacion.objects.all()
        evaldata = evaldata.extra(order_by="orden")

        # meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 
        # 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    meses = ['Enero-Marzo',
             'Abril-Junio',
             'Julio-Septiembre',
             'Octubre-Diciembre'
             ]

    aa = ['2016',
          '2017',
          '2018',
          '2019',
          '2020',
          '2021'
          ]

    lsta = []
    nm = {}
    na = {}
    lm = []
    for a in aa:
        na = {}
        na['num'] = a
        na['meses'] = []
        i = 1
        lm = []

        for m in meses:
            nm = {}
            nm['nombre'] = m
            nm['num'] = i

            encab = EvalEncab.objects.filter(usuario=evaluado, mes=i, aaa=a)
            if len(encab) > 0:
                nm['color'] = '21AE01'
            else:
                nm['color'] = 'ffffff'
            i += 1
            lm.append(nm)
        nm = {}
        nm['nombre'] = 'Resumen Anual'
        nm['num'] = 13
        encab = EvalEncab.objects.filter(usuario=evaluado, mes=13, aaa=a)
        if len(encab) > 0:
            nm['color'] = '21AE01'
        else:
            nm['color'] = 'ffffff'


        lm.append(nm)
        na['meses'] = lm
        lsta.append(na)
    accion = ''
    if evaluado.categoria == u'C':
        accion = 'cuadro'

    c = dict(
        evaluado=evaluado,
        evaluador=evaluador,
        accion=accion,
        aa=lsta,
        STATIC_URL = '/static/'
        )
    c.update(csrf(request))
    return render_to_response('calendario.html', c, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def evaluacion_a(request, aa):
    evaluadorexp = request.GET.get('evaluador')
    evaluadoexp = request.GET.get('evaluado')
    evaluador = Data_User.objects.get(noexp=evaluadorexp)
    evaluado = Data_User.objects.get(noexp=evaluadoexp)

    promedio = 0
    try:
        data = []
        encab = []
        pie = []
        try:
            evalencab = EvalEncab.objects.get(usuario=evaluado, mes='13', aaa=aa)
        except:
            evalencab = EvalEncab(usuario=evaluado, mes='13', aaa=aa)
            evalencab.observ = ''
            evalencab.save()
            transaction.commit()

        descind_a = Ind_A.objects.all()
        for ind in descind_a:
            nodo = {}
            evaltxt = ''
            try:
                eval_a = Evaluacion_a.objects.get(encab=evalencab, indaa=ind)
                evaltxt = eval_a.eval
            except:
                evaltxt = ''

            nodo['item'] = ind.id
            nodo['texto'] = ind.nombre
            nodo['eval'] = evaltxt
            if ind.orden == 1:
                nodo['eval'] = str(ind_anual(evaluado, aa))

            if ind.orden < 2:
                encab.append(nodo)
            else:
                if ind.orden > 9:
                    texto = nodo['texto']
                    nodo['texto'] = texto[:texto.find(':')]
                    nodo['expl'] = texto[texto.find(':') + 1:]
                    pie.append(nodo)
                else:
                    data.append(nodo)
    except:
        data = []
        encab = []
        pie = []

    cargo = evaluado.cargo.id
    c = {}
    c.update(csrf(request))
    c['evaluado'] = evaluado
    c['evaluador'] = evaluador
    c['promedio'] = promedio
    c['encab'] = encab
    c['pie'] = pie
    c['indc_a'] = data
    c['aa'] = aa
    c['STATIC_URL'] = '/static/'
    return render_to_response('evaluacionanual.html', c, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def evaluacion_m(request, mes, imes, aa):
    meses = '-, ' \
            'Enero-Marzo, ' \
            'Abril-Junio, ' \
            'Julio-Septiembre, ' \
            'Octubre-Diciembre'
    meses = meses.split(', ')
    ok = 0
    Datames = meses[imes]

    evaluadorexp = request.GET.get('evaluador')
    evaluadoexp = request.GET.get('evaluado')

    evaluador = Data_User.objects.get(noexp=evaluadorexp)
    evaluado = Data_User.objects.get(noexp=evaluadoexp)

    try:
        evalencab = EvalEncab.objects.get(usuario=evaluado, mes=mes, aaa=aa)
        observ = evalencab.observ
        eval = Evaluacion.objects.filter(encab=evalencab)
    except:
        eval = []
        observ = ""

    cargo = evaluado.cargo.id
    indgen = Ind_Gen.objects.all()
    data = []
    for ind in indgen:
        datanodo = {}
        datanodo['id'] = ind.id
        datanodo['nombre'] = ind.nombre
        datanodo['peso'] = ind.peso
        indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=evaluado)
        lespec = []
        for ie in indesp:
            _esp = {}
            _esp['id'] = ie.id
            _esp['nombre'] = ie.nombre
            _esp['peso'] = ie.peso
            _esp['selec'] = ''
            if len(eval) > 0:
                for value in eval:
                    if value.ind_esp.id == ie.id:
                        _esp['selec'] = value.eval
            else:
                _esp['selec'] = 'mb'

            lespec.append(_esp)
        datanodo['indespec'] = lespec
        data.append(datanodo)

    c = {}
    c.update(csrf(request))
    c['evaluado'] = evaluado
    c['evaluador'] = evaluador
    c['indgen'] = data
    c['observ'] = observ
    c['aa'] = aa
    c['mes'] = mes
    c['nombremes'] = Datames
    c['meses'] = ['Enero-Marzo', 'Abril-Junio', 'Julio-Septiembre', 'Octubre-Diciembre']
    c['STATIC_URL'] = '/static/'
    return render_to_response('evaluacion.html', c, context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def evaluacion(request):
    if request.method == 'GET':
        i = 0
        aa = request.GET.get('a')
        mes = request.GET.get('mes')
        imes = int(mes)
        if imes < 13:
            return evaluacion_m(request, mes, imes, aa)
        else:
            return evaluacion_a(request, aa)


@login_required(login_url='/ingresar')
def addeval_a(request):
    if request.method == 'POST':
        mes = '13'
        evaluado = request.POST['evaluado']
        evaluador = request.POST['evaluador']
        aa = request.POST['aa']
        cargo = request.POST['idcargo']

        OEvaluado = Data_User.objects.get(noexp=evaluado)
        OEvaluador = Data_User.objects.get(noexp=evaluador)
        OCargo = Cargo.objects.get(id=cargo)

        id = 0
        llave = ''
        eval = {}
        while id < 20:
            llave = 'ind' + str(id)
            if llave in request.POST:
                eval[id] = request.POST[llave]
            id += 1

        try:
            encab = EvalEncab.objects.get(usuario=OEvaluado, mes=mes, aaa=aa)
        except EvalEncab.DoesNotExist:
            encab = EvalEncab(usuario=OEvaluado, mes=mes, aaa=aa)

        encab.observ = ''
        encab.valor = -1
        encab.save()
        transaction.commit()

        cindanual = Ind_A.objects.all()
        for item in cindanual:
            try:
                teval = Evaluacion_a.objects.get(encab=encab, indaa=item)
            except:
                teval = Evaluacion_a(encab=encab, indaa=item)

            if item.id in eval:
                texto = eval[item.id]
                teval.eval = texto[:4990]
            else:
                teval.eval = '???'
            teval.save()
    return HttpResponseRedirect('/evaluar/?exp=' + evaluado + '&evaluador=' + evaluador)


@login_required(login_url='/ingresar')
def addeval(request):
    if request.method == 'POST':
        mes = request.POST['mes']
        evaluado = request.POST['evaluado']
        evaluador = request.POST['evaluador']
        aa = request.POST['aa']
        #indgen = request.POST['idindgen']
        observ = request.POST['comment']
        usuario = Data_User.objects.get(noexp=evaluado)
        try:
            encab = EvalEncab.objects.get(usuario=usuario, mes=mes, aaa=aa)
        except EvalEncab.DoesNotExist:
            encab = EvalEncab(usuario=usuario, mes=mes, aaa=aa)

        encab.observ = observ
        encab.save()

       # try:
       #     m13 = EvalEncab.objects.get(usuario=usuario, mes=13, aaa=aa)
       #     m13.delete()
       # except EvalEncab.DoesNotExist:
       #     pass

        eval = []
        pst = request.POST.keys()
        for key in pst:
            if key[0] == 'n':
                eval.append(key[1:])

        for key in eval:
            nkey = 'n' + key
            indesp = Ind_Esp.objects.get(id=int(key))
            valor = request.POST[nkey]
            try:
                teval = Evaluacion.objects.get(encab=encab, ind_esp=indesp)
            except Evaluacion.DoesNotExist:
                teval = Evaluacion(encab=encab, ind_esp=indesp, eval=valor)
            teval.eval = valor
            teval.save()
    return HttpResponseRedirect('/evaluar/?exp=' + evaluado + '&evaluador=' + evaluador)

@login_required(login_url='/ingresar')
def calcind(request):
    relac = {}

    if request.method == 'GET':
        aa = request.GET.get('a')
        mes = int(request.GET.get('mes'))
        exp = request.GET.get('evaluado')
        #   evaluador = request.GET.get('evaluador')
        udata = Data_User.objects.get(noexp=exp)
        nombre = udata.nombre
#        cargo = udata.cargo.nombre
 #       periodo = meses[mes] + '/' + aa
 #       categoria = Categorias[udata.categoria]

        area = udata.area.nombre

        evalencab = EvalEncab.objects.get(usuario=udata, mes=mes, aaa=aa)
#        observ = evalencab.observ
        # eval = Evaluacion.objects.filter(encab=evalencab)
        indgen = Ind_Gen.objects.all()

        valpeso = {}
        valcalif = {}
        param = Parametros.objects.all()
        for item in param:
            relac[item.nombre.strip()] = item.valor.strip().replace('\'', '').replace('"', '')
            if item.nombre.find('peso') >= 0:
                nombre = item.nombre.replace('peso', '')
                valpeso[nombre.lower()] = float(item.valor.lower().strip())

        relac['peso'] = valpeso


        peso = valpeso

        for ind in indgen:
            indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=udata)
            sumeval = 0
            contador = 0
            real = 0
            for ie in indesp:
                try:
                    teval = Evaluacion.objects.get(encab=evalencab, ind_esp=ie)
                    real += ie.peso * peso[teval.eval]
                    sumeval += peso[teval.eval]
                    contador += 1
                except:
                    pass

            total = total + real * sumeval

    return HttpResponse(total)


@login_required(login_url='/ingresar')
def printeval(request):
    if request.method == 'GET':
        mes = int(request.GET.get('mes'))
        if mes == 13:
            return printeval_a(request)
        else:
            return printeval_m(request)



def separaln(entrada, limlinea, rpt, fontName, fontSize, sangria):
    txt = ''
    lprint = []
    lltotal = []
    l = []
    entrada = entrada.split('\r\n')
    for lines in entrada:
        lines = lines.strip()
        if len(lines) > 0:
            while lines.find('  ') >= 0:
                lines = lines.replace('  ', ' ')
            txt = lines.split()
            linea = ''
            if sangria:
                linea = '    '
            nlinea = 0
            while len(txt) > 0:
                largo = rpt.largotexto(linea + ' ' + txt[0], fontName, fontSize)
                if largo < limlinea:
                    linea = linea + ' ' + txt[0]
                    txt = txt[1:]
                else:
                    silabas = Syllabification.silabas(txt[0])
                    palabra = ''
                    while rpt.largotexto(linea + ' ' + palabra + '- ', fontName, fontSize) < limlinea and (len(silabas) > 0):
                        palabra = palabra + silabas[0]
                        if len(silabas) > 1:
                            silabas = silabas[1:]
                        else:
                            silabas = []

                    txt[0] = ''
                    for item in silabas:
                        txt[0] = txt[0] + item
                    if (len(palabra) > 0):
                        linea = linea + ' ' + palabra
                        if len(silabas) > 0:
                            linea = linea + '-'
                        else:
                            txt = txt[1:]
                        linea = linea.replace(',-', ',')
                    if nlinea > 0:
                        linea = linea.strip()

                    lprint.append(linea)
                    linea  = ''
                    nlinea += 1
            if len(linea) > 0:
                lprint.append(linea.strip())

        else:
            lprint.append('')
    largos = []
    espacio = rpt.largotexto(' ', fontName, fontSize)
    maximo = 0
    for item in lprint:
        largo = rpt.largotexto(item, fontName, fontSize)
        if largo > maximo:
            maximo = largo
        largos.append(largo)

    for item in range(0, len(lprint)):
        linea = lprint[item]
        falta = int(round((maximo - largos[item]) / espacio))
        if (falta >= 1) and (falta < 20):
            temp = ''
            if len(linea) >= 2:
                while linea[0] == ' ':
                    temp += linea[0]
                    linea = linea[1:]
                    if linea == '' :
                        break;

                while falta > 0:
                    if len(linea) >= 1:
                        letra = linea[0]
                        if len(linea) > 1:
                            linea = linea[1:]
                        else:
                            linea = ''
                            falta = 0
                    else:
                        falta = 0
                    temp = temp + letra
                    if letra == ' ':
                        temp = temp + ' '
                        falta -= 1

            linea = temp + linea
        lprint[item] = linea
    return lprint

@login_required(login_url='/ingresar')
def printeval_m(request):
    nombreeval = ''
    a4 = 800
    carta = 790
    peso = {'mb': 1, 'b': 0.75, 'r': 0.50, 'm': 0.25}
    orden = ['mb', 'b', 'r', 'm']
    Categorias = {"T": "Técnicos", "O": "Operarios", "S": "Servicio", "C": "Cuadros", "D": "Directivos"}

    meses = ["", "Enero-Marzo", "Abril-Junio", "Julio-Septiembre", "Octubre-Diciembre"]
    calif = {'mb': 'muy bien', 'b': 'bien', 'r': 'regular', 'm': 'mal', 'mm': 'muy mal'}
    tletra = 8

    relac = {'peso': peso, 'orden': orden, 'categorias': Categorias, 'calif': calif, 'Tamletra': tletra, 'Pie': ' ', 'Encab': ' '}

    valpeso  = {}
    valcalif = {}
    param = Parametros.objects.all()
    for item in param:
        relac[item.nombre.strip()] = item.valor.strip().replace('\'', '').replace('"', '')
        if item.nombre.find('peso') >= 0 :
            nombre = item.nombre.replace('peso', '')
            valpeso[nombre.lower()] = float(item.valor.lower().strip())


    relac['peso'] = valpeso
    relac['calif'] = calif

    # peso

   # txt = relac['peso'].strip().lower().split(',')
  #  for item in txt:
  #      item = item.split(':')
  #      val[item[0].strip()] = float(item[1])

    peso = valpeso

    # calif
   # val = {}
   # txt = relac['calif'].strip().lower().split(',')
   # for item in txt:
    #    item = item.split(':')
    #    val[item[0].strip()] = item[1]

    #calif = val

    # categorias
    val = {}
    txt = relac['categorias'].strip().split(',')
    for item in txt:
        item = item.split(':')
        val[item[0].strip()] = item[1]
    relac['categorias'] = val
    Categorias = val

    # orden
    #val = {}
    relac['orden'] = relac['orden'].strip().lower().split(',')
    orden = relac['orden']

    response = ''
    if request.method == 'GET':
        aa = request.GET.get('a')
        mes = int(request.GET.get('mes'))
        exp = request.GET.get('evaluado')
        #   evaluador = request.GET.get('evaluador')
        udata = Data_User.objects.get(noexp=exp)
        nombre = udata.nombre
        cargo = udata.cargo.nombre
        periodo = meses[mes] + '/' + aa
        categoria = Categorias[udata.categoria]

        area = udata.area.nombre

        nombreeval = nombre.split(' ')[0] + '_' + exp + '_' + meses[mes] + '-' + aa

        rpt = Report()
        response = rpt.preparar(encab=relac['Encab'], pie=relac['Pie'], nombreeval=nombreeval )

        rpt.letra("Helvetica-Bold", tletra + 3)
        rpt.origen(35, carta)
        rpt.escribeln('Nombre: ' + nombre)
        rpt.ysum(2)
        rpt.escribeln('Cargo: ' + cargo)
        rpt.ysum(2)
        rpt.escribeln('Categoria: ' + categoria)
        rpt.ysum(2)
        rpt.escribeln('Area: ' + area)
        rpt.ysum(2)
        rpt.escribeln('Periodo: ' + periodo)
        rpt.ysum(2)

        evalencab = EvalEncab.objects.get(usuario=udata, mes=mes, aaa=aa)
        observ = evalencab.observ
        #eval = Evaluacion.objects.filter(encab=evalencab)
        indgen = Ind_Gen.objects.all()
        #ldata = []
        #lineas = []
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.letra("Helvetica-Bold", tletra + 3)
        rpt.escribeln('Indicadores')
        rpt.escribeln('')
        limlinea = 75
        indice = {}
        total = 0

        for ind in indgen:
            indice[ind.id] = {}
            indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=udata)
            valores = []
            sumeval = 0
            contador = 0
            real = 0
            for ie in indesp:
                #valor = ''
                nodo = {}

                try:
                    teval = Evaluacion.objects.get(encab=evalencab, ind_esp=ie)
                    valor = calif[teval.eval]
                    nodo['calif'] = valor
                    nodo['valor'] = peso[teval.eval]
                    nodo['peso'] = ie.peso
                    nodo['real'] = ie.peso * peso[teval.eval]
                    real += nodo['real']
                    valores.append(nodo)
                    sumeval += nodo['valor']
                    contador += 1

                except:
                    valor = '?'
            indicador = {}
            indicador['peso'] = ind.peso
            indicador['valores'] = valores
            indicador['suma'] = sumeval
            if real > 1:
                real = 1
            indicador['real'] = real

            if contador == 0:
                resultado = 0
            else:
                resultado = real  # sumeval/contador

            indicador['resultado'] = resultado
            for itempeso in orden:
                if peso[itempeso] >= resultado:
                    indicador['resultado'] = calif[itempeso]
            indice[ind.id] = indicador
            total = total + indicador['real'] * indicador['peso']

        rfinaltxt = ''
        rfinal = total  # rfinal/rfinalc
        for itempeso in orden:
            if peso[itempeso] >= rfinal:
                rfinaltxt = calif[itempeso]

        for ind in indgen:

            datanodo = {}
            datanodo['id'] = ind.id
            datanodo['nombre'] = ind.nombre
            valindicador = indice[ind.id]
            #print valindicador
            sumeval += valindicador['suma']
            contador += 1
            rpt.letra("Helvetica-Bold", tletra + 3)
            y = rpt.yval()
            rpt.escribeln(ind.nombre.strip())
            rpt.letra("Helvetica", tletra + 2)
            rpt.escribe_xy(430, y, valindicador["resultado"])
            rpt.ysum(2)

            indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=udata)
            for ie in indesp:
                rpt.letra("Helvetica", tletra + 2)
                #valor = ''
                try:
                    teval = Evaluacion.objects.get(encab=evalencab, ind_esp=ie)
                    valor = calif[teval.eval]
                except:
                    valor = '?'

                    #     lineas.append('       ' + ie.nombre[:limlinea] + '    '+ valor)
                y = rpt.yval()
                ie.nombre = ie.nombre.strip()

                lprint = separaln(ie.nombre, 345, rpt, "Helvetica", tletra + 2, False)


                rpt.escribeln(u'    \u2022 ' + lprint[0])
                lprint = lprint[1:]

                # rpt.letra("Helvetica", 8)
                rpt.escribe_xy(450, y, valor)
                # rpt.letra("Helvetica", 9)
                for lines in lprint:
                    rpt.escribeln('       ' + lines)
               # if len(ie.nombre) > limlinea:
                #    txt = ie.nombre[limlinea:]
                #    while len(txt) >= limlinea:
                #        rpt.escribeln('       ' + txt[:limlinea])
                 ##       txt = txt[limlinea:]
                #    rpt.escribeln('       ' + txt)
                rpt.ysum(4)
            rpt.ysum(4)
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.letra("Helvetica-Bold", tletra + 2)
        rpt.escribeln('Resultado final:  ' + rfinaltxt)
        rpt.escribeln('')
        rpt.escribeln(u'Indice de desempeño:  ' + str(total))
        evalencab.valor = total * 100
        evalencab.save()
        transaction.commit()

        rpt.escribeln('')
        rpt.letra("Helvetica-Bold", tletra + 2)
        rpt.escribeln('Observaciones')
        rpt.letra("Helvetica", tletra + 2)
        rpt.escribeln('')

       # observ = observ.split('\r\n')
        limlinea = 120
        #corrector

        lprint = separaln(observ, 430, rpt, "Helvetica", tletra + 2, True)
        for lines in lprint:
            rpt.escribeln(lines)
        rpt.letra("Helvetica-Bold", tletra + 2)
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('Firma del Evaluado.')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.escribeln('Firma del Evaluador')
        rpt.finaliza()
    return response


def cortar(largo, acortar):
    texto = acortar.split(' ')
    linea = []
    tmp = u''
    resto = u''
    for palabra in texto:
        if len(tmp) + len(palabra) < largo:
            if len(tmp) == 0:
                tmp = u'' + palabra
            else:
                tmp = tmp + u' ' + palabra
            resto = tmp
        else:
            espacios = largo - len(tmp)
            if espacios < 20:
                posicion = 1
                for i in range(espacios):
                    if posicion >= len(tmp):
                        posicion = 1
                    while tmp[posicion] != u' ':
                        if posicion > len(tmp):
                            posicion = 1
                        posicion += 1
                        if posicion >= len(tmp):
                            posicion = 1

                    tmp = tmp[:posicion] + u' ' + tmp[posicion:]
                    posicion += 2

            linea.append(tmp)
            tmp = u'' + palabra
    if len(resto) > 0:
        linea.append(tmp)
    return linea


def ind_anual(usuario, aa):
    indAnual = 0
    contador = 0
    datAnual = EvalEncab.objects.filter(usuario=usuario, aaa=aa)
    for eval in datAnual:
        if eval.mes < 13:
            indAnual += eval.valor
            contador += 1
    indAnual = (indAnual / contador)
    return indAnual


@login_required(login_url='/ingresar')
def printeval_a(request):
    nombreeval = ''
    MAXLINE = 90
    peso = {'mb': 1, 'b': 0.75, 'r': 0.50, 'm': 0.25}
    orden = ['mb', 'b', 'r', 'm']
    Categorias = {"T": "Técnicos", "O": "Operarios", "S": "Servicio", "C": "Cuadros", "D": "Directivos"}

    tletra = 8
    evanual = {}
    relac = {'peso': peso, 'orden': orden, 'categorias': Categorias, 'calif': '', 'Tamletra': tletra}
    param = Parametros.objects.all()
    for item in param:
        relac[item.nombre.strip()] = item.valor.strip().replace('\'', '').replace('"', '')
        if item.nombre.find('eva_') >= 0:
            nombre = item.nombre.replace('eva', '').replace('_S', '1').replace('_A', '2').replace('_D', '3')
            evanual[nombre] = int(float(item.valor) * 100)

    orden = sorted(evanual)
    val = {}
    txt = relac['categorias'].strip().split(',')
    for item in txt:
        item = item.split(':')
        val[item[0].strip()] = item[1]
    relac['categorias'] = val
    Categorias = val
    response = ''
    if request.method == 'GET':
        aa = request.GET.get('a')
        #mes = 13
        exp = request.GET.get('evaluado')
        #evaluador = request.GET.get('evaluador')
        udata = Data_User.objects.get(noexp=exp)
        nombre = udata.nombre
        cargo = udata.cargo.nombre
        periodo = aa
        categoria = Categorias[udata.categoria]

        area = udata.area.nombre
        evalencab = EvalEncab.objects.get(usuario=udata, mes=13, aaa=aa)
        #indc = {}
        descind_a = Ind_A.objects.all()
        evaldic = {}
        encabdic = {}
        piedic = {}

        for ind in descind_a:
            listatxt = []
            try:
                eval_a = Evaluacion_a.objects.get(encab=evalencab, indaa=ind)
                if len(eval_a.eval) > MAXLINE:
                    listatxt = cortar(MAXLINE, eval_a.eval)
                else:
                    listatxt.append(eval_a.eval)
            except:
                listatxt = []
            nodo = {}
            nombrelst = []
            if len(ind.nombre) > MAXLINE:
                nombrelst = cortar(MAXLINE, ind.nombre)
            else:
                nombrelst.append(ind.nombre)

            nodo['nombre'] = nombrelst
            nodo['eval'] = listatxt

            if ind.orden in [0, 1]:
                encabdic[ind.orden] = nodo
            if ind.orden in [2, 3, 4, 5, 6, 7, 8, 9]:
                evaldic[ind.orden] = nodo
            if ind.orden in [10, 11]:
                piedic[ind.orden] = nodo

        nombreeval = nombre.split(' ')[0] + '_' + exp + '_res-anual-' + aa
        rpt = Report()
        response = rpt.preparar(encab=relac['Encab'], pie=relac['Pie'], nombreeval=nombreeval)

        rpt.letra("Helvetica-Bold", tletra + 5)
        rpt.origen(35, 800)
        rpt.escribeln('                                                             ANEXO 2')
        rpt.ysum(2)
        rpt.letra("Helvetica-Bold", tletra + 3)
        rpt.escribeln('      RESUMEN ANUAL INDIVIDUAL DE EVALUACIÓN DEL DESEMPEÑO PARA TRABAJADORES')
        rpt.ysum(2)

        rpt.escribeln(u'                                                                         AÑO ' + aa)

        rpt.ysum(4)
        rpt.escribeln(' ')
        rpt.escribeln('Nombre: ' + nombre)
        rpt.ysum(2)
        rpt.escribeln('Cargo: ' + cargo)
        rpt.ysum(2)
        rpt.escribeln('Categoria: ' + categoria)
        rpt.ysum(2)
        rpt.escribeln('Area: ' + area)
        rpt.ysum(4)
        # rpt.next()
        rpt.escribeln(' ')
        rpt.escribeln('EVALUACIÓN OBTENIDA')

        rpt.letra("Helvetica-Bold", tletra + 2)
        evatxt = ''
        nodo = encabdic[1]
        try:
            eval = int(nodo['eval'][0])
            for item in orden:
                if evanual[item] >= eval:
                    evatxt = item

        except:
            evatxt = ''

        x = 200
        rpt.ysum(4)
        rpt.escribe('Desempeño Laboral Superior')
        if evatxt == '1':
            rpt.escribex(x, '[X]')
        else:
            rpt.escribex(x, '[  ]')
        rpt.escribeln(' ')

        rpt.ysum(4)
        rpt.escribe('Desempeño Laboral Adecuado')
        if evatxt == '2':
            rpt.escribex(x, '[X]')
        else:
            rpt.escribex(x, '[  ]')
        rpt.escribeln(' ')

        rpt.ysum(4)
        rpt.escribe('Desempeño Laboral Deficiente')
        if evatxt == '3':
            rpt.escribex(x, '[X]')
        else:
            rpt.escribex(x, '[  ]')
        rpt.escribeln(' ')

        rpt.ysum(4)

        nodo = encabdic[1]
        rpt.escribeln('Indice Promedio: ' + str(Decimal(nodo['eval'][0]) / 100))
        rpt.ysum(6)
        rpt.escribeln(' ')
        rpt.escribeln('ASPECTOS A DESTACAR:')
        rpt.ysum(4)

        for orden in evaldic:
            nodo = evaldic[orden]
            parrafo = nodo['nombre']
            for linea in parrafo:
                rpt.escribeln(linea)
            rpt.escribeln(' ')
            parrafo = nodo['eval']
            for linea in parrafo:
                rpt.escribeln('    ' + linea)
            rpt.escribeln(' ')
            rpt.escribeln(' ')

        for orden in piedic:
            nodo = piedic[orden]
            parrafo = nodo['nombre']
            anular = False
            for linea in parrafo:
                if linea.find(':') > 0:
                    linea = linea[:linea.find(':')] + '.'
                    anular = True
                    rpt.escribeln(linea)
                if not anular:
                    rpt.escribeln(linea)

            rpt.escribeln(' ')
            parrafo = nodo['eval']
            for linea in parrafo:
                rpt.escribeln('    ' + linea)
            rpt.escribeln(' ')
            rpt.escribeln(' ')
        rpt.escribeln(' ')
        rpt.escribeln(' ')
        rpt.escribeln(' ')
        rpt.escribeln(' ')
        rpt.escribex(90, 'Firma del Evaluado ')
        rpt.escribex(350, 'Firma del Evaluador ')
        rpt.ysum(2)
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.ysum(2)
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        rpt.escribex(90, 'Fecha : ' + fecha)

        rpt.finaliza()
    return response

    evalencab = EvalEncab.objects.get(usuario=udata, mes=mes, aaa=aa)
    #eval = Evaluacion_a.objects.filter(encab=evalencab)

    #ldata = []
    #lineas = []
    rpt.escribe('')
    rpt.escribe('')
    rpt.letra("Helvetica-Bold", tletra + 3)
    rpt.escribe('Indicadores')
    rpt.escribe('')
    limlinea = 88
    indice = {}
    total = 0

    for ind in indgen:
        indice[ind.id] = {}
        indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=udata)
        valores = []
        sumeval = 0
        contador = 0
        real = 0
        for ie in indesp:
            #valor = ''
            nodo = {}

            try:
                teval = Evaluacion.objects.get(encab=evalencab, ind_esp=ie)
                valor = calif[teval.eval]
                nodo['calif'] = valor
                nodo['valor'] = peso[teval.eval]
                nodo['peso'] = ie.peso
                nodo['real'] = ie.peso * peso[teval.eval]
                real += nodo['real']
                valores.append(nodo)
                sumeval += nodo['valor']
                contador += 1

            except:
                valor = '?'
        indicador = {}
        indicador['peso'] = ind.peso
        indicador['valores'] = valores
        indicador['suma'] = sumeval
        indicador['real'] = real

        if contador == 0:
            resultado = 0
        else:
            resultado = real  # sumeval/contador

        indicador['resultado'] = resultado
        for itempeso in orden:
            if peso[itempeso] >= resultado:
                indicador['resultado'] = calif[itempeso]
        indice[ind.id] = indicador
        total = total + indicador['real'] * indicador['peso']

    rfinaltxt = ''
    rfinal = total  # rfinal/rfinalc
    for itempeso in orden:
        if peso[itempeso] >= rfinal:
            rfinaltxt = calif[itempeso]

    for ind in indgen:

        datanodo = {}
        datanodo['id'] = ind.id
        datanodo['nombre'] = ind.nombre
        valindicador = indice[ind.id]
        print valindicador
        sumeval += valindicador['suma']
        contador += 1
        rpt.letra("Helvetica-Bold", tletra + 3)
        y = rpt.yval()
        rpt.escribe(ind.nombre.strip())
        rpt.letra("Helvetica", tletra + 2)
        rpt.escribe_xy(430, y, valindicador["resultado"])
        rpt.ysum(2)

        indesp = Ind_Esp.objects.filter(ind_gen=ind.id, usuario=udata)
        for ie in indesp:
            rpt.letra("Helvetica", tletra + 2)
            valor = ''
            try:
                teval = Evaluacion.objects.get(encab=evalencab, ind_esp=ie)
                valor = calif[teval.eval]
            except:
                valor = '?'

            y = rpt.yval()
            ie.nombre = ie.nombre.strip()
            rpt.escribe(u'      \u2022 ' + ie.nombre[:limlinea])

            # rpt.letra("Helvetica", 8)
            rpt.escribe_xy(450, y, valor)
            # rpt.letra("Helvetica", 9)
            if len(ie.nombre) > limlinea:
                txt = ie.nombre[limlinea:]
                while len(txt) >= limlinea:
                    rpt.escribe('       ' + txt[:limlinea])
                    txt = txt[limlinea:]
                rpt.escribe('       ' + txt)
            rpt.ysum(4)
        rpt.ysum(4)
    rpt.escribe('')
    rpt.escribe('')
    rpt.letra("Helvetica-Bold", tletra + 2)
    rpt.escribe('Resultado final:  ' + rfinaltxt)
    rpt.escribe('')
    rpt.escribe(u'Indice de desempeño:  ' + str(total))

    rpt.escribe('')
    rpt.letra("Helvetica-Bold", tletra + 2)
    rpt.escribe('Observaciones')
    rpt.letra("Helvetica", tletra)
    rpt.escribe('')

    observ = observ.split('\r\n')
    limlinea = 120

    for lines in observ:
        txt = lines
        if len(txt) > limlinea:
            while len(txt) >= limlinea:
                rpt.escribe('       ' + txt[:limlinea])
                txt = txt[limlinea:]
        lines = "       " + txt
        rpt.escribe(lines)
    rpt.letra("Helvetica-Bold", tletra + 2)
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('Firma del Evaluado.')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('')
    rpt.escribe('Firma del Evaluador')

    rpt.finaliza()
    return response


@login_required(login_url='/ingresar')
def titulo(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""
    if request.user.is_authenticated():
        username = request.user.username
        uid = request.user.id
        usr1 = User.objects.get(pk=uid)
        #addd = usr1.cargo
        nombre = ""
        apellidos = ""
        cargo = ""
    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['Nombre'] = nombre
    c['Apellidos'] = apellidos
    c['Cargo'] = cargo
    return render_to_response('titulo.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def central(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""
    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""
    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['Nombre'] = nombre
    c['Apellidos'] = apellidos
    c['Cargo'] = cargo
    return render_to_response('central.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def configurar(request):
   # defparam = ["peso", "orden", "categorias", "calif", "Tamletra", "EvAnual", "Pie", "Encab"]

    #username = ""
    #nombre = ""
    #apellidos = ""
    #cargo = ""
    c = {}
    c['STATIC_URL'] = '/static/'
    c.update(csrf(request))
    if request.method == 'GET':
        parametros = Parametros.objects.all()
        for item in parametros:
            c[item.nombre] = item.valor.replace('"', '').replace("'", "").strip()

  #      tmpeso = c["peso"].split(',')
        #peso = {}
  #      for item in tmpeso:
  #          item = item.split(':')
  #          c['peso' + item[0].upper()] = item[1].replace(',','.')

   #     tmpeso = c["EvAnual"].split(',')
        # peso = {}
  #      for item in tmpeso:
  #          item = item.split(':')
  #          c['eva_' + item[0][0]] = item[1].replace(',','.')



        return render_to_response('Config.html', c,
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        for item in request.POST:
            if item.find('csrf') >= 0:
                item = ''
            else:
                val = request.POST[item]
                try:
                    parametro = Parametros.objects.get(nombre=item)
                except:
                    parametro = Parametros.objects.create(nombre=item, valor=val)


                parametro.valor = val
                parametro.save()
        transaction.commit()
    return HttpResponseRedirect('/usuarios/')


@login_required(login_url='/ingresar')
def indesp(request):
    #cargoid = -1
    indgenid = -1
    if request.method == 'GET':
        usuarioid = request.GET.get('usuario')
        indgenid = request.GET.get('indgen')
        dataindesp = Ind_Esp.objects.filter(ind_gen=indgenid, usuario=usuarioid)

#    if request.user.is_authenticated():
#        username = request.user.username
#        nombre = request.user.first_name
#        apellidos = request.user.last_name
#        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = usuarioid
    c['indgen'] = indgenid
    c['ind_esp'] = dataindesp
    c['STATIC_URL'] = '/static/'
    return render_to_response('IndEsp.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def indesp_ver(request):
    #indespid = -1
    peso = 0
    if request.method == 'GET':
        indespid = int(request.GET.get('id'))
        usuarioid = request.GET.get('usuario')
        indgenid = request.GET.get('indgen')
        dataindesp = {}
        dataindesp['peso'] = '0.0'
        dataindesp['id'] = indespid
        dataindesp['nombre'] = ''
        dataindesp['orden'] = 0
        dataindesp['lineas'] = 1
        if indespid >= 0:
            dataindesp = Ind_Esp.objects.get(id=indespid)
            # if len(dataindesp['nombre']) > 50 :
            #        dataindesp['lineas'] = divmod(len(dataindesp['nombre']), 50)
            peso = dataindesp.peso
            dataindesp.peso = str(dataindesp.peso).replace(',', '.')

    total = 0
    todos = Ind_Esp.objects.filter(ind_gen=Ind_Gen.objects.get(id=indgenid),
                                   usuario=Data_User.objects.get(id=usuarioid))
    for item in todos:
        total += item.peso
    total -= peso
    total = 1.0 - total

    #if request.user.is_authenticated():
    #    username = request.user.username
    #    nombre = request.user.first_name
    #    apellidos = request.user.last_name
    #    cargo = ""
    total = str(total) + '0'

    c = {}
    c.update(csrf(request))
    # c['usuario']=username
    # c['nombre']= nombre
    c['usuario'] = usuarioid
    c['indgen'] = indgenid
    c['indicador'] = dataindesp
    c["pesomax"] = total[:4]
    c['STATIC_URL'] = '/static/'
    return render_to_response('fmindesp.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def indesp_copiar(request):
    if request.method == 'GET':
        desde = int(request.GET.get('desde'))
        para = request.GET.get('para')
        odesde = Data_User.objects.get(id=desde)
        opara = Data_User.objects.get(id=para)

        borrar = Ind_Esp.objects.filter(usuario=opara)
        for item in borrar:
            item.delete()

        transaction.commit()

        datadesde = Ind_Esp.objects.filter(usuario=odesde)
        for item in datadesde:
            indgen = Ind_Gen.objects.get(id=item.ind_gen.id)

            creado = Ind_Esp.objects.create(peso=item.peso,
                                            nombre=item.nombre,
                                            ind_gen=indgen,
                                            usuario=opara,
                                            orden=item.orden)
            creado.save()
        transaction.commit()
    return HttpResponseRedirect('')


@login_required(login_url='/ingresar')
def modindesp(request):
    #indespid = -1
    if request.method == 'POST':
        indespid = int(request.POST.get('id'))
        usuarioid = request.POST.get('usuario')
        indgenid = request.POST.get('indgen')
        nombreval = request.POST.get('nombre')
        pesomax = request.POST.get('pesomax')
        pesoval = request.POST.get('peso')
        pesoval = float(pesoval.replace(',', '.').replace(' ', ''))
        orden = request.POST.get('orden')
        pesomax = float(pesomax)
        if pesomax < pesoval:
            pesoval = pesomax

        if indespid >= 0:
            dataindesp = Ind_Esp.objects.get(id=indespid)
            dataindesp.nombre = nombreval
            dataindesp.peso = pesoval
            dataindesp.orden = orden
        else:
            indgenobj = Ind_Gen.objects.get(id=indgenid)
            usuarioobj = Data_User.objects.get(id=usuarioid)
            dataindesp = Ind_Esp.objects.create(peso=pesoval,
                                                nombre=nombreval,
                                                ind_gen=indgenobj,
                                                usuario=usuarioobj,
                                                orden=orden)
        dataindesp.save()
        return HttpResponseRedirect('/indesp/?usuario=' + usuarioid + '&indgen=' + indgenid)


@login_required(login_url='/ingresar')
def borrindesp(request):
    #indespid = -1
    if request.method == 'GET':
        indespid = int(request.GET.get('id'))
        usuario = request.GET.get('usuario')
        indgenid = request.GET.get('indgen')

        if indespid >= 0:
            dataindesp = Ind_Esp.objects.get(id=indespid)
            dataindesp.delete()

        return HttpResponseRedirect('/indesp/?usuario=' + usuario + '&indgen=' + indgenid)


@login_required(login_url='/ingresar')
def indgen(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""
    buscar = request.GET.get('buscar')
    if buscar is not None:
        indgen = Ind_Gen.objects.filter(nombre__startswith=buscar)
        pag = 1
    else:
        indgen = Ind_Gen.objects.all()
        pag = request.GET.get('pag')

    paginator = Paginator(indgen, 10)

    try:
        indicadores = paginator.page(pag)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        indicadores = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        indicadores = paginator.page(paginator.num_pages)

    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['nombre'] = nombre
    c['apellidos'] = apellidos
    c['cargo'] = cargo
    c['indicadores'] = indicadores
    c['STATIC_URL'] = '/static/'
    return render_to_response('NomIndGen.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def borrindgen(request):
    #indespid = -1
    if request.method == 'GET':
        indgen = request.GET.get('id')
        if indgen >= 0:
            dataindgen = Ind_Gen.objects.get(id=indgen)
            indesp = Ind_Esp.objects.filter(ind_gen=dataindgen)
            if len(indesp) == 0:
                dataindgen.delete()

    return HttpResponseRedirect('/indgen/')


@login_required(login_url='/ingresar')
def dataindgen(request):
    data = {}
    data["nombre"] = ""
    data["peso"] = 0
    data["id"] = -1

    if request.method == 'POST':
        indicador = int(request.POST["id"])
        pnombre = request.POST["nombre"]
        ppeso = float(request.POST["peso"].replace(',', '.').replace(' ', ''))
        pesomax = float(request.POST["maxval"])

        if pesomax < ppeso:
            ppeso = pesomax

        if indicador >= 0:
            b = Ind_Gen.objects.get(id=indicador)
            b.nombre = pnombre
            b.peso = ppeso
            b.save()
        else:
            b = Ind_Gen.objects.create(nombre=pnombre, peso=ppeso)
            b.save()
            transaction.commit()

        return HttpResponseRedirect('/indgen/')
    peso = 0
    if request.method == 'GET':
        indicador = request.GET.get('id', '')
        if indicador != "":
            data = Ind_Gen.objects.get(id=indicador)
            peso = data.peso

    ind = Ind_Gen.objects.all()
    peso_total = 0
    for item in ind:
        peso_total += item.peso

    peso_total -= peso
    peso_total = 1 - peso_total
    c = {}
    c.update(csrf(request))
    c['indicador'] = data
    c['pesototal'] = str(peso_total)[:4]
    return render_to_response('fmindgen.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def guardaindgen(request):
    #indicador = ""
    #result = ""
    data = {}
    if request.method == 'GET':
        indicador = request.GET.get('id', '')
        if indicador != "":
            data = Ind_Gen.objects.get(id=indicador)
        else:
            data["id"] = -1
            data["nombre"] = ""
            data["peso"] = ""

    c = {}
    c.update(csrf(request))
    c['indicador'] = data
    return render_to_response('fmindgen.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def cargos(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""
    buscar = request.GET.get('buscar')

    if buscar is not None:
        if buscar == '':
            dcargos = Cargo.objects.all()
        else:
            dcargos = Cargo.objects.filter(nombre__contains=buscar)
        pag = 1
    else:
        dcargos = Cargo.objects.all()
        pag = request.GET.get('pag')
    paginator = Paginator(dcargos, 15)

    try:
        pagina = paginator.page(pag)
    except PageNotAnInteger:
        pagina = paginator.page(1)
    except EmptyPage:
        pagina = paginator.page(paginator.num_pages)

    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['nombre'] = nombre
    c['apellidos'] = apellidos
    c['cargo'] = cargo
    c['cargos'] = pagina
    c['buscar'] = buscar
    c['STATIC_URL'] = '/static/'
    return render_to_response('nomcargo.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def guardar_cargo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        idcargo = int(request.POST.get('id'))
        try:
            OCargo = Cargo.objects.get(id=idcargo)
        except:
            OCargo = Cargo.objects.create(nombre=nombre)
        OCargo.save()
    return HttpResponseRedirect('/cargos/')


@login_required(login_url='/ingresar')
def ver_cargo(request):
    if request.method == 'GET':
        idcargo = int(request.GET.get('id'))
        ocargo = Cargo.objects.get(id=idcargo)
    c = {}
    c.update(csrf(request))
    c['Cargo'] = ocargo

    return render_to_response('fmcargo.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def seleccionar_usuario_ie(request):
    user = ''

    if request.method == 'GET':
        usuarioid = request.GET.get('id', '')
        Usuario = Data_User.objects.get(id=usuarioid)
        evaluadorexp = request.GET.get('evaluador', '')
        evaluador = Data_User.objects.get(noexp=evaluadorexp)
        indgen = Ind_Gen.objects.all()
        if request.user.is_authenticated():
            user = request.user

    #expeval = evaluadorexp
    datevaluador = Arbol_eval.objects.filter(evaluador=evaluadorexp)
    sujetos = Data_User.objects.all().order_by('nombre')
    data = []
    for item in sujetos:
        for ev in datevaluador:

            if (item.noexp == ev.evaluado_exp) and (item.noexp != Usuario.noexp):
                nodo = {}
                nodo['id'] = item.id
                nodo['noexp'] = item.noexp
                nodo['nombre'] = item.nombre
                data.append(nodo)

    c = {}
    c.update(csrf(request))
    c['evaluador'] = evaluador
    c['copiar'] = data
    c['usuario'] = Usuario
    c['user'] = user
    c['primero'] = indgen[0]
    c['indgen'] = indgen
    c['STATIC_URL'] = '/static/'
    return render_to_response('usindesp.html', c,
                              context_instance=RequestContext(request))

#@gzip_page
@login_required(login_url='/ingresar')
def usuarios(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""
    tipo = '1'
    buscar = request.GET.get('buscar')
    if buscar is not None:
        data = Data_User.objects.filter(nombre__startswith=buscar, activo = True).order_by('nombre')
        pag = 1
    else:
        if 'tipo' in request.GET:
            tipo = request.GET.get('tipo')
        else:
            tipo = '1'
        ok = True

        if tipo == '1':
            data = Data_User.objects.filter(activo = True).order_by('nombre')

        if tipo == '2':
            data = Data_User.objects.filter(evaluador=ok,activo = True)
            for item in data:
                eval = Arbol_eval.objects.filter(evaluador=item.noexp)
                if len(eval) > 0:
                    user = Data_User.objects.get(noexp=item.noexp)
                    user.evaluador = True
                    user.save()
                else:
                    user = Data_User.objects.get(noexp=item.noexp)
                    user.evaluador = False
                    user.save()

            #data = Data_User.objects.filter(evaluador=ok)

        if tipo == '3':
            data = Data_User.objects.filter(evaluado=False, activo=True)

        if tipo == '4':
            data = Data_User.objects.filter(admin=ok, activo=True)

        if tipo == '5':
            data = Data_User.objects.filter(activo=False)

        pag = request.GET.get('pag')

    paginator = Paginator(data, 15)

    try:
        pagina = paginator.page(pag)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        pagina = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        pagina = paginator.page(paginator.num_pages)

    for item in pagina.object_list:
        existe = Arbol_eval.objects.filter(evaluador=item.noexp)
        if len(existe) > 0:
            item.ok = True
        else:
            item.ok = False

    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['nombre'] = nombre
    c['apellidos'] = apellidos
    c['cargo'] = cargo
    c['tipo'] = tipo
    c['usuarios'] = pagina
    c['STATIC_URL'] = '/static/'
    return render_to_response('usuarios.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def borrar_usuario(request):
    username = ""
    nombre = ""
    apellidos = ""
    cargo = ""

    data = Data_User.objects.all()

    paginator = Paginator(data, 15)
    pag = request.GET.get('pag')
    try:
        pagina = paginator.page(pag)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        pagina = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        pagina = paginator.page(paginator.num_pages)

    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['nombre'] = nombre
    c['apellidos'] = apellidos
    c['cargo'] = cargo
    c['usuarios'] = pagina
    c['STATIC_URL'] = '/static/'
    return render_to_response('usuarios.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def d_usr(request):
    if request.method == 'GET':
        noexp = request.GET.get('noexp')
        Usuario = Data_User.objects.get(noexp=noexp)
        activo = not Usuario.activo
        Usuario.activo = activo
        Usuario.save()
        usr = User.objects.get(username=noexp)
        usr.is_active = activo
        usr.save()
        transaction.commit()
    return HttpResponseRedirect('/usuarios/')


@login_required(login_url='/ingresar')
def guardar_usuario(request):
    tipo = u'1'
    pag = u'1'

    if request.method == 'POST':
        acceso = False
        if 'acceso' in request.POST:
            acceso = request.POST.get('acceso')
            if acceso == u'on':
                acceso = True
            else:
                acceso = False
        pag = request.POST.get('pag')
        tipo = request.POST.get('tipo')
        area = request.POST.get('area')
        categoria = request.POST.get('categoria')
        cargo = request.POST.get('cargo')
        cid = request.POST.get('cid')
        noexp = request.POST.get('noexp')
        uswinid = request.POST.get('uid')
        cpl = request.POST.get('cpl')
        if cpl == u'on':
            cpl = True
        else:
            cpl = False
        noexp = noexp.strip()
        noexp = "00000"[:6 - len(noexp)] + noexp
        nombre = request.POST.get('nombre')
        idusr = int(request.POST.get('id'))
        cargo = Cargo.objects.get(id=cargo)
        area = Areas.objects.get(id=area)

        try:
            Usuario = Data_User.objects.get(noexp=noexp)
        except Exception as e:
            Usuario = None

        if Usuario is not None:
            Usuario.cid = cid
            Usuario.nombre = u'' + nombre
            if noexp == u'040222':
                acceso = True
                Usuario.admin = False
            else:
                Usuario.admin = acceso
            Usuario.categoria = categoria
            Usuario.noexp = noexp
            Usuario.area = area
            Usuario.uid = uswinid
            Usuario.cargo = cargo
            Usuario.cpl = cpl

        else:
            Usuario = Data_User.objects.create(noexp=noexp, cid = cid, nombre = nombre, activo = True, \
                                               categoria = categoria, uid = ' ', evaluador = False, \
                                               evaluado = False, admin = acceso, cargo = cargo, area = area, cpl= False)
        Usuario.save()

        try:
            usr = User.objects.get(username=noexp)
            usr.is_superuser = acceso
        except Exception as e:
            usr = User.objects.create(username = noexp, password = '', is_superuser = acceso, first_name = '', \
                                      last_name = '', email = '', is_staff = False, is_active = True)
        usr.save()
        transaction.commit()

    return HttpResponseRedirect('/usuarios/?pag='+pag+'&tipo='+tipo)


@login_required(login_url='/ingresar')
def usuario(request):
    #userid = ""
    #result = ""
    #areas = []
    data = []
    su = False
    areas = []
    pag = u'1'
    tipo = u'1'
    #cargos = ''
    if request.method == 'GET':
        userid = request.GET.get('id', '')
        pag = request.GET.get('pag', '')
        tipo = request.GET.get('tipo', '')

        oareas = Areas.objects.all()
        if userid != '-1':
            data = Data_User.objects.get(id=userid)
            try:
                usr = User.objects.get(username=data.noexp)
            except Exception as e:
                usr = User.objects.create(username=data.noexp, password='', is_superuser=False, first_name='', \
                                          last_name='', email='', is_staff=True, is_active=True)
            usr.save()
            transaction.commit()



            su = usr.is_superuser
            for area in oareas:
                if area.id != data.area.id:
                    nodo = {}
                    nodo['id'] = area.id
                    nodo['nombre'] = area.nombre
                    areas.append(nodo)
        else:
            data = {}
            data['id'] = -1
            data['noexp'] = ''
            data['cid'] = ''
            data['nombre'] = ''
            data['acceso'] = 'U'
            data['categoria'] = ''
            data['cargo'] = ''
            data['area'] = ''
            data['uid'] = ''
            data['cpl'] = False

            areas = oareas



    cargos = Cargo.objects.all()

    c = {}
    c.update(csrf(request))
    c['pag'] = pag
    c['tipo'] = tipo
    c['usuario'] = data
    c['su'] = su
    c['cargos'] = cargos
    c['areas'] = areas
    return render_to_response('fmusuario.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def usuario_email(request):
    #userid = ""
    #result = ""
    #areas = []
    data = []
    su = False
    areas = []
    texto = 'ok'
    if request.method == 'GET':
        exp = request.GET.get('exp', '')
        exp = exp.zfill(6)
        if exp != '-1':
            data = Data_User.objects.get(noexp=exp)
            usr = User.objects.get(username=data.noexp)
            evaluados = []
            evaluador = {}
            evaluadospor(exp, evaluados, evaluador)
            texto = 'mailto:' + data.uid + codecs.decode('@cimex.com.cu?subject=Evaluación de Trabajadores', 'latin-1')
            texto = texto + '&body= Para evaluar a sus subordinados debe conectarse al siguiente url %0A http://fiw-servcomb.cimex.com.cu:8000/ %0A y acceder con su usuario y clave de red'



  #  "mailto:me@example.com"
  #                           + "?cc=myCCaddress@example.com"
  #                           + "&subject=" + escape("This is my subject")
 #                            + "&body=" + escape("texto " )
 #                   ;

    return HttpResponse(texto)


def evaluadospor(userexp, data, evaluador):
    datevaluador = Arbol_eval.objects.all()

    userev = []

    #evalua = {}
    for evl in datevaluador:
        if evl.evaluador == userexp:
            datatmp = {}
            datatmp['noexp'] = evl.evaluado_exp
            datatmp['evaluador'] = evl.evaluador
            userev.append(datatmp)

    sujetos = Data_User.objects.all().order_by('nombre')

    #udata = {}
    for sujeto in sujetos:
        for usrdata in userev:
            if usrdata['noexp'] == sujeto.noexp:
                udata = {}
                udata['id'] = sujeto.id
                udata['cid'] = sujeto.cid
                udata['nombre'] = sujeto.nombre
                udata['cargo'] = sujeto.cargo.nombre
                udata['cargoid'] = sujeto.cargo.id
                udata['categoria'] = sujeto.categoria
                udata['noexp'] = sujeto.noexp
                #   ind = Ind_Esp.objects.filter(cargo=sujeto.cargo.id)
                #   if len(ind) == 0:
                #        udata['completo'] = False
                #    else:
                udata['completo'] = True

                data.append(udata)
        if userexp == sujeto.noexp:
            evaluador['id'] = sujeto.id
            evaluador['cid'] = sujeto.cid
            evaluador['noexp'] = sujeto.noexp
            evaluador['nombre'] = sujeto.nombre
            evaluador['cargo'] = sujeto.cargo.nombre
            evaluador['cargoid'] = sujeto.cargo.id
            evaluador['categoria'] = sujeto.categoria
            evaluador['cpl'] = sujeto.cpl
    return


def noevaluados(data, exp):
    datevaluador = Arbol_eval.objects.all()
    sujetos = Data_User.objects.all().order_by('nombre')

    for sujeto in sujetos:
        evalua = {}
        evalua['m'] = True
        for evl in datevaluador:
            if evl.evaluado_exp == sujeto.noexp:
                evalua['m'] = False
        if exp == sujeto.noexp:
            evalua['m'] = False
        if evalua['m'] == True:
            # evalua['cargo'] = sujeto.cargo.nombre
            evalua['cid'] = sujeto.cid
            evalua['noexp'] = sujeto.noexp
            evalua['nombre'] = sujeto.nombre
            data.append(evalua)
    return


@login_required(login_url='/inicio/')
def seleccionar_usuario(request):
    userexp = ""
    #result = ""
    #sujetos = ""
    data = []

    evaluador = {}
    if request.method == 'GET':
        userexp = request.GET.get('exp', '')
        #user = request.GET.get('user', '')
        addusr = request.GET.get('usuarios', '')
        if addusr != "":
            dataev = Data_User.objects.get(noexp=userexp)
            dataev.evaluador = True
            dataev.save()

            addusr = addusr.replace(' ', '').split(',')
            for adduno in addusr:
                b = Arbol_eval.objects.create(evaluador=userexp, evaluado_exp=adduno)
                b.save()

                dataev = Data_User.objects.get(noexp=adduno)
                dataev.evaluado = True
                dataev.save()

            evaluadospor(userexp, data, evaluador)
            c = {}
            c.update(csrf(request))
            c['sujetos'] = data
            c['STATIC_URL'] = '/static/'
            # return HttpResponseRedirect('/seleccionar_usuario/?exp='+userexp)
            return render_to_response('usuariosaevaluar.html', c,
                                      context_instance=RequestContext(request))
        else:
            evaluadospor(userexp, data, evaluador)
    c = {}
    c.update(csrf(request))
    c['evaluador'] = evaluador
    c['sujetos'] = data
    c['user'] = userexp
    c['STATIC_URL'] = '/static/'
    return render_to_response('selusuario.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def faddeval_usuario(request):
    userexp = ""
    #result = ""
    #sujetos = ""
    #data = []

    noev = []
    #evaluador = {}
    if request.method == 'GET':
        userexp = request.GET.get('exp', '')

    noevaluados(noev, userexp)

    c = {}
    c.update(csrf(request))

    c['evaluador'] = userexp
    c['sineval'] = noev
    return render_to_response('fmselusuario.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def fdeleval_usuario(request):
    #userexp = ""
    #result = ""
    #sujetos = ""

    #noev = []
    #evaluador = {}
    if request.method == 'GET':
        userexp = request.GET.get('exp', '')
        b = Arbol_eval.objects.get(evaluado_exp=userexp)
        expevaluador = b.evaluador
        b.delete()
        transaction.commit()
        b = Arbol_eval.objects.filter(evaluador=expevaluador)
        if b is None:
            dataev = Data_User.objects.get(noexp=expevaluador)
            dataev.evaluador = False
            dataev.save()

        dataev = Data_User.objects.get(noexp=userexp)
        dataev.estado = False
        dataev.save()
    return HttpResponse("ok")


@login_required(login_url='/ingresar')
def addusuariosel(request):
    userexp = ""
    #result = ""
    #sujetos = ""

    noev = []
    #evaluador = {}
    if request.method == 'GET':
        userexp = request.GET.get('exp', '')

    noevaluados(noev, userexp)

    c = {}
    c.update(csrf(request))
    c['evaluador'] = userexp
    c['sineval'] = noev
    return render_to_response('fmselusuario.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def areas(request):
    username = ""
    nombre = ""
    #apellidos = ""
    cargo = ""
    ldata = Areas.objects.all()
    data = []
    for item in ldata:
        if item.id != 1:
            nodo = {}
            nodo['id'] = item.id
            nodo['nombre'] = item.nombre
            data.append(nodo)



    paginator = Paginator(data, 15)
    pag = request.GET.get('pag')
    try:
        pagina = paginator.page(pag)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        pagina = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        pagina = paginator.page(paginator.num_pages)

    if request.user.is_authenticated():
        username = request.user.username
        nombre = request.user.first_name
        apellidos = request.user.last_name
        cargo = ""

    c = {}
    c.update(csrf(request))
    c['usuario'] = username
    c['nombre'] = nombre
    c['cargo'] = cargo
    c['areas'] = pagina
    c['STATIC_URL'] = '/static/'
    return render_to_response('areas.html', c,
                              context_instance=RequestContext(request))

@login_required(login_url='/ingresar')
def areastrabaj(request):
    lareas = Areas.objects.all()
    areas = []
    selec = ''
    for item in lareas:
        if item.id != 1:
            area = {}
            if selec == '':
                selec = str(item.id)

            area['id'] = item.id
            area['nombre'] = item.nombre
            areas.append(area)


    if request.method == 'GET':
        if 'area' in request.GET:
            selec = request.GET.get('area', '')



    c = {}
    c.update(csrf(request))
    c['areas'] = areas
    c['ids'] = selec
    c['frame'] = '/areastrabajlst/?id=' + selec
    c['STATIC_URL'] = '/static/'
    return render_to_response('areastrabaj.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def areastrabajlst(request):
    if request.method == 'GET':
        areaid = request.GET.get('id', '')
        area = Areas.objects.get(id=areaid)
        trabajadores = Data_User.objects.filter(area=area)
        c = {}
        c.update(csrf(request))
        c['trabajadores'] = trabajadores
        c['areaid'] = areaid
        c['STATIC_URL'] = '/static/'
        return render_to_response('areatrabajlst.html', c,
                                  context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def areatrabjquitar(request):
    if request.method == 'GET':
        area = Areas.objects.get(id='1')
        noexp = request.GET["noexp"]
        noexp = noexp.zfill(6)
        datauser = Data_User.objects.get(noexp=noexp)
        datauser.area = area
        datauser.save()
        return HttpResponse("ok")



@login_required(login_url='/ingresar')
def areatrabajadfm(request):
    if request.method == 'POST':
        areaid = request.POST["id"]
        area = Areas.objects.get(id=areaid)
        trabaj = request.POST["usuarios"]
        trabaj = trabaj.split(',')
        for item in trabaj:
            datauser = Data_User.objects.get(noexp=item)
            datauser.area = area
            datauser.save()

        return HttpResponseRedirect('/areastrabajlst/?id='+areaid)



    if request.method == 'GET':
        areaid = request.GET.get('id', '')
        area = Areas.objects.get(id=areaid)
        datauser = Data_User.objects.all()
        trabajadores = []

        for item in datauser:
            if item.area != area:
                trabajador = {}
                trabajador['id'] = item.id
                trabajador['nombre'] = item.nombre
                trabajador['noexp'] = item.noexp
                trabajador['area'] = item.area
                trabajadores.append(trabajador)



        c = {}
        c.update(csrf(request))
        c['trabajadores'] = trabajadores
        c['area'] = areaid
        c['STATIC_URL'] = '/static/'
        return render_to_response('areastrabajfm.html', c,
                                  context_instance=RequestContext(request))




@login_required(login_url='/ingresar')
def dataarea(request):
    #areaid = ""
    #result = ""
    data = {}
    if request.method == 'GET':
        areaid = request.GET.get('id', '')
        if areaid == '-1':
            data['nombre'] = ''
            data['id'] = '-1'
        else:
            data = Areas.objects.get(id=areaid)

    if request.method == 'POST':
        areaid = int(request.POST["id"])
        pnombre = request.POST["nombre"]

        if areaid >= 0:
            b = Areas.objects.get(id=areaid)
            b.nombre = pnombre
            b.save()
        else:
            b = Areas.objects.create(nombre=pnombre)
            b.save()

        return HttpResponseRedirect('/areas/')

    c = {}
    c.update(csrf(request))
    c['area'] = data
    return render_to_response('fmarea.html', c,
                              context_instance=RequestContext(request))


@login_required(login_url='/ingresar')
def borrararea(request):
    #areaid = ""
    #result = ""
    #data = {}
    if request.method == 'GET':
        areaid = request.GET.get('id', '')
        data = Areas.objects.get(id=areaid)
        usuarios = Data_User.objects.filter(area=data)
        if len(usuarios) == 0:
            try:
                data.delete()
            except:
                error = 'Imposible Borrar Area'
                return HttpResponseRedirect('/areas/')

    return HttpResponseRedirect('/areas/')


@login_required(login_url='/ingresar')
def cambia_clave(request):
    logged = request.user
    logged = User.objects.get(username=logged)

    if request.method == 'POST':
        exp = request.POST["userexp"]
        usuario = Data_User.objects.get(noexp=exp)
        usr = User.objects.get(username=exp)
        if "old_password" in request.POST:
            old_password = request.POST["old_password"]
        else:
            old_password = ''
        new_password1 = request.POST["new_password1"]
        new_password2 = request.POST["new_password2"]

        if logged.is_superuser or (check_password(old_password, usr.password)):
            if new_password1 == new_password2:
                usr.set_password(new_password1)
                usr.save()
                return HttpResponseRedirect('/usuarios/')
            else:
                error = True
        else:
            error = True

    if request.method == 'GET':
        exp = request.GET["exp"]
        usuario = Data_User.objects.get(noexp=exp)

    c = {}
    c.update(csrf(request))
    c['usuario'] = usuario
    c['su'] = logged.is_superuser
    return render_to_response('cclave.html', c,
                              context_instance=RequestContext(request))


def loclogout(request):
    try:
        #if request.user.is_authenticated():

        #    request.user.

      #  request.session.delete(request.session.session_key)
        del request.session['username']
        logout(request)
    except KeyError:
        pass
    return HttpResponse("Aplicación terminada")


def ayuda(request):
    c = {}
    c.update(csrf(request))
    c['STATIC_URL'] = '/static/'

    if request.method == 'GET':
        id = int(request.GET.get('id'))
        dir = request.GET.get('dir')
        if id >= 0:
            if id >= 49:
                id = 49
            continuar = True
            while continuar:
                try:
                    ayuda = Ayuda.objects.get(item=id)
                    continuar = False
                except:
                    if dir == 'd':
                        id += 1
                    else:
                        id -= 1

            c['siguiente'] = id + 1
            if id >= 1:
                c['anterior'] = id - 1
            else:
                c['anterior'] = 0
            alto = ayuda.alto
            if alto == 0:
                alto = 100
            largo = ayuda.largo
            if largo == 0:
                largo = 100
            #texto = ayuda.texto
            texto = ayuda.texto
            c['texto'] = texto
            texto = texto.split('/r')

            c['parrafos'] = texto
            c['imagen'] = ayuda.imagen
            c['alto'] = alto
            c['largo'] = largo
            c['item'] = ayuda.item

            return render_to_response('ayuda.html', c)
    else:
        return render_to_response('framesAyuda.html', c)


def gayuda(request):
    c = {}
    c.update(csrf(request))
    c['STATIC_URL'] = '/static/'

    if request.method == 'POST':
        item = int(request.POST.get('item'))
        texto = request.POST.get('texto')
        ayuda = Ayuda.objects.get(item=item)
        ayuda.texto = texto
        ayuda.save()
        transaction.commit()

    return HttpResponseRedirect('/a/?id=' + str(item))
