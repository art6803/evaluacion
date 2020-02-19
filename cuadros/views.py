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
from django.shortcuts import render
from django.template import RequestContext
from django.template.context_processors import csrf


import codecs

from eval.models import Data_User, EvalEncab, Parametros, Areas
from cuadros.models import Ind_Cuadro, EvaluacionCuadro
from reporte.rcls import Report, separaln, cortar

from reporte import Syllabification


def indicadores(request):
    indcuadro = Ind_Cuadro.objects.all()

    c = {}
    c.update(csrf(request))
    c['indicador'] = indcuadro
    c['STATIC_URL'] = '/static/'
    return render_to_response('NomIndCuad.html', c,
                              context_instance=RequestContext(request))


def indicadoresmod(request):
    if request.method == 'GET':
        indicador = int(request.GET.get('id'))
        operacion = request.GET.get('oper')

        if indicador >= 0:
            dataind = Ind_Cuadro.objects.get(id=indicador)

        if operacion == 'b':
            dataind.delete()
            return HttpResponseRedirect('/indcuad/')

        if operacion == 'e':
            if indicador >= 0:
                dataind = Ind_Cuadro.objects.get(id=indicador)
                c = {}
                c.update(csrf(request))
                c['indicador'] = dataind
                c['STATIC_URL'] = '/static/'
                return render_to_response('fmindcuad.html', c,
                                          context_instance=RequestContext(request))

        if operacion == 'a':
            dataind = {}
            dataind['orden'] = 0
            dataind['peso'] = 0
            dataind['nombre'] = ''
            dataind['id'] = -1
            c = {}
            c.update(csrf(request))
            c['indicador'] = dataind
            c['STATIC_URL'] = '/static/'
            return render_to_response('fmindcuad.html', c,
                                      context_instance=RequestContext(request))

    if request.method == 'POST':
        indicador = int(request.POST.get('id'))
        orden = request.POST.get('orden')
        peso = request.POST.get('peso').replace(',', '.')
        nombre = request.POST.get('nombre')
        if indicador >= 0:
            dataind = Ind_Cuadro.objects.get(id=indicador)
            dataind.orden = orden
            dataind.peso = peso
            dataind.nombre = nombre
        else:
            dataind = Ind_Cuadro.objects.create(nombre=nombre, peso=peso, orden=orden)
        dataind.save()
        transaction.commit()

        return HttpResponseRedirect('/indcuad/')


@login_required(login_url='/ingresar')
def printeval(request):
    if request.method == 'GET':
        mes = int(request.GET.get('mes'))
        if mes == 13:
            return printeval_a(request)
        else:
            return printeval_m(request)



