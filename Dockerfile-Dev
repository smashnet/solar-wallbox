FROM python:3.8
LABEL Nicolas Inden <nicolas@inden.one>

WORKDIR /app

COPY requirements.txt ./

# Install python requirements
RUN pip install --upgrade pip && pip3 install --no-cache-dir -r requirements.txt

# Create required paths
ENV CONFIG_PATH /app/src/config
RUN mkdir -p $CONFIG_PATH

COPY entrypoint.sh ./

ENV PORT 8080
EXPOSE 8080

ENTRYPOINT [ "./entrypoint.sh" ]
