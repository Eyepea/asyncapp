import pathlib
import setuptools

LONG_DESCRIPTION = pathlib.Path('README.rst').read_text('utf-8')

def find_version():
    with open("asyncapp/__version__.py") as f:
        version = f.readlines()[-1].split('=')[-1].strip().strip("'").strip('"')
        if not version:
            raise RuntimeError('No version found')

    return version


setuptools.setup(
    name='asyncapp',
    long_description=LONG_DESCRIPTION,
    description='(a)sync Slack API library',
    keywords=[
        'bot',
        'slack',
        'api',
        'sans-io',
        'async'
    ],
    packages=setuptools.find_packages(),
    zip_safe=True,
    install_requires=['aiohttp'],
    # python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
    ],
    author='Ovv',
    author_email='contact@ovv.wtf',
    license='MIT',
    url='https://github.com/Eyepea/asyncapp',
    version=find_version(),
)
