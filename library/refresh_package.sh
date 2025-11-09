!#/bin/sh
#pip freeze | cut -d "@" -f1 | xargs pip uninstall -y
pip uninstall -y testmorphseg
pip install setuptools
python setup.py bdist_wheel sdist
pip install .
python ../run.py