@login_required(login_url='/ingresar')
def printeval_m(request):

    relac = dict(
        peso={'mb': 1, 'b': 0.75, 'r': 0.50, 'm': 0.25},
        orden=['mb', 'b', 'r', 'm'],
        categorias={"T": "Técnicos", "O": "Operarios", "S": "Servicio", "C": "Cuadros", "D": "Directivos"},
        calif={'mb': 'muy bien', 'b': 'bien', 'r': 'regular', 'm': 'mal', 'mm': 'muy mal'},
        Tamletra=8,
        Pie=' ',
        Encab=' ')

    nombreeval = ''
    a4 = 800
    carta = 790
    peso = relac['peso']
    orden = relac['orden']
    Categorias = relac['categorias']

    meses = ["", "Enero-Marzo", "Abril-Junio", "Julio-Septiembre", "Octubre-Diciembre"]
    calif = relac['calif']
    tletra = relac['Tamletra']


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
        evaluador = request.GET.get('evaluador')
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
        indicadorc = Ind_Cuadro.objects.all()
        #ldata = []
        #lineas = []
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.letra("Helvetica-Bold", tletra + 3)
        rpt.escribeln('Indicadores')
        rpt.escribeln('')
        limlinea = 75
        indice = 0
        total = 0
        calif['-'] = '?'
        peso['-'] =  0
        contador = 0






        for ind in indicadorc:

            try:
                teval = EvaluacionCuadro.objects.get(encab=evalencab, indicador=ind)
                eval = teval.eval
            except:
                eval = '-'
            valor = ind.peso * peso[eval]
            indice += valor
            contador += 1
            datanodo = {}
            datanodo['id'] = ind.id
            datanodo['nombre'] = ind.nombre
            rpt.letra("Helvetica", tletra + 3)
            y = rpt.yval()
            ind.nombre = ind.nombre.strip()
            lprint = separaln(ind.nombre, 345, rpt, "Helvetica", tletra + 2, False)
            rpt.escribeln(lprint[0])
            lprint = lprint[1:]
            rpt.escribe_xy(470, y, calif[eval])
            for lines in lprint:
                rpt.escribeln(lines)
            rpt.letra("Helvetica", tletra + 2)

            rpt.ysum(4)

        rfinal = indice
        if rfinal > 1:
            rfinal = 1# rfinal/rfinalc
        for itempeso in orden:
            if peso[itempeso] >= rfinal:
                rfinaltxt = calif[itempeso]


        rpt.ysum(4)
        rpt.escribeln('')
        rpt.escribeln('')
        rpt.letra("Helvetica-Bold", tletra + 2)
        rpt.escribeln('Resultado final:  ' + rfinaltxt)
        rpt.escribeln('')
        rpt.escribeln(u'Indice de desempeño:  ' + str(rfinal))
        evalencab.valor = rfinal * 100
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
        descind_a = {} #Ind_A.objects.all()
        evaldic = {}
        encabdic = {}
        piedic = {}

        for ind in descind_a:
            listatxt = []
            try:
                eval_a = {} #Evaluacion_a.objects.get(encab=evalencab, indaa=ind)
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
def evalcuadro(request):
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

        descind_a = {} #Ind_A.objects.all()
        for ind in descind_a:
            nodo = {}
            evaltxt = ''
            try:
                eval_a = {} #Evaluacion_a.objects.get(encab=evalencab, indaa=ind)
                evaltxt = eval_a.eval
            except:
                evaltxt = ''

            nodo['item'] = ind.id
            nodo['texto'] = ind.nombre
            nodo['eval'] = evaltxt
            if ind.orden == 1:
                nodo['eval'] =''# str(ind_anual(evaluado, aa))

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

    evaluado = Data_User.objects.get(noexp=evaluadoexp)
    evaluador = Data_User.objects.get(noexp=evaluadorexp)
    sololectura = False
    eval = {}
    try:
        evalencab = EvalEncab.objects.get(usuario=evaluado, mes=mes, aaa=aa)
        eval = EvaluacionCuadro.objects.filter(encab=evalencab)
        observ = evalencab.observ
        sololectura = not evalencab.autoeval

    except:
        observ = ""

    cargo = evaluado.cargo.id
    indc = Ind_Cuadro.objects.all()
    indicador = []
    if evaluadorexp != evaluadoexp:
        sololectura = False
    for item in indc:
        nodo ={}
        nodo['nombre'] = item.nombre
        nodo['peso'] = item.peso
        nodo['id'] = item.id
        nodo['selec'] = 'mb'
        for data in eval:
            if data.indicador == item:
                nodo['selec'] = data.eval



        indicador.append(nodo)


    c = {}
    c.update(csrf(request))
    c['evaluado'] = evaluado
    c['evaluador'] = evaluador
    c['indicador'] = indicador
    c['observ'] = observ
    c['sololectura'] = sololectura
    c['aa'] = aa
    # mes +=1
    c['mes'] = mes
    c['nombremes'] = Datames
    c['meses'] = ['Enero-Marzo', 'Abril-Junio', 'Julio-Septiembre', 'Octubre-Diciembre']
    c['STATIC_URL'] = '/static/'
    return render_to_response('evaluacionc.html', c, context_instance=RequestContext(request))

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
        if evaluador != evaluado:
            encab.autoeval = False
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
            indesp = Ind_Cuadro.objects.get(id=int(key))
            valor = request.POST[nkey]
            try:
                teval = EvaluacionCuadro.objects.get(encab=encab, indicador=indesp)
            except EvaluacionCuadro.DoesNotExist:
                teval = EvaluacionCuadro(encab=encab, indicador=indesp, eval=valor)
            teval.eval = valor
            teval.save()
    return HttpResponseRedirect('/evaluar/?exp=' + evaluado + '&evaluador=' + evaluador)

