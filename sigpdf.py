#!/usr/local/bin/python
#
# sigpdf
# Author: Joerg Schultze-Lutter, 2026
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import argparse
import getpass
import io
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.constants import UserAccessPermissions
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.pdfbase.pdfmetrics import stringWidth


def wrap_text_to_width(text, font_name, font_size, max_width):
    """
    Wraps text so that each line is no wider than max_width.
    Very long words will be split character by character if necessary.

    Parameters
    ==========
    text
        Watermark text to wrap
    font_name
        Font name
    font_size
        Font size
    max_width
        maximum width of text
    Returns
    =======
    lines
        List item, containing the lines for the watermark
    """

    words = text.split()

    if not words:
        return [""]

    lines = []
    current_line = ""

    for word in words:
        test_line = word if not current_line else f"{current_line} {word}"

        if stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
            continue

        if current_line:
            lines.append(current_line)
            current_line = ""

        # single word fits on one line
        if stringWidth(word, font_name, font_size) <= max_width:
            current_line = word
            continue

        # Break a very long word character by character
        partial = ""

        for char in word:
            test_word = partial + char

            if stringWidth(test_word, font_name, font_size) <= max_width:
                partial = test_word
            else:
                if partial:
                    lines.append(partial)

                partial = char

        current_line = partial

    if current_line:
        lines.append(current_line)

    return lines


def calculate_watermark_layout(
    text,
    font_name,
    initial_font_size,
    min_font_size,
    max_width,
    max_height,
):
    """
    Wraps text so that each line is no wider than max_width.
    Very long words will be split character by character if necessary.

    Parameters
    ==========
    text
        Watermark text to wrap
    font_name
        Font name
    initial_font_size
        Font size
    min_font_size
        min font size
    max_width
        maximum width of text
    max_height
        maximum height of text
    Returns
    =======

    font_size
        Font Size
    lines
        List item, containing the lines for the watermark
    line_spacing
        Line Spacing
    """

    font_size = initial_font_size

    while font_size >= min_font_size:

        lines = wrap_text_to_width(
            text=text,
            font_name=font_name,
            font_size=font_size,
            max_width=max_width,
        )

        line_spacing = font_size * 1.15
        block_height = len(lines) * line_spacing

        if block_height <= max_height:
            return font_size, lines, line_spacing

        # Decrease font size
        font_size -= 1

    # Minimum size reached
    font_size = min_font_size

    lines = wrap_text_to_width(
        text=text,
        font_name=font_name,
        font_size=font_size,
        max_width=max_width,
    )

    line_spacing = font_size * 1.15

    return font_size, lines, line_spacing


def create_watermark_page(
    width,
    height,
    text,
    angle=45,
    opacity=0.08,
):
    """
    Creates a transparent watermark page.

    Long texts are automatically wrapped, reduced in font size if
    necessary, and centered as a whole block of text

    Parameters
    ==========
    width
    height
    text
    angle
    opacity

    Returns
    ==========
    rendered page

    """

    packet = io.BytesIO()

    c = canvas.Canvas(
        packet,
        pagesize=(width, height),
        pdfVersion=(1, 4),
    )

    font_name = "Helvetica-Bold"

    # -------------------------------------------------------
    # Size calculation
    # -------------------------------------------------------

    # Default size for short watermarks
    initial_font_size = min(width, height) / 10

    # Not smaller than approximately 3% of the short side dimension
    min_font_size = min(width, height) * 0.03

    # Maximum line width
    max_text_width = min(width, height) * 0.80

    # Maximum height of the multi-line text block
    max_text_height = min(width, height) * 0.40

    font_size, lines, line_spacing = calculate_watermark_layout(
        text=text,
        font_name=font_name,
        initial_font_size=initial_font_size,
        min_font_size=min_font_size,
        max_width=max_text_width,
        max_height=max_text_height,
    )

    # -------------------------------------------------------
    # Center text
    # -------------------------------------------------------

    block_height = len(lines) * line_spacing

    x = width / 2
    y = height / 2

    c.saveState()

    watermark_color = Color(
        0.45,
        0.45,
        0.45,
        alpha=opacity,
    )

    c.setFillColor(watermark_color)
    c.setFillAlpha(opacity)
    c.setFont(font_name, font_size)

    # Page center
    c.translate(x, y)

    # Rotate whole text block
    c.rotate(angle)

    # Vertical starting point:
    # The entire multi-line block is centered around (0, 0).
    start_y = (block_height - line_spacing) / 2 - font_size * 0.30

    for index, line in enumerate(lines):
        line_y = start_y - index * line_spacing

        c.drawCentredString(
            0,
            line_y,
            line,
        )

    c.restoreState()

    c.showPage()
    c.save()

    packet.seek(0)

    return PdfReader(packet).pages[0]


def ask_optional_user_password():
    """
    Optionally prompts for a password to open the PDF.

    Blank entry / user presses return key:
        PDF can be opened without a password.


    Parameters
    ==========

    Returns
    ==========
    password

    """
    while True:
        password = getpass.getpass(
            "Password to open the PDF file (Return = no password): "
        )

        # Allow empty input
        if password == "":
            return ""

        confirmation = getpass.getpass("Repeat password: ")

        if password == confirmation:
            return password

        print("Passwords don't match. Please try again")


