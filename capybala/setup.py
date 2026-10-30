from setuptools import setup, find_packages

setup(
    name="capybala",
    version="0.3.0",
    description="Context-Aware Pruning for Yielding & Backtrack-Aligned Loop Avoidance: The chill, self-healing runtime that cures autonomous AI agents from cognitive deadlocks.",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "llama-stack": ["llama-stack-client"],
        "langchain": ["langchain-core"],
    },
)
