FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  

ENV appHome=/app/

RUN mkdir -p ${appHome}

WORKDIR ${appHome}

COPY requirements.txt ${appHome}

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt  


# Copy whole project in the docker home directory
COPY . ${appHome}

EXPOSE 8000

ENTRYPOINT [ "/app/build.sh" ]