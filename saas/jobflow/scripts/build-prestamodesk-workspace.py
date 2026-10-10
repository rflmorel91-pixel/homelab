"""Compile existing, scoped screens into one workspace without eval or frames."""
from pathlib import Path
import hashlib, json, re
root=Path(__file__).resolve().parents[1]
app=root/'app'
screens={'loans':'prestamodesk-app.html','cashier':'prestamodesk-caja.html','collections':'prestamodesk-cobros.html','supervision':'prestamodesk-cobros-supervision.html','administration':'prestamodesk-administracion.html'}

def scope_css(css):
    def split_selectors(text):
        parts=[];start=0;depth=0
        for i,ch in enumerate(text):
            if ch in '([':depth+=1
            elif ch in ')]':depth-=1
            elif ch==',' and depth==0:parts.append(text[start:i]);start=i+1
        parts.append(text[start:]);return parts
    def scan(text):
        out='';pos=0
        while pos<len(text):
            open_at=text.find('{',pos)
            if open_at<0:return out+text[pos:]
            head=text[pos:open_at].strip();level=1;i=open_at+1;quote=None
            while i<len(text) and level:
                ch=text[i]
                if quote:
                    if ch==quote and text[i-1]!='\\':quote=None
                elif ch in ('"',"'"):quote=ch
                elif ch=='{':level+=1
                elif ch=='}':level-=1
                i+=1
            body=text[open_at+1:i-1]
            if head.startswith('@'):
                content=scan(body) if head.startswith(('@media','@supports','@layer')) else body
            else:
                selectors=[]
                for selector in split_selectors(head):
                    selector=selector.strip()
                    if selector.startswith(('body', 'html', ':root')):
                        selector=re.sub(r'^(?:body|html|:root)', ':where(.pd-module)',selector)
                    else:selector=':where(.pd-module) '+selector
                    selectors.append(selector)
                head=','.join(selectors);content=body
            out+=head+'{'+content+'}\n';pos=i
        return out
    return scan(re.sub(r'/\*.*?\*/','',css,flags=re.S))

result=['/* Generated from existing screens; regenerate using scripts/build-prestamodesk-workspace.py. */\nwindow.PrestamoDeskScreens = {']
styles=[]
for key,filename in screens.items():
    page=(app/filename).read_text()
    body=re.search(r'<body[^>]*>(.*)</body>',page,re.S).group(1)
    scripts=re.findall(r'<script[^>]*src="(/assets/[^"]+)"[^>]*>\s*</script>',body,re.S)
    body=re.sub(r'<script.*?</script>','',body,flags=re.S)
    code='\n'.join((app/src.lstrip('/')).read_text() for src in scripts)
    result.append(json.dumps(key)+': {html:'+json.dumps(body,ensure_ascii=False)+', start: function(document, window, fetch, localStorage, location, setTimeout, clearTimeout) {\n'+code+'\nreturn {canLeave: () => !(typeof paymentSubmitting !== "undefined" && paymentSubmitting) && !(typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) && (!window.prestamodeskInvitationSharing || window.prestamodeskInvitationSharing.canLeave()) && (!window.prestamodeskLoanCreation || window.prestamodeskLoanCreation.canLeave()) && (!window.prestamodeskBorrowerContact || window.prestamodeskBorrowerContact.canLeave()), confirmLeave: () => window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? false : (typeof paymentSubmitting !== "undefined" && paymentSubmitting) || (typeof paymentNeedsReview !== "undefined" && paymentNeedsReview) ? false : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.confirmLeave() : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.confirmLeave() : false, leaveMessage: () => window.prestamodeskLoanCreation && !window.prestamodeskLoanCreation.canLeave() ? window.prestamodeskLoanCreation.leaveMessage : window.prestamodeskBorrowerContact && !window.prestamodeskBorrowerContact.canLeave() ? window.prestamodeskBorrowerContact.leaveMessage : window.prestamodeskInvitationSharing ? window.prestamodeskInvitationSharing.leaveMessage : "Revise el resultado del pago en Caja antes de cambiar de sección."};\n}},')
    for css in re.findall(r'href="(/assets/[^" ]+\.css)"',page):
        if css not in [item[0] for item in styles]:styles.append((css,scope_css((app/css.lstrip('/')).read_text()).replace(':where(.pd-module)', ':where(.pd-module[data-mode=administration])') if key=='administration' else scope_css((app/css.lstrip('/')).read_text())))
result.append('};\n')
generated={}
for prefix,contents in [('prestamodesk-workspace-screens','\n'.join(result)),('prestamodesk-workspace-screens-style','\n'.join(item[1] for item in styles))]:
    contents=contents.rstrip()+'\n'
    suffix='.js' if prefix.endswith('screens') else '.css'
    name=prefix+'-'+hashlib.sha256(contents.encode()).hexdigest()[:12]+suffix
    for previous in (app/'assets').glob(prefix+'-*'+suffix):previous.unlink()
    (app/'assets'/name).write_text(contents)
    generated[prefix]=(name,suffix)
    print(name)

page=app/"prestamodesk-workspace.html"
if page.exists():
    contents=page.read_text()
    for prefix,(name,suffix) in generated.items():
        contents=re.sub(prefix+r"-[a-f0-9]+"+re.escape(suffix),name,contents)
    page.write_text(contents)
