import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
import matplotlib.image as mpimg
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,AnnotationBbox)
import matplotlib.path as mpltPath
from matplotlib import rc
import numpy as np
from itertools import product

# font.family        : serif
# font.serif         : Times, Palatino, New Century Schoolbook, Bookman, Computer Modern Roman
# font.sans-serif    : Helvetica, Avant Garde, Computer Modern Sans serif
# font.cursive       : Zapf Chancery
# font.monospace     : Courier, Computer Modern Typewriter
# text.usetex        : true
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)

fck = 50
fyk = 500
rec = 0.05
concr = "C50/60"
steel = "A500"
Es = 200000

num_bars = 6
fcd = 1
radius = 0.5
diameter = 2.0 * radius
num_layers = 100
height_layer = diameter / num_layers
radius_reinf = radius - rec
    
areat = math.pi * radius * radius
fyd = round (fyk/1.15, 0)
eta = 1 if fck <= 50 else 1.0 + (fck - 50) / 200
lambd = 0.8 if fck <= 50 else 0.8 + (fck - 50) / 400
epsc2 = 2 if fck <= 50 else 2.0 + 0.085 * math.pow(fck - 50.0, 0.53)
epscu2 = 3.5 if fck <= 50 else 2.5 + 35 * math.pow((90.0 - fck)/100.0, 4)
n = 2 if fck <= 50 else 1.4 + 23.4 * math.pow((90.0 - fck)/100.0, 4)
x2 = 1.0 - epsc2/epscu2


concrete = {
    "C50/60": 50,
    "C55/67": 55,
    "C60/75": 60,
    "C70/85": 70,
    # "C80/95": 80,
}

reinfsteel = {
    "A400": 400,
    "A500": 500
}

steelname = {
    "A400": ["A400","S400"],
    "A500": ["A500","S500"]
}

locale = {
    "PT": 0,
    "EN": 1
}

zetas = [0.05, 0.1, 0.15]

nns = [100, 6, 10]

limits = {   #  w   miu  niu  niu
    "C50/60": [1.0, 0.4, 2.1, -1.1],
    "C55/67": [0.5, 0.25, 1.6, -0.6],
    "C60/75": [0.5, 0.25, 1.6, -0.6],
    "C70/85": [0.5, 0.2, 1.6, -0.6]
}

def sign(num):
    return 1 if num >= 0 else 0 if num == 0 else -1

def epsilon(x, x0):
    return epscu2 * (x0-x) / x0 if x0 < 1 else epsc2 * (1.0 - (x - x2)/(x0 - x2))

def conc_stress(epsc):
    return (1-((1-epsc/epsc2)**n))


def concreteforces(x0):
    ndiv = 1000
    ddiv = 2.0*radius / ndiv
    xxi = ddiv / 2.0
    
    xxx = np.linspace(ddiv / 2.0, x0, ndiv)
    yyy = np.subtract(radius, xxx)

    mtot = 0
    ftot = 0
    for i in range(ndiv):
        xx  = xxi + i *  ddiv
        if xx > x0: break
        eps = epsilon(xx, x0)
        dist = radius - xx

        area = ddiv * 2.0*math.sqrt(radius*radius-dist*dist)
        sig = fcd if eps >= epsc2 else (1-((1-eps/epsc2)**n))

        ftot += area * sig
        mtot += area * sig * dist

    return (ftot / areat, mtot / areat)


def steelforces(x0, ns=6):
    epsyd = fyd / Es * 1000

    dtheta = 2.0 * np.pi / ns
    theta0 = 0.5 * (1-ns%2) * dtheta
    r = radius - rec    
    polygon = radius-r*np.array([[np.cos(x)] for x in np.linspace(theta0,theta0+2*np.pi,ns+1)[:-1]])   
    eps = epsilon(polygon, x0)

    ftot = 0
    mtot = 0
    for i in range(ns):
        theta = theta0 + i * dtheta
        r = radius - rec
        rs = r * math.cos(theta)
        z = radius - rs
        eps = epsilon(z, x0)
        fs = sign(eps)*fyd if math.fabs(eps) >= epsyd else eps * Es / 1000
        ftot += fs
        mtot += fs * rs

    return (round(ftot / ns / fyd,6), round(mtot / ns / fyd,6))


