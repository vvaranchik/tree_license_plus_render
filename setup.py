import setuptools

with open('README.md', 'r') as readme:
    long_desc = readme.read()

setuptools.setup(
    name='tree_license',
    version='0.1',
    scripts=['tree_license', 'render.sh'],
    author='Daniil Morshchinin',
    decription='',
    long_descripiton=long_desc,
    long_descripiton_content_type='text/markdown',
    url='https://github.com/vvaranchik/tree_license_plus_render',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operation System :: OS Independent'
    ]
)
