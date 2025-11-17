from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="txt2phrases",
    version="1.0.3",
    author="Udita Agarwal",
    author_email="udita20agarwal@gmail.com",
    description="A comprehensive library for text processing, keyword extraction, and classification from PDF and HTML documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/semanticClimate/encyclopedia/tree/main/txt2phrases",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "transformers>=4.0.0",
        "pandas>=1.0.0",
        "tqdm>=4.50.0",
        "PyPDF2>=2.0.0",
        "scikit-learn>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "txt2phrases=txt2phrases.cli:main",
        ],
    },
    keywords="text-processing, keyword-extraction, pdf, html, nlp, tf-idf, classification",
)
