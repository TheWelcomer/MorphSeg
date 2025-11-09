from setuptools import find_packages,setup
#TODO: Expose spacy module, nonspacy module (you already do this!)
print(find_packages("."))
setup(
    name="testmorphseg",
    version="0.0.0",
    #package_dir={"":"."},
    packages=find_packages("."),#["testmorphseg","testmorphseg.non_spacy"], #praying you don't need 'model'
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    description="Erm... What the Segma?",
    long_description="Long description",
    author="Timmald",
    author_email="aprilscout.dog@gmail.com",
    license="MIT",
    install_requires=["spacy","torch","pandas","tqdm","numpy","rich","editdistance"],
    include_package_data=True,
    package_data={
        "testmorphseg.non_spacy.pretrained_models": ["*.pt"],
    },
)