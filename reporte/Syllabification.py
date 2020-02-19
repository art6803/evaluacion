#!/usr/bin/python
# -*- coding: utf8 -*-

# Syllabification (NOT hyphenation) for Spanish
#
# Copyright (C) 2007 Andy Teijelo <andy@teijelo.net>
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

import re
import sys
import unicodedata

cre = re.compile(u'''(b|br|bl|c|ch|cr|cl|d|dr|f|fr|fl|gu|g|
                 gr|gl|gü|h|j|k|kr|kl|l|ll|m|mn|n|ñ|p|ph|
                 pr|pl|qu|q|rr|r|s|t|tr|tl|v|vr|vl|w|x|y|z)?        # preámbulo, posibles principios de sílaba.
                 (ih?u(?![aeoáéíóú])|                               # - i, h opcional y u, si detrás de la u no viene una vocal fuerte
                                                                    #   porque si viniera, la u se uniría a la vocal fuerte en la sílaba
                                                                    #   siguiente, como en chihuahua.
                                                                    #   Ejemplos:
                                                                    #       viu-da, pi-pihu-ca (eso no existe, pero si existiera, se dividiría así)
                  uh?i(?![aeoáéíóú])|                               # - u, h opcional e i, si detrás de la i no viene una vocal fuerte
                                                                    #   por las mismas razones del caso anterior.
                                                                    #   Ejemplos:
                                                                    #       fui, intuición
                                                                    #   con la h, sin embargo, no parece existir en español.
                  uy(?![aeiouáéíóú])|                               # - u con y, si detrás de la y no viene alguna vocal. Si viniera, la y
                                                                    #   tomaría su función de consonante para la sílaba siguiente.
                                                                    #   Ejemplos:
                                                                    #       muy
                                                                    #   no encuentro ninguno con consonante detrás de la y
                  [iuü]?[aeoáéíóú](h?[iuy](?![aeoiuáéíóú]))?|       # - Este es el caso fundamental, el de la mayoría de las sílabas.
                                                                    #   Este caso maneja las sílabas compuestas de solamente una vocal fuerte,
                                                                    #   los diptongos débil-fuerte y fuerte débil, y los triptongos.
                                                                    #   La estructura es: una vocal débil opcional, una fuerte y otra
                                                                    #   débil opcional. La presencia de las vocales débiles determina
                                                                    #   si hay diptongo, triptongo o nada. Una h puede aparecer entre la fuerte
                                                                    #   y la segunda vocal débil. No así entre la primera débil y la fuerte,
                                                                    #   pues ... VERIFICAR, POSIBLE ERROR!
                  [ui]|                                             #
                  y(?![aeiouáéíóú]))                                #                                           ''',
                 re.UNICODE | re.IGNORECASE | re.VERBOSE)

acentos = re.compile(u'[áéíóú]',re.UNICODE | re.IGNORECASE)
final_llanas = re.compile(u'[nsaeiou]',re.UNICODE | re.IGNORECASE)

def silabas(word):
    pos = []
    for m in cre.finditer(word):
        pos.append(m.start())
    pos.append(len(word))
    return [word[pos[x]:pos[x+1]] for x in xrange(len(pos)-1)]

def removeaccents(word):
    return unicodedata.normalize('NFD',word).encode('ascii','ignore').decode('ascii')

def silaba_tonica(l):
    '''Recibe la lista de sílabas y devuelve la posición de la
    tónica, -1 para la última, -2 para la penúltima, etc.'''

    acento_grafico = False
    silaba_acentuada = 0
    # en español ninguna palabra tiene más de un acento gráfico
    # así que simplemente voy a retornar el último que me encuentre,
    # en caso de que haya más de uno
    for i,silaba in enumerate(l):
        if acentos.search(silaba):
            acento_grafico = True
            silaba_acentuada = i - len(l) # -1 para la última, -2 para la penúltima, etc.
    if acento_grafico:
        return silaba_acentuada
    if final_llanas.search(l[-1][-1]): # si el último caracter de la última sílaba es n, s o vocal, es llana
        return max(-2,-len(l)) # los monosílabos no tiene penúltima sílaba
    else:
        return -1

def jeperipi(word):
    result = []

    uppercase = False
    titlecase = False
    if all(letter.isupper() for letter in word):
        uppercase = True
    if word[0].isupper() and all(letter.islower() for letter in word[1:]):
        titlecase = True

    for silaba in silabas(word):
        m = re.search(u'.*([aeoáéíóú])',silaba,re.UNICODE | re.IGNORECASE | re.VERBOSE)
        if not m:
            m = re.search(u'.*([iuy])',silaba,re.UNICODE | re.IGNORECASE | re.VERBOSE)
        if m:
            lastpart = silaba[m.end()-1:]
            add = u'p'
            if uppercase:
                add = u'P'
            if titlecase:
                lastpart = lastpart.lower()
            result.append(silaba[:m.end()-1]+
                          removeaccents(silaba[m.end()-1])+
                          add + lastpart)
    return result

if __name__=="__main__":
    wordre = re.compile("\w+",re.UNICODE | re.IGNORECASE)
    while True:
        l = u"dialogar con la prensa, Juan Pedro Shaerer, jefe de la delegación regional, se refirió a los retos del DIH en los conflictos actuales, en medio de hostilidades que se producen en zonas urbanas, con la utilización de armas explosivas en lugares de abundante población, y que provocan heridos, personas desplazadas y, en muchos casos, la muerte "
        if l=='':
            break
        pos = 0

        u = l.encode('latin-1')
        for m in wordre.finditer(u):
            sys.stdout.write(u[pos:m.start()].encode('utf8'))
            w = m.group(0)
            l = silabas(w)
            t = silaba_tonica(l)
            l[t] = l[t].upper()
            d = u"-".join(l)
            #d = u"".join(jeperipi(w))
            sys.stdout.write(d.encode('utf8'))
            pos = m.end()
        sys.stdout.write(u[pos:].encode('utf8'))
