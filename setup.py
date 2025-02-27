from setuptools import setup, find_packages

setup(
    name="ezpass",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "cryptography",
        "pyperclip",
    ],
    entry_points={
        "console_scripts": [
            "ezpass=ezpass:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple and secure password manager",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kinzozi/ezpass",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 