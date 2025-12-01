FROM python:3.9-slim
RUN pip install flask
WORKDIR /app
COPY inventory_service.py /app/
CMD ["python", "inventory_service.py"]
