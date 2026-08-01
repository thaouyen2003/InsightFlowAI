class DashboardLayout:


    def generate(self, charts):

        layout = []


        # Priority order

        priority = {

            "line": 1,

            "bar": 2,

            "pie": 3

        }



        sorted_charts = sorted(
            charts,
            key=lambda x:
            priority.get(
                x.get("type"),
                99
            )
        )



        for index, chart in enumerate(sorted_charts):

            layout.append({

                "position": index + 1,

                "chart": chart

            })


        return layout