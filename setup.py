from setuptools import setup, find_packages

setup(
    name='lti1p3platform',
    version='0.0.7',
    description='LTI 1.3 Platform implementation',
    author='Jun Tu',
    author_email='jun@openlearning.com',
    url='https://github.com/OpenLearningNet/lti1p3platform',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
    install_requires=[
        "requests[security]",
        "pyjwt[crypto]",
        "jwcrypto"
    ],
)
