# sigpdf

## Introduction
Processes a PDF file, adds a custom watermark as well as an owner password and an optional user password, and allows you to enable or disable individual permissions, such as whether printing is allowed or not.

## Installlation
`pip install -r requirements.txt`

## Usage

```
usage: sigpdf.py [-h] [--text TEXT] [--angle ANGLE] [--opacity OPACITY] [--allow-print] [--allow-copy] [--allow-annotations] input output

Adds a diagonal watermark to each page of a PDF file and protects the output file with AES-256.

positional arguments:
  input                PDF input file
  output               PDF output file

options:
  -h, --help           show this help message and exit
  --text TEXT          Watermark text (default: "CONFIDENTIAL")
  --angle ANGLE        Rotation angle in degrees (default: 45)
  --opacity OPACITY    Opacity level between 0 and 1 (default: 0.18)
  --allow-print        Allows PDF printing
  --allow-copy         Allows copying or extraction of text and graphics.
  --allow-annotations  Allows adding and changing annotations
```

## Example

```
python sigpdf.py --text "Hello World" .\input_file.pdf .\output_file.pdf
```
