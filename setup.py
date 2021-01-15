from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='optimal-transport-morphometry',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc',
    author_email='kitware@kitware.com',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.0',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        (
            'antspyx @ '
            'https://github.com/girder/optimal-transport-morphometry/releases/download/1/'
            'antspyx-0.2.6-cp38-cp38-linux_x86_64.whl'
        ),
        'celery',
        'django',
        'django-admin-display',
        'django-allauth',
        'django-composed-configuration[dev,prod]>=0.10.0',
        'django-configurations[database,email]',
        'django-extensions',
        'django-filter',
        'django-oauth-toolkit==1.3.2',
        'django-s3-file-field[minio,boto3]',
        'djangorestframework',
        'drf-yasg',
        # Production-only
        'gunicorn',
        # Development-only
        'django-debug-toolbar',
    ],
    extras_require={'dev': ['ipython', 'tox']},
)
