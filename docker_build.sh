docker build . -t blobmoji && docker run --rm -it -v "$PWD/build:/blobmoji/build" -v "$PWD/png:/blobmoji/png" -v "$PWD/fonts:/blobmoji/fonts" blobmoji
