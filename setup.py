from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="norelinorth_ai_assistant",
    version="2.2.1",
    description="Embedded AI Assistant inside ERPNext DocTypes with Langfuse observability",
    author="Noreli North",
    url="https://github.com/norelinorth/norelinorth_ai_assistant",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)