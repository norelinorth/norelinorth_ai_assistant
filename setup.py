from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="ai_assistant",
    version="2.1.1",
    description="Embedded AI Assistant inside ERPNext DocTypes with Langfuse observability",
    author="Noreli North",
    author_email="honeyspotdaily@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)