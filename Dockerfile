FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Install Flask
RUN pip install flask gunicorn pymupdf tiktoken

# Expose default port
EXPOSE 7860

# create sample data on Hugging Face
# RUN python create_sample_data.py

# Run with Gunicorn
CMD ["gunicorn", "--access-logfile", "-", "--log-level", "debug",  "-w", "1", "-b", "0.0.0.0:7860", "app:app"]