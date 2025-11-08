from setuptools import find_packages,setup
#TODO: Expose spacy module, nonspacy module (you already do this!)
setup(
    name="testmorphseg",
    version="0.0.0",
    package_dir={"":"."},
    packages=find_packages(where="."),
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    description="Erm... What the Segma?",
    long_description="Long description",
    author="Timmald",
    author_email="aprilscout.dog@gmail.com",
    license="MIT",
    requires=["spacy"],
)