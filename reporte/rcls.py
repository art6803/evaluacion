#!/usr/bin/python
# -*- coding: utf8 -*-

# interfase para reportlab
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


from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer, SimpleDocTemplate, Table, TableStyle, Preformatted, PageBreak
from reportlab.lib.pagesizes import letter, A4
from reporte import Syllabification


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


def separaln(entrada, limlinea, rpt, fontname, fontsize, sangria):
    lprint = []
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
                largo = rpt.largotexto(linea + ' ' + txt[0], fontname, fontsize)
                if largo < limlinea:
                    linea = linea + ' ' + txt[0]
                    txt = txt[1:]
                else:
                    silabas = Syllabification.silabas(txt[0])
                    palabra = ''
                    while rpt.largotexto(linea + ' ' + palabra + '- ', fontname,
                                         fontsize) < limlinea:  # and (len(silabas) > 0):
                        palabra = palabra + silabas[0]
                        if len(silabas) > 1:
                            silabas = silabas[1:]
                        else:
                            silabas = []
                            break

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
                    linea = ''
                    nlinea += 1
            if len(linea) > 0:
                lprint.append(linea.strip())

        else:
            lprint.append('')
    largos = []
    espacio = rpt.largotexto(' ', fontname, fontsize)
    maximo = 0
    for item in lprint:
        largo = rpt.largotexto(item, fontname, fontsize)
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
                    if linea == '':
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


class Report():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.inix = 0
        self.iniy = 0
        self.p = 0
        self.alto = 9
        self.nletra = 'Helvetica'
        self.txtpie = ' '
        self.verencab = True
        self.verpie = True

    def preparar(self, encab, pie, nombreeval):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="' + nombreeval + '.pdf"'
        self.p = canvas.Canvas(response, pagesize=A4)  # A4)
        self.width, self.height = letter  # keep for later
        self.txtpie = pie
        self.txtencab = encab
        return response

    def letra(self, letra='Helvetica', alto=9):
        self.p.setFont(letra, alto)
        self.alto = alto
        self.nletra = letra

    def escribe_xy(self, x, y, linea):
        self.p.drawString(x, y, linea)

    def numpagina(self):
        return str(self.p.getPageNumber())

    def piepagina(self):
        pagina = str(self.p.getPageNumber())
        letra = self.nletra
        size = self.alto
        self.letra("Helvetica-Bold", 6)
        self.p.drawString(100, 15, self.txtpie)
        self.letra('Helvetica-Bold', 6)
        self.p.drawString(420, 15, "Pagina: " + pagina)
        self.letra(letra, size)

    def encabpagina(self):
        pagina = str(self.p.getPageNumber())
        letra = self.nletra
        size = self.alto
        self.color(0.7, 0.7, 0.7)
        self.letra("Helvetica-Bold", 8)
        self.p.drawString(56, 820, self.txtencab)
        self.letra(letra, size)
        self.color(0, 0, 0)

    def detlargo(self, texto, fontName, fontSize):
        txt = texto.split()
        resultado = []
        for item in txt:
            largo = self.largotexto(item, fontName, fontSize)
            resultado.append(largo)
        return txt, resultado, self.p.stringWidth(' ', fontName, fontSize)

    def largotexto(self, texto, fontName, fontSize):
        largo = self.p.stringWidth(texto, fontName, fontSize)
        return largo

    def color(self, r, g, b):
        self.p.setStrokeColorRGB(r, g, b)
        self.p.setFillColorRGB(r, g, b)

    def margenizq(self, x):
        self.x = x
        self.inix = x

    def origen(self, x, y):
        self.x = x
        self.y = y
        self.inix = x
        self.iniy = y
        self.final = 30

    def escribeln(self, linea):
        self.escribe_xy(self.x, self.y, linea)
        self.y = self.y - self.alto
        if self.y < self.final:
            self.cpag()

    def escribe(self, linea):
        self.escribe_xy(self.x, self.y, linea)

    def escribex(self, x, linea):
        self.escribe_xy(x, self.y, linea)

    def escribexr(self, x, linea, largo):
        self.escribe_xy(x, self.y, linea)
        self.p.setLineWidth(0.5)
        self.p.rect(x - 4, self.y - 5, largo, 16, fill=0)

    def escribexls(self, x, linea, incremento):
        self.escribe_xy(x, self.y, linea)
        largo = self.p.stringWidth(linea, self.nletra, self.alto)
        self.p.setLineWidth(0.5)
        self.p.line(x - incremento, self.y + self.alto, x + largo + incremento, self.y + self.alto)

    def escribexln(self, x, linea):
        self.escribe_xy(x, self.y, linea)
        self.y = self.y - self.alto
        if self.y < self.final:
            self.cpag()

    def findepagina(self, final):
        self.final = final

    def ver(self, encab, pie):
        self.verencab = encab
        self.verpie = pie

    def cpag(self):
        if self.verencab:
            self.encabpagina()
        if self.verpie:
            self.piepagina()
        self.p.showPage()
        self.x = self.inix
        self.y = self.iniy
        self.p.setFont(self.nletra, self.alto)

    def finaliza(self):
        self.encabpagina()
        self.piepagina()
        self.p.save()

    def xval(self):
        return self.x

    def yval(self):
        return self.y

    def ysum(self, incremento):
        self.y = self.y - incremento
        if self.y < self.final:
            self.cpag()
