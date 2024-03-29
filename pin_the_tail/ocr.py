import re
from collections import namedtuple
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import pytesseract

from pin_the_tail.location import Region

OCRMatch = namedtuple("OCRMatch", ["index_start", "index_end", "region", "confidence"])


class OCRMatcher:
    def __init__(
        self,
        image_numpy_array: np.ndarray,
        language: Optional[str] = None,
        line_break: str = "\n",
        paragraph_break: str = "\n\n",
    ):
        self._image = image_numpy_array

        self._language = language

        self._df: Optional[pd.DataFrame] = None
        self.process(line_break, paragraph_break)

    @property
    def language(self):
        return self._language

    def _get_raw_ocr(self):
        if self._df is None:
            ocr_data = pytesseract.image_to_data(
                self._image, lang=self._language, output_type=pytesseract.Output.DATAFRAME
            )
            ocr_data = ocr_data.dropna()
            self._df = ocr_data
        return self._df

    def process(self, line_break="\n", paragraph_break="\n\n"):
        final_string = ""
        index_mapping = []
        for _, paragraph in self._get_raw_ocr().groupby(["page_num", "block_num", "par_num"]):
            if len(final_string) > 0:
                previous_region = index_mapping[-1].region
                index_mapping.append(
                    OCRMatch(
                        len(final_string),
                        len(final_string) + len(paragraph_break),
                        Region.from_coordinates(
                            previous_region.right,
                            previous_region.top,
                            paragraph.iloc[0]["left"],
                            previous_region.bottom,
                        ),
                        None,
                    )
                )
                final_string += paragraph_break

            new_paragraph = True
            for _, line in paragraph.groupby("line_num"):
                if len(final_string) > 0 and not new_paragraph:
                    previous_region = index_mapping[-1].region
                    index_mapping.append(
                        OCRMatch(
                            len(final_string),
                            len(final_string) + len(line_break),
                            Region.from_coordinates(
                                previous_region.right, previous_region.top, line.iloc[0]["left"], previous_region.bottom
                            ),
                            None,
                        )
                    )
                    final_string += line_break

                new_paragraph = False

                new_line = True
                for _, row in line.iterrows():
                    if row["text"] == "":
                        continue
                    if len(final_string) > 0 and not new_line:
                        previous_region = index_mapping[-1].region
                        index_mapping.append(
                            OCRMatch(
                                len(final_string),
                                len(final_string) + 1,
                                Region.from_coordinates(
                                    previous_region.right, previous_region.top, row["left"], previous_region.bottom
                                ),
                                None,
                            )
                        )
                        final_string += " "
                    index_mapping.append(
                        OCRMatch(
                            len(final_string),
                            len(final_string) + len(row["text"]),
                            Region(row["left"], row["top"], row["width"], row["height"]),
                            row["conf"] / 100,
                        )
                    )
                    final_string += row["text"]
                    new_line = False

        self._parsed_text = final_string
        self._ocr_segments = index_mapping

    @property
    def text(self) -> str:
        return self._parsed_text

    def find_bounding_boxes(
        self, needle: str, start: Optional[int] = None, end: Optional[int] = None, regex: bool = False, regex_flags=0
    ) -> Tuple[int, int, List[OCRMatch]]:
        """
        Find needle within the parsed string, returning the start and end indices and the bounding boxes
        encompassing the whole tokens found by the search.

        If the needle matches part of a token (e.g. needle="he" token="the"), then the start and end indices will be the
        start and end of the needle within the string, but the list of bounding boxes will be for the full tokens (e.g.
        the bounding box will be for "the", not just the "he" in it).  This may change in the future to be for just the
        matched part of a token.
        """
        no_match_found = -1, -1, []  # type: Tuple[int, int, List]

        start = start or 0
        end = end or len(self._parsed_text)
        text_to_search = self._parsed_text[start:end]

        if regex:
            match = re.search(needle, text_to_search, regex_flags)
            if match is None:
                return no_match_found
            index_start, index_end = match.span()
        else:
            index_start = text_to_search.find(needle)
            if index_start == -1:
                return no_match_found

            index_end = index_start + len(needle)

        index_start += start
        index_end += start

        for i, token in enumerate(self._ocr_segments):
            if token.index_start <= index_start < token.index_end:
                tokens = []
                if index_end <= token.index_end:
                    tokens.append(token)
                else:
                    end_token_i = i
                    while index_end >= token.index_end:
                        tokens.append(token)
                        end_token_i += 1
                        token = self._ocr_segments[end_token_i]

                return index_start, index_end, tokens
        return no_match_found

    def find_bounding_boxes_all(
        self, needle: str, start: Optional[int] = None, end: Optional[int] = None, regex: bool = False, regex_flags=0
    ) -> List[Tuple[int, int, List[OCRMatch]]]:
        results = []
        start = start or 0

        found = self.find_bounding_boxes(needle, start, end, regex, regex_flags)
        while found[0] != -1:
            results.append(found)
            start = found[1]
            found = self.find_bounding_boxes(needle, start, end, regex, regex_flags)

        return results

    def find(
        self, needle: str, start: Optional[int] = None, end: Optional[int] = None, regex: bool = False, regex_flags=0
    ) -> Optional[OCRMatch]:
        index_start, index_end, bounding_boxes = self.find_bounding_boxes(needle, start, end, regex, regex_flags)

        if len(bounding_boxes) > 0:
            return OCRMatch(
                index_start,
                index_end,
                Region.from_coordinates(
                    min(t.region.left for t in bounding_boxes),
                    min(t.region.top for t in bounding_boxes),
                    max(t.region.right for t in bounding_boxes),
                    max(t.region.bottom for t in bounding_boxes),
                ),
                min(t.confidence for t in bounding_boxes if t.confidence is not None),
            )

        return None

    def find_all(
        self,
        needle: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        regex: bool = False,
        regex_flags=0,
    ) -> List[OCRMatch]:
        results = []
        start = start or 0

        found = self.find(needle, start, end, regex, regex_flags)
        while found is not None:
            results.append(found)
            start = found[1]
            found = self.find(needle, start, end, regex, regex_flags)

        return results
