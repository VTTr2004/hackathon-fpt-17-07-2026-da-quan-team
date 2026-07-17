from app.modules.base import Analyzer
from app.modules.business_model.analyzer import BusinessModelAnalyzer
from app.modules.cash_flow.analyzer import CashFlowAnalyzer
from app.modules.surrounding_area.analyzer import SurroundingAreaAnalyzer
from app.schemas.common import AnalysisModule

ANALYZERS: dict[AnalysisModule, Analyzer] = {
    AnalysisModule.BUSINESS_MODEL: BusinessModelAnalyzer(),
    AnalysisModule.CASH_FLOW: CashFlowAnalyzer(),
    AnalysisModule.SURROUNDING_AREA: SurroundingAreaAnalyzer(),
}


def get_analyzer(module: AnalysisModule) -> Analyzer:
    return ANALYZERS[module]
