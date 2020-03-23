from setuptools import setup, find_packages

setup(
    name='infestor',
    version='0.1.4',
    packages=find_packages(),
    url='http://github.com/emre/transmitter',
    license='MIT',
    author='emre yilmaz',
    author_email='mail@emreyilmaz.me',
    description='CLI app to claim and create discounted accounts'
                ' on the HIVE blockchain.',
    entry_points={
        'console_scripts': [
            'infestor = infestor.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=["lighthive", "pymongo", "flask", "gunicorn", "steemconnect"],
)
