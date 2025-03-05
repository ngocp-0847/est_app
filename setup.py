from setuptools import setup, find_packages

setup(
    name="est_egg",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "instructor>=0.3.0",
        "pydantic>=2.0.0",
        "streamlit>=1.23.0",
    ],
    entry_points={
        "console_scripts": [
            "est-analyst-cli=est_egg.cli:main",
            "est-analyst-web=est_egg.streamlit_app:run_streamlit",
        ],
    },
    author="",
    author_email="",
    description="Software Requirement Analysis Tool",
)
