# main font metrics (from woff2)
geist     = dict(upm=1000, ascent=1005, descent=-295, lineGap=0, xAvg=581)
geistMono = dict(upm=1000, ascent=1005, descent=-295, lineGap=0, xAvg=600)
# fallback reference metrics (capsize)
roboto   = dict(upm=2048, xAvg=978)   # Android default (mobile target)
courier  = dict(upm=2048, xAvg=1229)  # monospace fallback
def calc(main, fb):
    mainAvg = main['xAvg']/main['upm']
    fbAvg   = fb['xAvg']/fb['upm']
    sa = mainAvg/fbAvg
    asc = (main['ascent']/main['upm'])/sa
    dsc = (abs(main['descent'])/main['upm'])/sa
    lg  = (main['lineGap']/main['upm'])/sa
    return dict(sizeAdjust=round(sa*100,2), ascent=round(asc*100,2), descent=round(dsc*100,2), lineGap=round(lg*100,2))
print('Geist vs Roboto   :', calc(geist, roboto))
print('GeistMono vs Courier:', calc(geistMono, courier))
