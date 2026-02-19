FROM python:3.10-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorios de logs
RUN mkdir -p logs

# Exponer puerto
EXPOSE 8000

# Comando para iniciar
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
