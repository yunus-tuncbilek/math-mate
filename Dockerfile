FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Install Flask
RUN pip install flask gunicorn

ENV FLASK_APP=app.py

# Expose default port
EXPOSE 7860

# Apply DB migrations, seed from sample_data (idempotent), then serve.
# Runs at startup (not build) so the SQLite file lives in the writable layer.
CMD ["sh", "-c", "flask db upgrade && python seed.py && gunicorn --access-logfile - --log-level debug -w 1 -b 0.0.0.0:7860 app:app"]