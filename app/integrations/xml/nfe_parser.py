from __future__ import annotations

from app.services.nota_xml_parser_service import NotaXmlParserService


def parse_nfe_xml_file(xml_path: str) -> dict:
    return NotaXmlParserService().parse_file(xml_path)