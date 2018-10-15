from setuptools import setup

setup(
    name='infestor',
    version='0.0.3',
    packages=["infestor",],
    url='http://github.com/emre/transmitter',
    license='MIT',
    author='emre yilmaz',
    author_email='mail@emreyilmaz.me',
    description='CLI app to claim and create discounted accounts'
                ' on the STEEM blockchain.',
    entry_points={
        'console_scripts': [
            'infestor = infestor.main:main',
        ],
    },
    install_requires=["lightsteem"]
)
