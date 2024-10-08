try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name="swell_llm_import",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=1.8,<2",
        "pyyaml",
        "jsonschema",
        "jsonref",
        "argparse",
        "openai",
        "PyPDF2",
        "requests",
        "beautifulsoup4",
        "python-dotenv",
        "tiktoken",
    ],
    entry_points={
        "console_scripts": [
            "preprocess_source=preprocess_source:main",
            "build_schema=build_schema:main",
            "generate_product=generate_product:main",
            "import_batch=import_batch:main",
        ],
    },
)