@login_required(login_url='/ingresar')
def vercpl(request):
    if request.method == 'GET':
        userexp = request.GET.get('exp')
        evaluadorexp = request.GET.get('evaluador')
        evaluador = Data_User.objects.get(noexp=evaluadorexp)
        evaluado = Data_User.objects.get(noexp=userexp)
        evaldata = []

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

            i += 1
            lm.append(nm)
        nm = {}
        nm['nombre'] = 'Resumen Anual'
        nm['num'] = 13

        lm.append(nm)
        na['meses'] = lm
        lsta.append(na)

    c = dict(
        evaluado=evaluado,
        evaluador=evaluador,
        aa=lsta,
        STATIC_URL='/static/'
    )
    c.update(csrf(request))
    return render_to_response('calendariocpl.html', c, context_instance=RequestContext(request))


def calculacpl(mes, aa, exp):
    evaluado = True
    udata = Data_User.objects.get(noexp=exp)
    try:
        evalencab = EvalEncab.objects.get(usuario=udata, mes=mes, aaa=aa)
    except:
        evaluado = False


    if evaluado:
        indicadorc = Ind_Cuadro.objects.all()
        peso = {}
        cpl = 0
        param = Parametros.objects.all()
        for item in param:
            if item.nombre.find('peso') >= 0:
                nombre = item.nombre.replace('peso', '')
                peso[nombre.lower()] = float(item.valor.lower().strip())
        valor = 0
        for ind in indicadorc:
            try:
                teval = EvaluacionCuadro.objects.get(encab=evalencab, indicador=ind)
                eval = teval.eval
                valor = ind.peso * peso[eval]
            except:
                eval = '-'


            cpl += valor
        cpl = str(cpl)
    else:
        cpl = "no-eval"

    return cpl

