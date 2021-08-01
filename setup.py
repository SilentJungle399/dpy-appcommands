import setuptools
import slash

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="slash",
    version=slash.__version__,
    author="SilentJungle399",
    description="A simple module to use for slash commands in discord.py.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    url="https://github.com/SilentJungle399/slash-commands",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
