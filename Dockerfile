FROM python:alpine3.6
RUN apk update
RUN apk add --no-cache gcc python3-dev libc-dev libressl-dev
COPY . /app
WORKDIR /app
RUN pip install -e .
ENTRYPOINT ["infestor"]
