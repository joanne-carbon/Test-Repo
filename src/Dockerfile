FROM python:3.6.6

WORKDIR /app

# Install dependencies and Clean up
RUN apt-get update \
  && apt-get install -y \
    unzip \
    wget \
  && apt-get clean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

# Install protoc binary
ENV PROTOC_VERISON 3.6.0
ENV PROTOC_DIR /protoc
RUN wget https://github.com/google/protobuf/releases/download/v$PROTOC_VERISON/protoc-$PROTOC_VERISON-linux-x86_64.zip \
  && unzip protoc-$PROTOC_VERISON-linux-x86_64.zip -d $PROTOC_DIR \
  && ln -s $PROTOC_DIR/bin/* /usr/local/bin/ \
  && rm protoc-$PROTOC_VERISON-linux-x86_64.zip

RUN pip install --upgrade \
    pip==18.0 \
    awscli==1.14.58

# Install requirements
ADD requirements.txt $WORKDIR
RUN pip install -r requirements.txt
ADD requirements_test.txt $WORKDIR
RUN pip install -r requirements_test.txt

# Copy the app to a new directory
ADD . $WORKDIR

# Compile protobuf files
RUN protoc --proto_path=. --python_out=. ./*/model/protobuf/*.proto
RUN protoc --proto_path=$(pip show carbon-core | grep 'Location' | awk {'print $2'}) --proto_path=. --python_out=. ./*/model/protobuf/*/*/*.proto

# Run it!
EXPOSE 5000
CMD ["./start-application.sh"]
