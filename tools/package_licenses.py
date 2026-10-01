"""Copy installed dependency notices to the portable app folder."""
from pathlib import Path
import importlib.metadata
import shutil
import sys

root=Path('dist/LiLiFaceSnixp/licenses')
root.mkdir(parents=True,exist_ok=True)
for name in ('opencv-python-headless','pillow','pywin32','pystray','numpy','mss'):
    package=importlib.metadata.distribution(name)
    for item in package.files or []:
        if any(term in item.name.lower() for term in ('license','copying','copyright')):
            source=Path(package.locate_file(item))
            if source.is_file():
                target=root/name/item.name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if python_license.exists(): shutil.copy2(python_license,root/'Python-LICENSE.txt')
# LGPL library source provided alongside the runnable distribution.
package=importlib.metadata.distribution('pystray')
for item in package.files or []:
    if str(item).startswith('pystray/') and item.suffix=='.py':
        target=root/'pystray-source'/Path(*item.parts[1:])
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(package.locate_file(item),target)
print('Dependency licenses and pystray source packaged.')
