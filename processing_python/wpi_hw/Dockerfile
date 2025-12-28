FROM hendraet/synthesis-in-style:cuda-11.1

WORKDIR /workspace/final_application

# Copy your working WPI final_application (already patched)
COPY final_application /workspace/final_application

# Bake deps once (same set you proved works)
RUN python3 -m pip install -q pip==23.3.2 && \
    python3 -m pip install -q \
      protobuf==3.20.3 \
      pytorch-lightning==1.5.10 \
      torchmetrics==0.6.2 \
      typing-extensions==4.1.1 \
      PyYAML==5.4.1 \
      Pillow==8.3.2 \
      tqdm==4.62.2 \
      opencv-python==4.5.5.62 \
      wandb==0.12.9 && \
    python3 -m pip install -q \
      fastapi==0.110.0 \
      uvicorn==0.27.1 \
      httpx==0.27.0

EXPOSE 8002
CMD ["bash", "-lc", "uvicorn api.app:app --host 0.0.0.0 --port 8002"]
