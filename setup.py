# ==============================================================================
# setup.py - Setup alternativo
# ==============================================================================

SETUP_PY_CONTENT = '''
from setuptools import setup, find_packages
from pathlib import Path

# Leggi README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Leggi requirements
def read_requirements(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="modular-framework",
    version="1.0.0",
    author="Framework Team",
    author_email="team@framework.com",
    description="Framework Python modulare con database, networking e plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/modular-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'mypy>=1.7.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.3.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'framework=framework.cli.commands:cli',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
'''

print("✅ File di configurazione e __init__.py creati!")
print("\n📁 Struttura moduli completa:")
print("   framework/")
print("   ├── __init__.py              # ModularFramework principale")
print("   ├── core/")
print("   │   ├── __init__.py          # ✅ Exports core")
print("   │   ├── config.py            # ✅ Configurazione Pydantic")
print("   │   ├── logger.py            # Logging")
print("   │   ├── exceptions.py        # Eccezioni")
print("   │   └── base.py              # Classi base")
print("   ├── database/")
print("   │   ├── __init__.py          # ✅ Exports database")
print("   │   └── ...")
print("   ├── networking/")
print("   │   ├── __init__.py          # ✅ Exports networking")
print("   │   └── ...")
print("   ├── plugins/")
print("   │   ├── __init__.py          # ✅ Exports plugins")
print("   │   └── ...")
print("   ├── utils/")
print("   │   ├── __init__.py          # ✅ Exports utils")
print("   │   └── ...")
print("   └── cli/")
print("       ├── __init__.py          # ✅ Exports CLI")
print("       └── commands.py")

print("\n🔧 Per risolvere l'errore:")
print("   1. Crea i file mancanti nel tuo progetto")
print("   2. pip install -r requirements.txt")
print("   3. pytest tests/test_database.py")