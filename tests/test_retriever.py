"""Tests for ContextRetriever — RAG-style context injection for Kama."""


class TestExtractGlazeNames:
    """Test _extract_glaze_names method."""

    def test_find_single_glaze(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        names = retriever._extract_glaze_names("Tell me about Chun Blue")
        assert "chun blue" in names

    def test_find_multiple_glazes(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        names = retriever._extract_glaze_names("Chun Blue over Iron Red")
        assert "chun blue" in names
        assert "iron red" in names

    def test_no_glaze_found(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        names = retriever._extract_glaze_names("What is pottery?")
        assert names == []

    def test_case_insensitive(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        names = retriever._extract_glaze_names("Tell me about shino")
        assert "shino" in names


class TestSearchChemistryRules:
    """Test _search_chemistry_rules method."""

    def test_chemistry_search_crawling(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        rules = retriever._search_chemistry_rules("crawling")
        assert len(rules) >= 1
        # Should find the Shino layering rule which mentions crawling
        titles = [r["title"] for r in rules]
        assert any("shino" in t.lower() or "layering" in t.lower() for t in titles)

    def test_chemistry_search_iron(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        rules = retriever._search_chemistry_rules("iron oxide")
        assert len(rules) >= 1
        titles = [r["title"] for r in rules]
        assert any("iron" in t.lower() for t in titles)

    def test_chemistry_search_no_match(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        rules = retriever._search_chemistry_rules("xyznonexistent")
        assert rules == []


class TestSearchCombinations:
    """Test _search_combinations method."""

    def test_combination_search_by_name(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        combos = retriever._search_combinations(["tenmoku"])
        assert len(combos) >= 1

    def test_combination_search_no_match(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        combos = retriever._search_combinations(["nonexistent"])
        assert combos == []


class TestRetrieve:
    """Test the main retrieve() method."""

    def test_empty_context(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("What is pottery?")
        assert result == ""

    def test_context_has_sections(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("Tell me about Chun Blue")
        assert "## Studio Glazes" in result
        assert "Chun Blue" in result

    def test_context_size_limit(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("Tell me about Chun Blue and Iron Red and Shino")
        assert len(result) < 4000

    def test_context_includes_chemistry(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("What causes crawling?")
        assert "## Chemistry Rules" in result

    def test_context_includes_combinations(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("Tell me about Tenmoku combinations")
        assert "## Known Combinations" in result

    def test_full_combo_question(self, test_db_path):
        from core.ai.context import ContextRetriever

        retriever = ContextRetriever(test_db_path)
        result = retriever.retrieve("What happens if I layer Chun Blue over Iron Red?")
        assert "## Studio Glazes" in result
        assert "Chun Blue" in result
        assert "Iron Red" in result
