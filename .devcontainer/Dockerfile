ARG USER=app

FROM python:3.14-trixie

ARG USER

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

RUN groupadd --system $USER && \
    useradd --system --create-home --gid $USER $USER

RUN pip install uv
