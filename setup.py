from setuptools import setup

setup(
    name='flask-resty-shared-session',
    version='0.1.2',
    url='https://github.com/scivey/flask-resty-shared-session',
    license='BSD',
    author='Scott Ivey',
    author_email='scott.ivey@gmail.com',
    description='An adapted flask-session module and corresponding OpenResty package, so flask and Nginx can share session information.',
    packages=['flask_resty_shared_session'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.8',
        'redis>=2.10.5'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)