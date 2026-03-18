from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DownloadStatus(str, Enum):
    PENDING = "pending"
    FETCHING_DETAIL = "fetching_detail"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class Source(str, Enum):
    IEEE = "IEEE"
    NATURE = "Nature"


@dataclass
class Author:
    name: str
    affiliation: str = ""


@dataclass
class Paper:
    title: str
    authors: list[Author] = field(default_factory=list)
    journal: str = ""
    year: str = ""
    abstract: str = ""
    doi: str = ""
    url: str = ""
    pdf_url: str = ""
    source: str = ""
    # IEEE specific
    arnumber: str = ""

    def first_author_surname(self) -> str:
        if not self.authors:
            return "Unknown"
        name = self.authors[0].name.strip()
        # 尝试取姓氏（最后一个词）
        parts = name.split()
        return parts[-1] if parts else "Unknown"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": [{"name": a.name, "affiliation": a.affiliation} for a in self.authors],
            "journal": self.journal,
            "year": self.year,
            "abstract": self.abstract,
            "doi": self.doi,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "source": self.source,
            "arnumber": self.arnumber,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        authors = [Author(**a) for a in d.get("authors", [])]
        return cls(
            title=d.get("title", ""),
            authors=authors,
            journal=d.get("journal", ""),
            year=d.get("year", ""),
            abstract=d.get("abstract", ""),
            doi=d.get("doi", ""),
            url=d.get("url", ""),
            pdf_url=d.get("pdf_url", ""),
            source=d.get("source", ""),
            arnumber=d.get("arnumber", ""),
        )


@dataclass
class DownloadTask:
    paper: Paper
    status: DownloadStatus = DownloadStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
    file_path: str = ""

    def to_dict(self) -> dict:
        return {
            "paper": self.paper.to_dict(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "file_path": self.file_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DownloadTask":
        paper = Paper.from_dict(d.get("paper", {}))
        status = DownloadStatus(d.get("status", "pending"))
        # 中断的下载重置为 pending
        if status in (DownloadStatus.FETCHING_DETAIL, DownloadStatus.DOWNLOADING):
            status = DownloadStatus.PENDING
        return cls(
            paper=paper,
            status=status,
            retry_count=d.get("retry_count", 0),
            error_message=d.get("error_message", ""),
            file_path=d.get("file_path", ""),
        )
