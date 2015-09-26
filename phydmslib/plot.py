"""Module for plotting."""


import os
import math
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt


def PlotSignificantOmega(plotfile, models, ngt, nlt, nsites, fdr, usetex=True):
    """Makes a PDF slopegraph of the number of sites with significant omega.

    *plotfile* : name of created PDF.

    *models* : list of model names as strings

    *ngt* : list of same length as *models* giving number of sites with
    *omega* > 1.

    *nlt* : list of same length as *models* giving number of sites with
    *omega* < 1.

    *nsites* : total number of sites (used for y-axis label).

    *fdr* : false discovery rate (used for y-axis label).

    *usetex* : use LaTex formatting of strings?
    """
    assert os.path.splitext(plotfile)[1].lower() == '.pdf', "plotfile %s does not end with extension '.pdf'"
    assert len(models) == len(ngt) == len(nlt)
    plt.rc('font', size=25)
    plt.rc('text', usetex=usetex)
    omegacategories = {'< 1':'bo-', '> 1':'rs-'}
    handles = []
    labels = []
    ymax = 1
    for (cat, style) in omegacategories.items():
        xs = [x for x in range(len(models))]
        ys = {'< 1':nlt, '> 1':ngt}[cat]
        ymax = max(ymax, max(ys))
        handle = plt.plot(xs, ys, style, markersize=22, linewidth=3)
        handles.append(handle[0])
        if usetex:
            labels.append('$\omega_r %s$' % cat)
        else:
            labels.append('omega %s' % cat)
    plt.xlim(-0.25, len(models) - 0.75)
    plt.ylim(0, int(1.02 * ymax + 1))
    plt.xticks(xs, models, fontsize=32)
    plt.locator_params(axis='y', bins=4)
    plt.ylabel('sites out of %d (FDR %.2f)' % (nsites, fdr), fontsize=30)
    plt.legend(handles, labels, loc='upper right', numpoints=1, fontsize=34, borderaxespad=0)
    plt.savefig(plotfile, bbox_inches='tight')
    plt.clf()
    plt.close()



def SelectionViolinPlot(plotfile, ylabel, models, yvalues, symmetrizey, hlines=None, points=None, usetex=True):
    """Creates violin plot showing distribution of selection and significant sites.

    Calling arguments:

    *plotfile* : name of PDF plot to create.

    *ylabel* : ylabel for the plot.

    *models* : list of models for which we create violin plots.

    *yvalues* : list of the same length as *models*, each entry is a list
    of the Y-values (such as P-values).

    *symmetrizey* : make y-axis symmetric around zero?

    *hlines* : if not *None*, list of the same length as *models* with each entry
    a list giving y-value for where we draw horizontal lines for that *model*.

    *points* : if not *None*, list of the same length as *models* with each entry
    a list giving the y-value for points to be placed for that *model*.

    *usetex* : use LaTex formatting of strings?
    """
    assert os.path.splitext(plotfile)[1].lower() == '.pdf', "plotfile %s does not end with extension '.pdf'"
    assert len(models) == len(yvalues) >= 1
    plt.rc('font', size=12)
    plt.rc('text', usetex=usetex)
    (height, widthper) = (3, 1.75)
    plt.figure(figsize=(widthper * (0.5 + len(models)), height))
    plt.ylabel(ylabel, fontsize=16)
    xs = [x for x in range(len(models))]
    violinwidth = 0.75
    plt.violinplot(yvalues, xs, widths=violinwidth, showextrema=False)
    plt.xlim(-1.2 * violinwidth / 2.0, len(models) - 1 + 1.2 * violinwidth / 2.0)
    if hlines:
        assert len(hlines) == len(models)
        line_ys = []
        line_xmins = []
        line_xmaxs = []
        for i in range(len(models)):
            line_ys += hlines[i]
            line_xmins += [i - violinwidth / 2.0] * len(hlines[i])
            line_xmaxs += [i + violinwidth / 2.0] * len(hlines[i])
        plt.hlines(line_ys, line_xmins, line_xmaxs, colors='b')
    if symmetrizey:
        (ymin, ymax) = plt.ylim()
        ymax = 1.05 * max(abs(ymin), abs(ymax))
        ymin = -ymax
    else:
        (ymin, ymax) = plt.ylim()
    if points:
        assert len(points) == len(models)
        point_xs = []
        point_ys = []
        for i in range(len(models)):
            (model_xs, model_ys) = SmartJitter(points[i], yspace=(ymax - ymin) / 25., xspace=0.05, xcenter=i)
            point_xs += model_xs
            point_ys += model_ys
        plt.scatter(point_xs, point_ys, s=23, c='r', marker='o', alpha=0.45)
    plt.ylim(ymin, ymax)
    plt.xticks(xs, models, fontsize=16)
    plt.savefig(plotfile, bbox_inches='tight')
    plt.clf()
    plt.close()


def SmartJitter(ys, yspace, xspace, xcenter):
    """Smartly horizontally spaces points with assigned y-values to decrease overlap.

    Divides y-axis into bins, in each bin spaces points horizontally with the largest
    y-value point in the center and lower y-value points spreading out horizontally.

    *ys* is a list of y-coordinates of the points.

    *yspace* is the spacing between y-axis bins.

    *xspace* is the spacing between points in the same bin on the x-axis.

    *xcenter* is the center for the y-axis.

    The return value is *(smart_xs, smart_ys)*, which is a list with the
    x and y values of the spaced points.
    """
    assert yspace > 0 and xspace > 0
    (ymin, ymax) = (min(ys), max(ys))
    (ymin, ymax) = (ymin - yspace / 10. - 1e-5, ymax + yspace / 10. + 1e-5)
    assigned = [False] * len(ys)
    smart_xs = []
    smart_ys = []
    binymin = ymin
    while not all(assigned):
        assert binymin <= ymax
        binymax = binymin + yspace
        yindices = [iy for (iy, y) in enumerate(ys) if binymin <= y < binymax]
        binymin += yspace
        assert all([not assigned[iy] for iy in yindices]), "Assigned point to duplicate bin"
        binys = []
        for iy in yindices:
            assigned[iy] = True
            binys.append(ys[iy])
        if not binys:
            continue
        # make centeredbinys so that largest value is in middle
        binys.sort()
        binys.reverse()
        centeredbinys = [binys[0]]
        before = True
        for y in binys[1 : ]:
            if before:
                centeredbinys.insert(0, y)
            else:
                centeredbinys.append(y)
            before = not before
        assert len(centeredbinys) == len(binys)
        smart_ys += centeredbinys
        xmin = xcenter - xspace * (len(binys) - 1) / 2.0
        smart_xs += [xmin + xspace * i for i in range(len(binys))]
    assert all(assigned), "Failed to assign all points to bins"
    assert len(smart_xs) == len(smart_ys) == len(ys) == len(assigned)
    return (smart_xs, smart_ys)



if __name__ == '__main__':
    import doctest
    doctest.testmod()