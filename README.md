# BetterHealthProject
Creation of a software regarding a private health clinic named Better Health

Authors: Maria Azcona Garcia, Mohamed Largo Yagoubi & Marçal Piró Patau

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/mpp44/BetterHealthProject.git
cd BetterHealthProject
```

### 2. Build Docker Image

```bash
docker-compose build
```

### 3. Start Docker Container

```bash
docker-compose up
```
Server will be running on: http://127.0.0.1:8000/

### 4. Create a superuser (optional)

```bash
python manage.py createsuperuser
```
You can access Django’s admin panel at: http://127.0.0.1:8000/admin/

## Run project in remote

### You can also view the functionalities online following the next link (project deployed in render.com):

```
https://betterhealthproject-w1tc.onrender.com
```
