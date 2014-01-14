# Copyright 2012, 2013 The GalSim developers:
# https://github.com/GalSim-developers
#
# This file is part of GalSim: The modular galaxy image simulation toolkit.
#
# GalSim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GalSim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GalSim.  If not, see <http://www.gnu.org/licenses/>
#
"""@file integ.py
A Python layer version of the C++ int1d function in galim::integ
"""

from . import _galsim

def int1d(func, min, max, rel_err=1.e-6, abs_err=1.e-12):
    """Integrate a 1-dimensional function from min to max.

    Example usage:

        >>> def func(x): return x**2
        >>> galsim.integ.int1d(func, 0, 1)
        0.33333333333333337
        >>> galsim.integ.int1d(func, 0, 2)
        2.666666666666667
        >>> galsim.integ.int1d(func, -1, 1)
        0.66666666666666674

    @param func     The function to be integrated.  y = func(x) should be valid.
    @param min      The lower end of the integration bounds (anything < -1.e10 is treated as
                    negative infinity).
    @param max      The upper end of the integration bounds (anything > 1.e10 is treated as positive
                    infinity).
    @param rel_err  The desired relative error (default `rel_err = 1.e-6`)
    @param abs_err  The desired absolute error (default `abs_err = 1.e-12`)
    """
    min = float(min)
    max = float(max)
    rel_err = float(rel_err)
    abs_err = float(abs_err)
    success, result = _galsim.PyInt1d(func,min,max,rel_err,abs_err)
    if success:
        return result
    else:
        raise RuntimeError(result)

def midpoint_int_image(f_image, a, b, N):
    h = (b*1.0 - a)/N
    w = [a + h * (i+0.5) for i in range(N)]
    images = map(f_image, w)
    return h*reduce(lambda x, y: x+y, images)

def trapezoidal_int_image(f_image, a, b, N):
    h = (b*1.0 - a)/N
    w = [a + h * i for i in range(N+1)]
    images = map(f_image, w)
    return 0.5*h*(images[0] + 2.0*reduce(lambda x, y: x+y, images[1:-1]) + images[-1])

def simpsons_int_image(f_image, a, b, N):
    if N%2 == 1:
        N += 1
    h = (b*1.0 - a)/N
    w = [a + h * i for i in range(N+1)]
    images = map(f_image, w)
    return h/3.0 * (images[0]
                    + 4.0*reduce(lambda x, y: x+y, images[1:-1:2])
                    + 2.0*reduce(lambda x, y: x+y, images[2:-2:2])
                    + images[-1])

#Node locations and weights for Gaussian-Kronrod quadrature
GK_nodes = [-0.9914553711208126392068547,
            -0.9491079123427585245261897,
            -0.8648644233597690727897128,
            -0.7415311855993944398638648,
            -0.5860872354676911302941448,
            -0.4058451513773971669066064,
            -0.2077849550078984676006894,
             0.0,
             0.2077849550078984676006894,
             0.4058451513773971669066064,
             0.5860872354676911302941448,
             0.7415311855993944398638648,
             0.8648644233597690727897128,
             0.9491079123427585245261897,
             0.9914553711208126392068547]
K_weights = [0.0229353220105292249637320,
             0.0630920926299785532907007,
             0.1047900103222501838398763,
             0.1406532597155259187451896,
             0.1690047266392679028265834,
             0.1903505780647854099132564,
             0.2044329400752988924141620,
             0.2094821410847278280129992,
             0.2044329400752988924141620,
             0.1903505780647854099132564,
             0.1690047266392679028265834,
             0.1406532597155259187451896,
             0.1047900103222501838398763,
             0.0630920926299785532907007,
             0.0229353220105292249637320]
G_weights = [0.0,
             0.1294849661688696932706114,
             0.0,
             0.2797053914892766670114678,
             0.0,
             0.3818300505051189449503698,
             0.0,
             0.4179591836734693877551020,
             0.0,
             0.3818300505051189449503698,
             0.0,
             0.2797053914892766670114678,
             0.0,
             0.1294849661688696932706114,
             0.0]

def gauss_kronrod_image_rule(f, a, b):
    z = [(b-a)/2.0 * n + (a+b)/2.0 for n in GK_nodes]
    fz = map(f, z)
    GImage = fz[0].copy()
    KImage = fz[0].copy()
    GImage.setZero()
    KImage.setZero()
    for i in xrange(15):
        GImage += fz[i] * G_weights[i]
        KImage += fz[i] * K_weights[i]
    GImage *= (b-a)/2.0
    KImage *= (b-a)/2.0
    errarray = (200 * abs(GImage.array-KImage.array))**1.5
    errImage = KImage.copy()
    errImage.setZero()
    errImage.array[:] = errarray
    return KImage, errImage

def globally_adaptive_GK_int_image(f, a, b, rel_err=1.e-3):
    SImage, errImage = gauss_kronrod_image_rule(f, a, b)
    err = errImage.array.sum()
    heap = [(a, b, SImage, errImage, err)]
    iter_=0
    while ((err / SImage.array.sum()) > rel_err) and iter_<100:
        errs = [heap[i][4] for i in range(len(heap))]
        max_ = max(errs)
        k = errs.index(max_)
        a = heap[k][0]
        b = heap[k][1]
        m = (a*1.0 + b)/2.0
        SImageLeft, errImageLeft = gauss_kronrod_image_rule(f, a, m)
        SImageRight, errImageRight = gauss_kronrod_image_rule(f, m, b)
        SImage = SImage - heap[k][2] + SImageLeft + SImageRight
        errImage = errImage - heap[k][3] + errImageLeft + errImageRight
        del heap[k]
        heap.append((a, m, SImageLeft, errImageLeft, errImageLeft.array.sum()))
        heap.append((m, b, SImageRight, errImageRight, errImageRight.array.sum()))
        err = errImage.array.sum()
        iter_ += 1
    return SImage
