from setuptools import setup, find_packages

setup(
    name='mkpipe-extractor-influxdb',
    version='1.0.0',
    license='Apache License 2.0',
    packages=find_packages(),
    install_requires=['mkpipe', 'influxdb-client'],
    include_package_data=True,
    entry_points={
        'mkpipe.extractors': [
            'influxdb = mkpipe_extractor_influxdb:InfluxDBExtractor',
        ],
    },
    description='InfluxDB extractor for mkpipe.',
    author='Metin Karakus',
    author_email='metin_karakus@yahoo.com',
    python_requires='>=3.9',
)
