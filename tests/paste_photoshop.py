"""Use Photoshop's documented COM scripting API; close only our disposable document."""
import json
from pathlib import Path
import win32com.client
from PIL import ImageGrab
image=ImageGrab.grabclipboard()
assert image is not None
ps=win32com.client.Dispatch('Photoshop.Application')
script='''
var previous = app.documents.length ? app.activeDocument : null;
var test = null;
try {
 test = app.documents.add(%d, %d, 72, "LiLiFaceSnixp clipboard acceptance", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
 var layer = test.paste();
 var b = layer.bounds;
 var answer = Math.round(b[2].as('px')-b[0].as('px')) + ',' + Math.round(b[3].as('px')-b[1].as('px'));
} finally {
 if (test) test.close(SaveOptions.DONOTSAVECHANGES);
 if (previous) app.activeDocument = previous;
}
answer;
''' % image.size
actual=ps.DoJavaScript(script)
result={'passed':actual==f'{image.width},{image.height}','pasted_dimensions':actual,'expected':image.size}
Path('test-results/photoshop-paste.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
assert result['passed']
