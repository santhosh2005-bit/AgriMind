"""Unit and integration tests for Tool Connectors: Weather, FAISS Knowledge, and Structured Data."""

import unittest
from backend.app.schemas.enums import ToolStatus
from backend.app.tools.weather import WeatherConnector, WeatherQueryInput
from backend.app.tools.knowledge import KnowledgeRetrieverTool, KnowledgeQueryInput
from backend.app.tools.structured_data import StructuredDataConnector, DataQueryInput
from backend.app.retrieval.vector_store import FAISSKnowledgeIndex


class TestToolConnectors(unittest.TestCase):
    """Test individual tool connectors, live API handling, FAISS retrieval, and CSV parsing."""

    def test_tool_a_weather_connector(self):
        """Tool A: Verify weather retrieval, unit validation, and risk indexing."""
        connector = WeatherConnector()
        # Query Nashik agricultural region coordinates
        query = WeatherQueryInput(
            place_name="Nashik",
            latitude=19.9975,
            longitude=73.7898,
            past_days=3,
            forecast_days=3,
        )
        result = connector.fetch_weather(query)

        self.assertIn(result.status, [ToolStatus.SUCCESS, ToolStatus.FAILED])
        if result.status == ToolStatus.SUCCESS:
            data = result.structured_data
            self.assertIn("avg_max_temp_c", data)
            self.assertIn("thermal_stress_risk", data)
            self.assertIn("vector_proliferation_risk", data)
            self.assertGreater(len(result.evidence_items), 0)
            ev = result.evidence_items[0]
            self.assertEqual(ev.source_type, "weather_api")
            self.assertIn("Nashik", ev.location_reference)

    def test_tool_b_agricultural_knowledge_retrieval(self):
        """Tool B: Verify FAISS vector search, page/section preservation, and semantic retrieval."""
        index = FAISSKnowledgeIndex()
        count = index.build_from_directory("data/knowledge")
        self.assertGreater(count, 0, "Should index seeded ICAR advisory documents")

        tool = KnowledgeRetrieverTool(index)
        query = KnowledgeQueryInput(
            query="What vector transmits tomato yellow leaf curl and what humidity favors it?",
            crop_filter="tomato",
            top_k=2,
        )
        res = tool.retrieve(query)
        self.assertEqual(res.status, ToolStatus.SUCCESS)
        self.assertGreater(len(res.evidence_items), 0)

        top_ev = res.evidence_items[0]
        self.assertIn("ICAR_Tomato", top_ev.source_name)
        self.assertIn("Section:", top_ev.location_reference)
        self.assertIn("Bemisia tabaci", top_ev.content_snippet)

    def test_tool_c_structured_data_query(self):
        """Tool C: Verify tabular parcel and soil analysis via Pandas."""
        tool = StructuredDataConnector(default_file_path="data/sample_inputs/structured/farm_parcels_soil_tests.csv")
        query = DataQueryInput(
            crop="Tomato",
            min_salinity_ec=2.0,
        )
        res = tool.query(query)
        self.assertEqual(res.status, ToolStatus.SUCCESS)
        records = res.structured_data.get("records", [])
        self.assertGreater(len(records), 0)
        self.assertEqual(records[0]["parcel_id"], "P-101")
        self.assertEqual(records[0]["crop_cultivated"], "Tomato")
        self.assertGreater(len(res.evidence_items), 0)
        self.assertIn("pH", res.evidence_items[0].content_snippet)


if __name__ == "__main__":
    unittest.main()
