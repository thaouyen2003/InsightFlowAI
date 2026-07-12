from app.services.dashboard.kpi_generator import KPIGenerator
from app.services.dashboard.chart_generator import ChartGenerator


class DashboardService:

    def __init__(self):

        self.kpi_generator = KPIGenerator()
        self.chart_generator = ChartGenerator()


    def generate(self, dataframe):

        summary = {

            "rows": len(dataframe),

            "columns": len(dataframe.columns)

        }

        kpis = self.kpi_generator.generate(dataframe)

        charts = self.chart_generator.generate(dataframe)

        return {

            "summary": summary,

            "kpis": kpis,

            "charts": charts

        }