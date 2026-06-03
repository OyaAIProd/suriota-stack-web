import urllib.request, io
from fontTools.ttLib import TTFont
UA={'User-Agent':'Mozilla/5.0'}
fonts={
 'Geist':'https://fonts.gstatic.com/s/geist/v5/gyByhwUxId8gMEwcGFWNOITd.woff2',
 'GeistMono':'https://fonts.gstatic.com/s/geistmono/v5/or3nQ6H-1_WfwkMZI_qYFrcdmhHkjko.woff2',
}
def metrics(url):
    req=urllib.request.Request(url,headers=UA)
    data=urllib.request.urlopen(req,timeout=30).read()
    f=TTFont(io.BytesIO(data))
    head=f['head']; hhea=f['hhea']; os2=f['OS/2']
    return dict(upm=head.unitsPerEm, ascent=hhea.ascent, descent=hhea.descent,
               lineGap=hhea.lineGap, xHeight=getattr(os2,'sxHeight',None),
               capHeight=getattr(os2,'sCapHeight',None), xAvg=os2.xAvgCharWidth)
for k,u in fonts.items():
    print(k, metrics(u))
