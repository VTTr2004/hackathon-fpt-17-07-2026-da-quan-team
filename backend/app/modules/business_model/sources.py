from dataclasses import dataclass

from app.schemas.common import Evidence


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    title: str
    authors: str
    year: int
    publisher: str
    doi: str

    def to_evidence(self) -> Evidence:
        return Evidence(
            evidence_id=self.source_id,
            source_type="peer_reviewed_research",
            title=self.title,
            publisher=self.publisher,
            url=f"https://doi.org/{self.doi}",
            reliability="high",
            notes=f"{self.authors} ({self.year}). Nguồn dùng cho phương pháp đánh giá, không thay thế dữ liệu startup.",
        )


SOURCES: dict[str, ResearchSource] = {
    source.source_id: source
    for source in (
        ResearchSource(
            "SRC-BM-TEECE-2010",
            "Business Models, Business Strategy and Innovation",
            "David J. Teece",
            2010,
            "Long Range Planning",
            "10.1016/j.lrp.2009.07.003",
        ),
        ResearchSource(
            "SRC-CVP-PAYNE-2017",
            "The customer value proposition: evolution, development, and application in marketing",
            "Adrian Payne, Pennie Frow & Andreas Eggert",
            2017,
            "Journal of the Academy of Marketing Science",
            "10.1007/s11747-017-0523-z",
        ),
        ResearchSource(
            "SRC-MKT-NARVER-1990",
            "The Effect of a Market Orientation on Business Profitability",
            "John C. Narver & Stanley F. Slater",
            1990,
            "Journal of Marketing",
            "10.1177/002224299005400403",
        ),
        ResearchSource(
            "SRC-RETAIL-SORESCU-2011",
            "Innovations in Retail Business Models",
            "Alina Sorescu et al.",
            2011,
            "Journal of Retailing",
            "10.1016/j.jretai.2011.04.005",
        ),
        ResearchSource(
            "SRC-CHANNEL-VERHOEF-2015",
            "From Multi-Channel Retailing to Omni-Channel Retailing",
            "Peter C. Verhoef, P.K. Kannan & J. Jeffrey Inman",
            2015,
            "Journal of Retailing",
            "10.1016/j.jretai.2015.02.005",
        ),
        ResearchSource(
            "SRC-UNIT-NOONE-2020",
            "Menu engineering re-engineered",
            "Breffni M. Noone & Gerard Cachia",
            2020,
            "International Journal of Hospitality Management",
            "10.1016/j.ijhm.2020.102504",
        ),
        ResearchSource(
            "SRC-SCALE-WINTER-2001",
            "Replication as Strategy",
            "Sidney G. Winter & Gabriel Szulanski",
            2001,
            "Organization Science",
            "10.1287/orsc.12.6.730.10084",
        ),
        ResearchSource(
            "SRC-LEARN-SOSNA-2010",
            "Business Model Innovation through Trial-and-Error Learning: The Naturhouse Case",
            "Marc Sosna, Rosa Nelly Trevinyo-Rodríguez & S. Ramakrishna Velamuri",
            2010,
            "Long Range Planning",
            "10.1016/j.lrp.2010.02.003",
        ),
    )
}


def evidence_for(source_ids: set[str]) -> list[Evidence]:
    return [SOURCES[source_id].to_evidence() for source_id in sorted(source_ids) if source_id in SOURCES]
