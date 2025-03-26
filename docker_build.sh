docker build . -t blobmoji && docker run --rm -it -v "$PWD/build:/blobmoji/build" blobmoji
