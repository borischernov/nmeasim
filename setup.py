from setuptools import setup

setup(
    name='nmeasim',
    description='A Python GNSS/NMEA receiver simulation',
    author='Wei Li Jiang',
    author_email='wjiang87@gmail.com',
    license='MIT',
    url='https://gitlab.com/nmeasim/nmeasim',
    keywords=['gnss', 'glonass', 'gps', 'nmea', 'simulator'],
    install_requires=[
        "pyserial",
        "geographiclib",
        "importlib.metadata; python_version<'3.8'"
    ],
    packages=["nmeasim"],
    package_data={
        'nmeasim': ['icon.ico']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires='>=3.6'
)
