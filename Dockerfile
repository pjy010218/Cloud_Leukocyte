# Dockerfile for Symbiosis Control Plane Simulation
FROM python:3.9-slim

WORKDIR /app

# Copy source code
COPY schemas.py .
COPY policy_engine.py .
COPY policy_integrator.py .
COPY policy_compiler.py .
COPY symbiosis_simulation.py .

# Run the simulation
CMD ["python", "symbiosis_simulation.py"]
