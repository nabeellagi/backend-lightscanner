"""Build a multi-page PDF from PIL images, entirely in memory."""

import io
from collections.abc import Callable

import img2pdf
from PIL import Image


def _make_layout_fun(settings: dict) -> Callable:
    """
    Make an img2pdf layout function for the batch.

    img2pdf calls the layout function once for each image.
    The closure walks through the frontend's layout data
    in upload order.
    """

    page_width_pt = img2pdf.in_to_pt(
        settings["pageWidthIn"]
    )

    page_height_pt = img2pdf.in_to_pt(
        settings["pageHeightIn"]
    )

    layouts = iter(
        settings["images"]
    )

    def layout_fun(
        img_width_px,
        img_height_px,
        ndpi,
    ):
        item = next(layouts)

        rendered_width_pt = img2pdf.in_to_pt(
            item["renderedWidthIn"]
        )

        rendered_height_pt = img2pdf.in_to_pt(
            item["renderedHeightIn"]
        )

        # "Fit to page"
        item_page_width_in = item.get("pageWidthIn")
        item_page_height_in = item.get("pageHeightIn")

        item_page_width_pt = (
            img2pdf.in_to_pt(item_page_width_in)
            if item_page_width_in
            else page_width_pt
        )

        item_page_height_pt = (
            img2pdf.in_to_pt(item_page_height_in)
            if item_page_height_in
            else page_height_pt
        )

        return (
            item_page_width_pt,
            item_page_height_pt,
            rendered_width_pt,
            rendered_height_pt,
        )

    return layout_fun


def build_pdf_from_images(
    images: list[Image.Image],
    settings: dict | None = None,
) -> bytes:

    if not images:
        raise ValueError(
            "build_pdf_from_images requires "
            "at least one image."
        )

    encoded_pages: list[bytes] = []

    for image in images:
        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=92,
        )

        encoded_pages.append(
            buffer.getvalue()
        )

    if settings is None:
        return img2pdf.convert(
            encoded_pages
        )
        
    if (
        len(settings["images"])
        != len(encoded_pages)
    ):
        raise ValueError(
            "Every PDF page needs exactly "
            "one image layout entry."
        )

    layout_fun = _make_layout_fun(
        settings
    )

    return img2pdf.convert(
        encoded_pages,
        layout_fun=layout_fun,
    )