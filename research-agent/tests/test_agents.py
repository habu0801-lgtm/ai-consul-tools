import pytest
from agents.wikipedia_agent import WikipediaAgent
from agents.base_agent import BaseAgent


class TestWikipediaAgent:
    """Tests for Wikipedia agent."""

    @pytest.fixture
    def agent(self):
        return WikipediaAgent()

    def test_agent_initialization(self, agent):
        """Test agent is properly initialized."""
        assert agent.name == "wikipedia"
        assert agent.timeout == 35
        assert agent.base_url == "https://ja.wikipedia.org/w/api.php"

    def test_research_returns_dict(self, agent):
        """Test that research returns a properly structured dict."""
        result = agent.research("飲食店 AI")

        assert isinstance(result, dict)
        assert "source" in result
        assert "status" in result
        assert "data" in result
        assert "timestamp" in result
        assert "execution_time" in result

        assert result["source"] == "wikipedia"

    def test_research_success(self, agent):
        """Test successful research."""
        result = agent.research("飲食業")

        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert "articles" in result["data"]
            assert "total_found" in result["data"]
            assert isinstance(result["data"]["articles"], list)

    def test_research_timeout_handling(self, agent):
        """Test that research handles timeouts gracefully."""
        agent.timeout = 0.001  # Very short timeout
        result = agent.research("テスト")

        # Should either succeed or return error (not raise exception)
        assert isinstance(result, dict)
        assert "status" in result


class TestBaseAgent:
    """Tests for base agent."""

    def test_build_response(self):
        """Test response building."""
        agent = WikipediaAgent()

        response = agent._build_response("success", {"test": "data"})

        assert response["source"] == "wikipedia"
        assert response["status"] == "success"
        assert response["data"] == {"test": "data"}
        assert response["error"] is None
        assert "timestamp" in response

    def test_handle_error(self):
        """Test error handling."""
        agent = WikipediaAgent()

        response = agent._handle_error("Test error")

        assert response["status"] == "error"
        assert response["error"] == "Test error"
        assert response["data"] == {}
