# pdfmerge
![automation](https://img.shields.io/docker/cloud/automated/joschuster/pdfmerge) ![build status](https://img.shields.io/docker/cloud/build/joschuster/pdfmerge)

A Docker container that watches for incoming files and merges (collates) them together using [qpdf](https://github.com/qpdf/qpdf).

Highly inspired by [OCRmyPDF](https://hub.docker.com/r/jbarlow83/ocrmypdf) and [rversts pdfmerge docker-container](https://hub.docker.com/r/rverst/pdfmerge)

OCRmyPDF is great for adding an OCR Layer to your scanned PDFs. It also provides a great Docker container. This and the included [watcher.py](https://ocrmypdf.readthedocs.io/en/latest/batch.html?highlight=watcher#watched-folders-with-watcher-py) makes it ideal for running on modern NAS (like Synology Diskstation or QNAP) with Docker support.

# Motivation
My ADF scanner does't support duplex scanning. Which means, I have to scan multipage documents in 2 steps, first the front (odd). Taking the pages and putting them back upside down to scan the back (even) pages in separat run. Resulting in 2 PDFs I had to merge manually page by page into one.

# Solution
I found [pdftk](https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/) and also [qpdf](https://github.com/qpdf/qpdf) for the task to bring both PDFs together in an alternating sequence. As the scanning of the back (even) pages is done from last to first page, it also inverts the order of that PDF pages.

So inspired by the clean worker.py python script of OCRmyPDF, pdfmerge is setup almost the same way.
I tried to keep as close as possible to their implementation so it should be easy for me and others to have some modifications later on.

Greate about that modular approach is, you can combine the output of the pdfmerge (Docker container) with the input of OCRmyPDF (watcher Docker container).

# Setup
I suggest you to use docker-compose with the following docker-compose.yml configuration:
```
version: '3.4'

services:
  pdfmerge:
    restart: always
    container_name: pdfmerge
    image: joschuster/pdfmerge
    volumes:
      - "/volume1/public/scan/duplexinbox:/input"
      - "/volume1/public/scan/inbox:/output"
      - "/etc/localtime:/etc/localtime:ro"
    environment: 
      - ODD_PAGES_PATTERN=front
      - EVEN_PAGES_PATTERN=back
    user: "<user-id>:<group-id>"
    entrypoint: python3
    command: watcher.py
```

Modify ```user-id``` and ```group-id``` to your need. Also set the ```volumes``` to your corresponding input and output folders. Nice-to-have: ```/etc/localtime:/etc/localtime:ro``` will ensure the correct time set in the container setting the correct date for the output file name.

## Environment variables
```
ODD_PAGES_PATTERN (default 'odd'): identify the odd pages like odd_123.pdf
EVEN_PAGES_PATTERN (default 'even'): identify the even pages like even_456.pdf
MERGED_NAME_PREFIX (default 'merged'): get an output with that prefix and the date time appended like merged_20201220-200629.pdf
```
