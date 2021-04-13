#!/usr/bin/env python
# -*- coding: utf-8 -*-


class TMSError(Exception):
    """Class for TMS error exception."""

    def __init__(self, code, message):
        super().__init__(message)
        self.message = message


class XMLError(Exception):
    """Class for XML error exception."""

    def __init__(self, code, message):
        super().__init__(message)
        self.message = message
