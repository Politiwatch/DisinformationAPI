FROM python:3
RUN apt update
WORKDIR /app
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
ADD ./src/ /app
ENV PORT 8080
CMD ["gunicorn", "app:app", "--config=config.py"]