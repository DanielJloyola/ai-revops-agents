"""Patch numbers into an existing deck slide (unpacked .pptx) and build a highlighted review copy.

Usage (from the unpacked deck dir):
  python slide_patch.py spec.json ppt/slides/slideN.xml            # clean slide
  python slide_patch.py spec.json ppt/slides/slideM.xml --review   # review copy (duplicate first with pptx add_slide.py)

spec.json:
{
  "rows":   {"Table 6|3": ["Oct 2026", "$5,000", ...]},          # table name | row index -> full row of cell text
  "yellow": ["Table 6|3|5", ...],                                  # cells that changed vs the user's current slide
  "orange": ["Table 6|2|6", ...],                                  # cells that need the user's decision
  "text":   {"Rectangle 9|1": ["44 of 152 ", "opps", " created ..."]},  # shape name | paragraph -> run texts (same run count)
  "orange_text": ["Box 17|1"],                                     # text paragraphs to mark orange (decision) on the review copy, unchanged
  "highlight_text": true,                                          # yellow text highlight on every patched paragraph (review copy)
  "review_title": "REVIEW COPY: YELLOW = UPDATE · ORANGE = YOUR CALL",
  "title_shape_prefix": "Slide Title",                              # shape holding the slide title in this deck
  "delta_rows": ["Table 6|4"]                                      # recolor run fonts by sign: + green 00703C, − red C00000, 0/n/a gray 808080
}
Table and shape names come from mapping the slide first (iterate p:graphicFrame / p:sp, print cNvPr name and texts).
"""
import json, sys
from lxml import etree
A='http://schemas.openxmlformats.org/drawingml/2006/main'; P='http://schemas.openxmlformats.org/presentationml/2006/main'
ns={'a':A,'p':P}; q=lambda t:'{%s}%s'%(A,t)
RPR_AFTER=('effectLst','effectDag','highlight','uLnTx','uLn','uFillTx','uFill','latin','ea','cs','sym','hlinkClick','hlinkMouseOver','rtl','extLst')

def set_cell(tc,val):
    paras=tc.findall('.//a:p',ns); p=paras[0]
    for extra in paras[1:]: extra.getparent().remove(extra)
    runs=p.findall('a:r',ns)
    for r in runs[1:]: p.remove(r)
    runs[0].find('a:t',ns).text=val

def fill_cell(tc,color):
    tcPr=tc.find('a:tcPr',ns)
    if tcPr is None: tcPr=etree.SubElement(tc,q('tcPr'))
    for f in ('noFill','solidFill','gradFill','blipFill','pattFill','grpFill'):
        for e in tcPr.findall('a:'+f,ns): tcPr.remove(e)
    sf=etree.Element(q('solidFill')); etree.SubElement(sf,q('srgbClr')).set('val',color)
    anchor=next((tcPr.find('a:'+t,ns) for t in ('cell3D','headers','extLst') if tcPr.find('a:'+t,ns) is not None),None)
    anchor.addprevious(sf) if anchor is not None else tcPr.append(sf)

def run_color(r,color):
    rPr=r.find('a:rPr',ns)
    if rPr is None: rPr=etree.Element(q('rPr')); r.insert(0,rPr)
    for e in rPr.findall('a:solidFill',ns)+rPr.findall('a:noFill',ns): rPr.remove(e)
    sf=etree.Element(q('solidFill')); etree.SubElement(sf,q('srgbClr')).set('val',color)
    anchor=next((ch for ch in rPr if etree.QName(ch).localname in RPR_AFTER),None)
    anchor.addprevious(sf) if anchor is not None else rPr.append(sf)

def highlight_run(r,color='FFFF00'):
    rPr=r.find('a:rPr',ns)
    if rPr is None: rPr=etree.Element(q('rPr')); r.insert(0,rPr)
    h=etree.Element(q('highlight')); etree.SubElement(h,q('srgbClr')).set('val',color)
    anchor=next((ch for ch in rPr if etree.QName(ch).localname in RPR_AFTER[3:]),None)
    anchor.addprevious(h) if anchor is not None else rPr.append(h)

def main(spec_path,slide,review):
    S=json.load(open(spec_path)); t=etree.parse(slide)
    rows={tuple(k.split('|')[:1])+(int(k.split('|')[1]),):v for k,v in S.get('rows',{}).items()}
    cells=lambda key:{(k.split('|')[0],int(k.split('|')[1]),int(k.split('|')[2])) for k in S.get(key,[])}
    Y,O=cells('yellow'),cells('orange'); D={(k.split('|')[0],int(k.split('|')[1])) for k in S.get('delta_rows',[])}
    for gf in t.iterfind('.//p:graphicFrame',ns):
        name=gf.find('.//p:cNvPr',ns).get('name')
        for i,tr in enumerate(gf.iterfind('.//a:tr',ns)):
            tcs=tr.findall('a:tc',ns)
            if (name,i) in rows:
                for tc,v in zip(tcs,rows[(name,i)]): set_cell(tc,v)
            if (name,i) in D:
                for tc in tcs:
                    r=tc.find('.//a:r',ns); c=r.find('a:rPr/a:solidFill/a:srgbClr',ns) if r is not None else None
                    if c is None or c.get('val') in ('FFFFFF',): continue
                    tx=r.find('a:t',ns).text or ''
                    c.set('val','00703C' if tx.startswith('+') else 'C00000' if tx.startswith(('−','-')) else '808080')
            if review:
                for j,tc in enumerate(tcs):
                    color='FFFF00' if (name,i,j) in Y else 'FFC000' if (name,i,j) in O else None
                    if color:
                        fill_cell(tc,color)
                        for r in tc.iterfind('.//a:r',ns): run_color(r,'000000')
    for sp in t.iterfind('.//p:sp',ns):
        name=sp.find('.//p:cNvPr',ns).get('name')
        if review and S.get('review_title') and name.startswith(S.get('title_shape_prefix','~')):
            sp.find('.//a:t',ns).text=S['review_title']
        if review:
            for key in S.get('orange_text',[]):
                sname,pi=key.split('|')
                if sname==name:
                    for r in sp.findall('.//p:txBody/a:p',ns)[int(pi)].findall('a:r',ns): highlight_run(r,'FFC000'); run_color(r,'000000')
        for key,texts in S.get('text',{}).items():
            sname,pi=key.split('|'); pi=int(pi)
            if sname!=name: continue
            runs=sp.findall('.//p:txBody/a:p',ns)[pi].findall('a:r',ns)
            assert len(runs)==len(texts),f'{key}: slide has {len(runs)} runs, spec has {len(texts)}'
            for r,tx in zip(runs,texts):
                r.find('a:t',ns).text=tx
                if review and S.get('highlight_text',True): highlight_run(r)
    t.write(slide,xml_declaration=True,encoding='UTF-8',standalone=True); print('patched',slide,'review' if review else 'clean')

if __name__=='__main__': main(sys.argv[1],sys.argv[2],'--review' in sys.argv)
