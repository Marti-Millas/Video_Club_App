# Video Club Back-office 🎮

Aquesta és la capa de persistència de l'aplicació de gestió de Video Club, desenvolupada per a l'assignatura d'**Accés a Dades (1r DAM)**.

## 🚀 Tecnologies utilitzades
* **Python 3.10+**
* **SQLAlchemy ORM** (Patró Repository i Unit of Work)
* **Alembic** (Migracions de base de dades)
* **PostgreSQL** (Desenvolupament) i **SQLite** (Test)

## 🛠️ Estructura del Projecte
L'aplicació segueix una arquitectura de domini:
- `src/domain/models.py`: Definició de les entitats.
- `src/domain/repositories.py`: Lògica d'accés a dades.
- `alembic/`: Historial de versions de la base de dades.
- `notebooks/`: Proves i execució de mètodes.

## 🔧 Configuració
1. Crea un entorn virtual: `python -m venv venv`
2. Instal·la les dependències: `pip install -r requirements.txt` (o via toml)
3. Configura el teu fitxer `.env` basant-te en l'entorn desitjat.