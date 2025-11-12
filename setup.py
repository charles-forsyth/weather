from setuptools import setup, find_packages

setup(
    name="weather-suite",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "Pillow",
        "RPi.GPIO",
    ],
    include_package_data=True,
    package_data={
        'weather': ['icons/*.png'],
    },
    entry_points={
        'console_scripts': [
            'weather-gui = weather.gui:main',
            'weather-leds = weather.leds:main',
        ],
    },
)