"""Setup script for pysack.

pysack: Encrypt Python projects with Nuitka and pack with PyInstaller.
"""

from setuptools import setup, find_packages

setup(
    name="pysack",
    version="0.2.10",
    license="MIT",
    description=(
        "Encrypt Python projects with Nuitka and pack with PyInstaller "
        "— one-command source code protection for your Python applications."
    ),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="jiuzero",
    author_email="1703417187@qq.com",
    url="https://github.com/JiuZero/PySack",
    project_urls={
        "Homepage": "https://github.com/JiuZero/PySack",
        "Repository": "https://github.com/JiuZero/PySack",
    },
    packages=find_packages(include=["pysack", "pysack.*"]),
    python_requires=">=3.8,<4",
    install_requires=[
        "nuitka",
        "pyinstaller",
    ],
    entry_points={
        "console_scripts": [
            "pysack=pysack.cmdline:execute",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Security :: Cryptography",
    ],
)