def ask_owner_password():
    """
    Prompts for the owner password.


    Parameters
    ==========

    Returns
    ==========
    password

    """
    while True:
        password = getpass.getpass("Owner password: ")

        if not password:
            print("The owner password must not be blank.")
            continue

        confirmation = getpass.getpass("Repeat owner password: ")

        if password == confirmation:
            return password

        print("Passwords don't match. Please try again")


def build_permissions(
    allow_print=False,
    allow_copy=False,
    allow_annotations=False,
):
    """
    Sets the permission defaults for the user.

    Defaults:
        - no printing
        - no copying
        - no annotations
        - no additional changes

    Parameters
    ==========
    allow_print: bool
    allow_copy: bool
    allow_annotations: bool

    Returns
    ==========
    permissions: dict

    """

    permissions = UserAccessPermissions.from_dict(
        {
            # printing
            "print": allow_print,
            # General changes are always prohibited.
            "modify": False,
            # copying / extracting
            "extract": allow_copy,
            # Add / change annotations
            "add_or_modify": allow_annotations,
            # no editing
            "fill_form_fields": False,
            # no extraction  of graphics
            "extract_text_and_graphics": allow_copy,
            # no page collation
            "assemble_doc": False,
            # no hq printing
            "print_to_representation": allow_print,
        }
    )

    return permissions


def add_watermark(
    input_pdf,
    output_pdf,
    text,
    user_password,
    owner_password,
    allow_print=False,
    allow_copy=False,
    allow_annotations=False,
    angle=45,
    opacity=0.18,
):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    total_pages = len(reader.pages)

    for page_number, page in enumerate(reader.pages, start=1):

        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        watermark = create_watermark_page(
            width=width,
            height=height,
            text=text,
            angle=angle,
            opacity=opacity,
        )

        page.merge_page(watermark)
        writer.add_page(page)

        print(
            f"\rProcessing page " f"{page_number} of {total_pages}...",
            end="",
            flush=True,
        )

    print()

    # copy existing metadata if present
    if reader.metadata:
        metadata = {
            key: value for key, value in reader.metadata.items() if value is not None
        }

        writer.add_metadata(metadata)

    # Create permission set
    permissions = build_permissions(
        allow_print=allow_print,
        allow_copy=allow_copy,
        allow_annotations=allow_annotations,
    )

    # AES-256 encryption
    #
    # user_password can be empty.
    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password,
        algorithm="AES-256",
        permissions_flag=permissions,
    )

    with open(output_pdf, "wb") as f:
        writer.write(f)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Adds a diagonal watermark to each page of a PDF file and protects the output file with AES-256."
        )
    )

    parser.add_argument(
        "input",
        help="PDF input file",
    )

    parser.add_argument(
        "output",
        help="PDF output file",
    )

    parser.add_argument(
        "--text",
        default="CONFIDENTIAL",
        help=("Watermark text " '(default: "CONFIDENTIAL")'),
    )

    parser.add_argument(
        "--angle",
        type=float,
        default=45,
        help="Rotation angle in degrees (default: 45)",
    )

    parser.add_argument(
        "--opacity",
        type=float,
        default=0.18,
        help=("Opacity level between 0 and 1 " "(default: 0.18)"),
    )

    parser.add_argument(
        "--allow-print",
        action="store_true",
        help="Allows PDF printing",
    )

    parser.add_argument(
        "--allow-copy",
        action="store_true",
        help=("Allows copying or extraction of text and graphics."),
    )

    parser.add_argument(
        "--allow-annotations",
        action="store_true",
        help=("Allows adding and changing annotations"),
    )

    args = parser.parse_args()

    if not 0 <= args.opacity <= 1:
        parser.error("--opacity value must be between 0 and 1.")

    print()
    print("Password protection:")
    print("===============")
    print()

    # User password is optional
    user_password = ask_optional_user_password()

    print()

    # Owner Password is mandatory
    owner_password = ask_owner_password()

    if user_password and owner_password == user_password:
        print(
            "\nError: User password and owner password are the same.",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print("Processing PDF file...")

    try:
        add_watermark(
            input_pdf=args.input,
            output_pdf=args.output,
            text=args.text,
            user_password=user_password,
            owner_password=owner_password,
            allow_print=args.allow_print,
            allow_copy=args.allow_copy,
            allow_annotations=args.allow_annotations,
            angle=args.angle,
            opacity=args.opacity,
        )

    except FileNotFoundError:
        print(
            f"\nError: File " f"'{args.input}' not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as exc:
        print(
            f"\nError during PDF processing: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print("Done.")
    print(f"Output file: {args.output}")
    print("Encryption: AES-256")

    print()
    print("Permissions")
    print("-------------")

    print("Printing     : ", "PERMITTED" if args.allow_print else "NOT PERMITTED")
    print("Copying      : ", "PERMITTED" if args.allow_copy else "NOT PERMITTED")
    print("Annotations  : ", "PERMITTED" if args.allow_annotations else "NOT PERMITTED")
    print("Modifications: NOT PERMITTED")
    print("Edit pages   : NOT PERMITTED")


if __name__ == "__main__":
    main()
