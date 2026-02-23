from sttcli.formatters.base import BaseFormatter


def get_formatter(name: str) -> type[BaseFormatter]:
    if name == "markdown":
        from sttcli.formatters.markdown import MarkdownFormatter
        return MarkdownFormatter
    elif name == "srt":
        from sttcli.formatters.srt import SRTFormatter
        return SRTFormatter
    elif name == "json":
        from sttcli.formatters.json_fmt import JSONFormatter
        return JSONFormatter
    elif name == "text":
        from sttcli.formatters.text import TextFormatter
        return TextFormatter
    else:
        raise ValueError(f"Unknown formatter: {name}")
