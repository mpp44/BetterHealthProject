# BetterHealthProject
Creation of a software regarding a private health clinic named Better Health

Authors: Maria Azcona Garcia, Mohamed Largo Yagoubi & Marçal Piró Patau

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/mpp44/BetterHealthProject.git
cd BetterHealthProject
```

### 2. Set up the database example data
This project uses example services and schedules models sourced from the JSON files catalogo_servicios.json and horarios.json:

```bash
python manage.py import_services
python manage.py import_schedules
```

If you want to delete all data:
```bash
python manage.py delete_all
```

### 3. Build Docker Image

```bash
docker-compose build
```

### 4. Start Docker Container

```bash
docker-compose up
```
Server will be running on: http://127.0.0.1:8000/

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```
You can access Django’s admin panel at: http://127.0.0.1:8000/admin/