@login_required(login_url='/ingresar')
def imprimircpl(request):

    abrev = {'Departamento': 'Dep.',
             'Gerencia': 'Ger.',
             'Sistemas': 'Sist.',
             'Procedimientos': 'Proced.',
             'Procesamiento': 'Proc.',
             'Empresariales': 'Emp.',
             'Tarjetas' : 'Tarj.',
             'Servicios':'Serv.',
             'Internos' : 'Int.',
             ' de ': ' '
             }

    nombreeval = ''
    a4 = 800
    carta = 790
    peso = {'mb': 1, 'b': 0.75, 'r': 0.50, 'm': 0.25}
    orden = ['mb', 'b', 'r', 'm']
    trimestres = ["", "Enero-Marzo", "Abril-Junio", "Julio-Septiembre", "Octubre-Diciembre"]
    mesesxt = {1: ["Enero", "Febrero","Marzo"],
             2: ["Abril","Mayo","Junio"],
             3: ["Julio","Agosto","Septiembre"],
             4: ["Octubre","Noviembre","Diciembre"]}
    calif = {'mb': 'muy bien', 'b': 'bien', 'r': 'regular', 'm': 'mal', 'mm': 'muy mal'}
    tletra = 8

    relac = {'peso': peso, 'orden': orden,  'calif': calif, 'Tamletra': tletra, 'Pie': ' ',
             'Encab': ' '}

    valpeso = {}
    valcalif = {}
    param = Parametros.objects.all()
    for item in param:
        relac[item.nombre.strip()] = item.valor.strip().replace('\'', '').replace('"', '')
        if item.nombre.find('peso') >= 0:
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

    # calif = val

    # orden
    # val = {}
    relac['orden'] = relac['orden'].strip().lower().split(',')
    orden = relac['orden']

    response = ''
    if request.method == 'GET':
        aa = request.GET.get('a')
        mes = int(request.GET.get('mes'))
        evaluadorexp = request.GET.get('evaluador')
        evaluador = Data_User.objects.get(noexp=evaluadorexp)

        nombreeval = 'cpl_'+ trimestres[mes]+ '_' +aa
        rpt = Report()
        response = rpt.preparar(encab='', pie='', nombreeval=nombreeval)
        rpt.ver(False, False)

        rpt.letra("Helvetica-Bold", tletra + 3)
        rpt.origen(45, carta)
        rpt.margenizq(85)
        rpt.escribeln('REPORTE PARA NOTIFICAR A LA DIRECCIÓN DE CUADROS EL CPL ALCANZADO ')
        rpt.ysum(2)
        rpt.escribeln('POR LOS CUADROS, PARA CALCULAR EL PAGO POR RESULTADOS EN MONEDA ')
        rpt.ysum(2)
        rpt.escribeln('NACIONAL.')
        rpt.ysum(10)
        rpt.margenizq(85)
        rpt.escribeln('Area : EMPRESA ')
        rpt.ysum(10)
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        rpt.escribeln('Fecha : ' + fecha)
        rpt.ysum(10)
        rpt.margenizq(75)
        rpt.letra("Helvetica", tletra + 3)
        meses = mesesxt[mes]
        observ ="El índice reflejado en la tabla es el Coeficiente de Participación Laboral (CPL) resultante de la " \
                "evaluación del desempeño al cierre del {} trimestre del año {}; y es válido para el Pago por " \
                "Resultados de los meses {}, {} y {} del año {}.".format(mes, aa, meses[0], meses[1], meses[2], aa )
        lprint = separaln(observ, 450, rpt, "Helvetica", tletra + 3, True)
        for lines in lprint:
            rpt.escribeln(lines)
        rpt.ysum(24)

        cuadros = Data_User.objects.filter(categoria='C')
        rpt.letra("Helvetica-Bold", tletra + 2)
        inicio = 75
        titulo = "   ÍNDICE DE LA EVALUACIÓN (CPL)"
        rpt.escribexr(15  + inicio, "EXPDTE.", 55)
        rpt.escribexr(70  + inicio, "NOMBRES Y APELLIDOS", 210)
        rpt.escribexr(280 + inicio, "ENTIDAD", 135)
        rpt.escribexr(415 + inicio, "CPL", 45)
        rpt.ysum(16)
        rpt.letra("Helvetica", tletra + 3)
        listado = []
        for item in cuadros:
            listado.append(item)

        #item = cuadros[1]
        #for i in range(200):
        #    listado.append(item)

        contador = 0
        lpp1 = 30
        lppr = lpp1 + 9
        cuadros = len(listado)
        if cuadros  < lpp1:
            cantpag = 1
        else:
            cantpag = int(1 + (round((len(listado) - lpp1) / lppr)))
        paginas = []
        rpt.findepagina(30)
        cuadro = 0
        for pag in range(cantpag):
            pag += 1
            if pag == 1:
                for linea in range(lpp1):
                    if cuadro < cuadros:
                        item = listado[cuadro]
                        area = item.area.nombre
                        for abb in abrev:
                            area = area.replace(abb, abrev[abb])
                        exp = item.noexp
                        nombre = item.nombre
                        cpl = calculacpl(mes, aa, exp)
                        cuadro += 1
                    else:
                        area = ''
                        exp = ''
                        nombre = ''
                        cpl = ''
                    rpt.escribexr(15 + inicio, exp, 55)
                    rpt.escribexr(70 + inicio, nombre, 210)
                    rpt.escribexr(280 + inicio, area, 135)
                    rpt.escribexr(415 + inicio, cpl, 45)
                    rpt.ysum(16)
            else:
                rpt.letra("Helvetica-Bold", tletra + 2)
                rpt.escribeln('Area : EMPRESA             Fecha : ' + fecha + ' ' * 75 + 'pag. '+ rpt.numpagina())
                rpt.ysum(10)
                rpt.letra("Helvetica", tletra + 3)
                for linea in range(lppr):
                    if cuadro < cuadros:
                        item = listado[cuadro]
                        area = item.area.nombre
                        for abb in abrev:
                            area = area.replace(abb, abrev[abb])
                        exp = item.noexp
                        nombre = item.nombre
                        cpl = calculacpl(mes, aa, exp)
                        cuadro += 1
                    else:
                        area = ''
                        exp = ''
                        nombre = ''
                        cpl = ''

                    rpt.escribexr(15  + inicio, exp, 55)
                    rpt.escribexr(70  + inicio, nombre, 210)
                    rpt.escribexr(280 + inicio, area,135)
                    rpt.escribexr(415 + inicio, cpl, 45)
                    rpt.ysum(16)

            rpt.ysum(16)
            rpt.letra("Helvetica-Bold", tletra + 2)
            rpt.escribeln('')
            rpt.escribeln('CERTIFICA:')
            rpt.escribeln('')
            rpt.escribeln('')
            rpt.escribeln('')
            rpt.escribeln('')
            rpt.escribeln('')
            rpt.letra("Helvetica", tletra + 2)
            rpt.escribexls(30 + inicio, "Nombres y Apellidos", 25)
            rpt.escribexls(240 + inicio, "Cargo", 45)
            rpt.escribexls(380 + inicio, "Firma", 35 )
            rpt.cpag()
        rpt.finaliza()
    return response

