from app.services.dashboard_layout import DashboardLayout



charts = [

    {
        "type":"pie",
        "title":"Status"
    },


    {
        "type":"bar",
        "title":"Category"
    },


    {
        "type":"line",
        "title":"Revenue Trend"
    }

]


layout = DashboardLayout()


result = layout.generate(charts)


print(result)