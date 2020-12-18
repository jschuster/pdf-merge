# Copyright (C) 2020 Joachim Schuster: https://github.com/jschuster
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import shutil
import os
import tempfile
import time
import logging
import pikepdf

from re import search
from pathlib import Path
from subprocess import call
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

ODD_PAGES_PATTERN = os.getenv('ODD_PAGES_PATTERN', 'odd')
EVEN_PAGES_PATTERN = os.getenv('EVEN_PAGES_PATTERN', 'even')
MERGED_NAME_PREFIX = os.getenv('MERGED_NAME_PREFIX', 'merged')

INPUT_DIRECTORY = os.getenv('INPUT_DIRECTORY', '/input')
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY', '/output')
POLL_NEW_FILE_SECONDS = int(os.getenv('POLL_NEW_FILE_SECONDS', '1'))
PDF_PATTERNS = ['*.pdf', '*.PDF']

LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

log = logging.getLogger('pdf-merge-watcher')

def prepare_pages(file_path):
    file_path = Path(file_path)
    if not wait_for_file_ready(file_path):
        log.info(f"Gave up waiting for {file_path} to become ready")
        return
    if search(ODD_PAGES_PATTERN, file_path.name):
        shutil.move(file_path, os.path.join(tempfile.gettempdir(), "odd.pdf"))
    elif search(EVEN_PAGES_PATTERN, file_path.name):
        shutil.move(file_path, os.path.join(tempfile.gettempdir(), "even.pdf"))
    else:
        log.info('PDF does not match even nor odd pages pattern')


def execute_pdf_merge():
    odd_file = Path(os.path.join(tempfile.gettempdir(), "odd.pdf"))
    even_file = Path(os.path.join(tempfile.gettempdir(), "even.pdf"))
    if odd_file.exists() & even_file.exists():
        log.info('Begin PDF merging')
        timestr = time.strftime("%Y%m%d-%H%M%S")
        merged_file = Path(os.path.join(OUTPUT_DIRECTORY, MERGED_NAME_PREFIX + "_" + timestr + ".pdf"))
        call(["qpdf", "--collate", odd_file, "--pages", odd_file, even_file, "z-1", "--", merged_file])
        log.info('Successful merged, removing source files')
        odd_file.unlink()
        even_file.unlink()
    elif odd_file.exists():
        log.info('Waiting for even pages')
    elif even_file.exists():
        log.info('Waiting for odd pages')
    else:
        log.info('No files to merge found')


def wait_for_file_ready(file_path):
    # This loop waits to make sure that the file is completely loaded on
    # disk before attempting to read. Docker sometimes will publish the
    # watchdog event before the file is actually fully on disk, causing
    # pikepdf to fail.

    retries = 5
    while retries:
        try:
            pdf = pikepdf.open(file_path)
        except (FileNotFoundError, pikepdf.PdfError) as e:
            log.info(f"File {file_path} is not ready yet")
            log.debug("Exception was", exc_info=e)
            time.sleep(POLL_NEW_FILE_SECONDS)
            retries -= 1
        else:
            pdf.close()
            return True

    return False


class EventHandler(PatternMatchingEventHandler):
    def on_any_event(self, event):
        if event.event_type in ['created']:
            prepare_pages(event.src_path)
            execute_pdf_merge()
            

if __name__ == "__main__":
    logging.basicConfig(level=LOGLEVEL)
    
    log.info(
        f"Starting PDF watcher with config:\n"
        f"Input Directory: {INPUT_DIRECTORY}\n"
        f"Output Directory: {OUTPUT_DIRECTORY}\n"
        f"Odd pages pdf name pattern: {ODD_PAGES_PATTERN}\n"
        f"Even pages pdf name pattern: {EVEN_PAGES_PATTERN}\n"
        f"Merged pages pdf name prefix: {MERGED_NAME_PREFIX}\n"
        f"Wait time (s) for polling on new files: {POLL_NEW_FILE_SECONDS}"
    )

    event_handler = EventHandler(patterns=PDF_PATTERNS)
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIRECTORY, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
