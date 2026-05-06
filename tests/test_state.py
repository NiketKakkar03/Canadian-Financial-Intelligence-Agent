from src.state import ResearchState


def test_default_initialization():
    state = ResearchState()
    assert state.query == ""
    assert state.thread_id == ""
    assert state.financials is None
    assert state.web_research is None
    assert state.report is None


def test_error_flags_default_to_false():
    state = ResearchState()
    assert state.financial_agent_error is False
    assert state.web_research_agent_error is False


def test_partial_state_missing_financials_is_valid():
    state = ResearchState(query="RBC Q4", thread_id="abc", web_research="some commentary")
    assert state.financials is None
    assert state.web_research == "some commentary"


def test_partial_state_missing_web_research_is_valid():
    state = ResearchState(query="RBC Q4", thread_id="abc", financials="revenue data")
    assert state.web_research is None
    assert state.financials == "revenue data"