def bend_circular():
    # calculate secrion coordinates
    xxi = height_layer / 2.0
    conc_dist = np.linspace(xxi, diameter-xxi, num_layers)
    conc_aux = np.subtract(radius, conc_dist)
    conc_area = height_layer * 2.0 * np.sqrt(np.subtract(radius*radius, conc_aux*conc_aux))
    conc_mom = conc_area * conc_dist
    
    # calculate reinforcement coordinates
    dtheta = 2.0 * np.pi / num_bars
    theta0 = 0.5 * (1-num_bars%2) * dtheta 
    reinf_dist = radius-radius_reinf*np.array([[np.cos(x)] for x in np.linspace(theta0,theta0+2*np.pi,num_bars+1)[:-1]])

    return conc_dist, conc_area, conc_mom, reinf_dist



if __name__ == "__main__":
    conc_dist, conc_area, conc_mom, reinf_dist = bend_circular()
    
    num_axis_pos = 100
    # neutralaxispositions
    x0 = np.concatenate((np.linspace(0.0001, 1, num_axis_pos), np.geomspace(1.0001, 100000, num_axis_pos)))
    # strains in eaxch concrete layer
    epsc = np.array([epsilon(conc_dist, xx) for xx in x0])
    epsc[epsc < 0] = 0.0
    # steress in eaxch concrete layer
    ### numpy compare and replace by number

    sig = np.where(epsc > epsc2, fcd, conc_stress(epsc))

    # inputs

    #ns = 6
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    props2 = dict(boxstyle='round', pad=0, ec="white", facecolor='white', alpha=0.8)
    props3 = dict(boxstyle='round', pad=0, ec="white", facecolor='white', alpha=0.8)

    listofinputs = [concrete, reinfsteel, zetas, nns]

    dw = 0.02
    numberw = int(limits[concr][0] / dw)
    aspectratio = (9.0/7.5)/((limits[concr][2]-limits[concr][3])/limits[concr][1])

    print('{0} {1} {2:.3f}'.format(fck, fyk,rec))

    # outputs
    # ciclo aos w (constroi linhas)
    wlist2 = []
    alist = []
    #ax.set_aspect(1.5)
    plt.figure(figsize = (7.5,9))
    ax = plt.gca()

    axlist = []
    aylist = []
    for i in range(numberw+1):
        w = i * dw
        mlist2 = []
        nlist2 = []
        # ciclo aox x (constroi uma linha)
        for j in range(num_axis_pos):
            x0 = 2.0 * j / num_axis_pos + 0.00001 if x0 <= 1 else 1 / (2.0 - x0)

            conc2 = concreteforces(x0)
            reinf = steelforces(x0, num_bars)
            mlist2.append(conc2[1]+reinf[1]*w)
            nlist2.append(conc2[0]+reinf[0]*w)

        wlist2.append([mlist2,nlist2])

        #print("w = " + str(w))
        s = 1
        # plt.plot(wlist[i][0], wlist[i][1], s, c="C"+str(i+1), alpha=0.5)
        # plt.plot(wlist[i][0], wlist[i][1], s, c='b', alpha=0.5)
        linew = 1.5 if i%5 == 0 else 1
        plt.plot(wlist2[i][0], wlist2[i][1], s, c='r', alpha=0.5, linewidth=linew)

        if i%5 == 0:
            ax.text(0.003, wlist2[i][1][0], '{:.1f}'.format(w),
                horizontalalignment='left', verticalalignment='bottom', bbox=props2)

    for j in range(16):
        #if j == 0: continue
        axlist = []
        aylist = []
        # ciclo aox x (constroi uma linha)
        for i in range(2):
            w = 0 if i == 0 else limits[concr][0] + dw
            x0 = 2.0 * j / 20 + 0.00001
            if x0 > 1.0: 
                x0 = 1 / (2.0 - x0)

            conc = concreteforces(x0)
            reinf = steelforces(x0, num_bars)
            axlist.append(conc[1]+reinf[1]*w)
            aylist.append(conc[0]+reinf[0]*w)

            if i == 1 and j > 0:
                lim = ax.get_xlim()
                dx = 7.5*(axlist[1]-axlist[0]) / (lim[1]-lim[0])
                dy = 9.0*(aylist[1]-aylist[0]) / (limits[concr][2]-limits[concr][3])
                angle = math.atan2(dy, dx) * 180.0 / math.pi
                aa = round(x0, 2)
                pos = 'top' if x0 < 0.6 else 'bottom'
                ax.text(axlist[1]+0.002, aylist[1]+0.002, r'$\alpha$={0:.2f}'.format(aa),
                    horizontalalignment='left', verticalalignment=pos, rotation = angle, bbox=props3)

        alist.append([axlist,aylist])

        #print("a = " + str(x0))
        s = 1
        # plt.plot(wlist[i][0], wlist[i][1], s, c="C"+str(i+1), alpha=0.5)
        plt.plot(alist[j][0], alist[j][1], s, c='b', alpha=0.5)

    axes = plt.gca()
    figure = plt.gcf()
    loc = axes.get_position()
    nstr = str(num_bars) if num_bars < 20 else r'$\infty$'
    strtext = ''.join(('{0}\n{1}\n'.format(concr, steel),r' $\zeta$ = {0:.2f}'.format(rec),'\n',r'$n_s$ = {}'.format(nstr)))
    # figure.text(0.8, 0.9, "C20/25", fontsize=12, bbox=props)
    # figure.text(0.5, 0.98, 'Flexão composta em secções retangulares', fontsize=14, horizontalalignment='center', verticalalignment='top')
    # figure.text(0.5, 0.95, 'de acordo com a EN 1992-1-1:2004', fontsize=10, horizontalalignment='center', verticalalignment='top')
    figure.text(0.9, 0.97, strtext, fontsize=10, horizontalalignment='center', verticalalignment='top', bbox=props)

    sleft = 0.3
    stop = 0.96
    strtext = r'$\nu=\frac{N_{Rd}}{A_cf_{cd}}$'
    figure.text(sleft, stop, strtext, fontsize=12, horizontalalignment='left', verticalalignment='center')
    strtext = r'$\mu=\frac{M_{Rd}}{A_cDf_{cd}}$'
    figure.text(sleft, stop - 0.05, strtext, fontsize=12, horizontalalignment='left', verticalalignment='center')
    strtext = r'$\omega=\frac{A_{s}f_{yd}}{A_cf_{cd}}$'
    figure.text(sleft+0.13, stop, strtext, fontsize=12, horizontalalignment='left', verticalalignment='center')
    strtext = r'$\zeta=\frac{c}{D}$'
    figure.text(sleft+0.13, stop - 0.05, strtext, fontsize=12, horizontalalignment='left', verticalalignment='center')
    strtext = r'$\alpha=\frac{x}{D}$'
    figure.text(sleft+0.26, stop - 0.05, strtext, fontsize=12, horizontalalignment='left', verticalalignment='center')

    plt.xlabel("Momento fletor, " + r'$\mu$')
    plt.ylabel("Força axial, " + r'$\nu$')
    #plt.xlim(0,limits[concr][1])
    plt.ylim(limits[concr][3],limits[concr][2])
    # plt.legend(legend, loc='upper right')
    plt.minorticks_on()
    plt.grid(b=True, color='black', which='minor', alpha=0.15)
    plt.grid(b=True, color='black', which='major')

    if num_bars == 6:
        im = plt.imread('figs/flexaocomposta-c6.png')
    elif num_bars == 10:
        im = plt.imread('figs/flexaocomposta-c10.png')
    else:
        im = plt.imread('figs/flexaocomposta-c.png')
    newax = figure.add_axes([0.05, 0.88, 0.25, 0.12], anchor='SW', zorder=-1)
    newax.imshow(im)
    newax.axis('off')

    # plt.xticks(np.arange(0,0.4,0.02))
    # plt.yticks(np.arange(-1,1,0.02))
    filename = 'circcol-pt/circ_col_' + str(fck) + '_' + str(fyk) + '_' + '{0:.0f}_{1:.0f}'.format(rec*100,num_bars) + '.svg'
    plt.savefig(fname=filename, dpi=600)
    #plt.show()

    print("End")
