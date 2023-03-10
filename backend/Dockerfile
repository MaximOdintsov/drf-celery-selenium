###########
# BUILDER #
###########

# pull official base image
FROM python:3.11-alpine as builder

# set work directory
WORKDIR /usr/src/user

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# copy project
COPY . .

# install dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/user/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.11-alpine

# create directory for the app user
RUN mkdir -p /home/user

# create the app user
RUN addgroup -S user && adduser -S user -G user

# create the appropriate directories
ENV HOME=/home/user
ENV APP_HOME=/home/user/web
RUN mkdir $APP_HOME
RUN mkdir -p $APP_HOME/backend/static
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
RUN pip install --upgrade pip
COPY --from=builder /usr/src/user/wheels /wheels
COPY --from=builder /usr/src/user/requirements.txt .
RUN pip install --no-cache /wheels/*

# copy entrypoint.sh
COPY ./backend/entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R user:user $HOME
RUN chmod 777 $APP_HOME/backend/parser_hh
# change to the user
USER user

# run entrypoint.sh
ENTRYPOINT ["/home/user/web/entrypoint.sh"]