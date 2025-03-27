docker build . -t blobmoji && docker run --rm -it -v "$PWD/fonts:/blobmoji/fonts" blobmoji
