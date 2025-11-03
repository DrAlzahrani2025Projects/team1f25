Feature: Top 5 Functional Requirements - Search Flow
  This feature captures the high-level acceptance scenarios for the top 5
  functional requirements described in the SRS (FR-1 .. FR-5).

  Background:
    Given the application is running
    And a mock LLM is available
    And the library API is reachable

  Scenario: FR-1 Conversational Input
    Given a user opens the chat interface
    When the user submits "I need articles about machine learning"
    Then the user message is recorded in session_state
    And the assistant displays an acknowledgement or follow-up message

  Scenario: FR-2 Determine Search Intent
    Given no prior messages
    When the user submits "Search now for climate change articles"
    Then the system triggers a library search
    And the search service is invoked with query "climate change articles"

  Scenario: FR-3 LLM Follow-up & Readiness
    Given the conversation contains user messages:
      | role | content                             |
      | user | I want sources on renewable energy  |
    And the LLM will respond with "READY_TO_SEARCH"
    When the orchestrator requests a follow-up from the LLM
    Then the orchestrator triggers a search

  Scenario Outline: FR-4 Parameter Extraction
    Given the conversation history includes:
      | role | content           |
      | user | <user_message>    |
    And the parameter-extraction LLM returns the JSON:
      """
      {"query": "<query>", "limit": <limit>, "resource_type": "<resource_type>"}
      """
    When parameters are extracted
    Then the system should use query "<query>", limit <limit>, and resource type "<resource_type>" for the search

    Examples:
      | user_message                              | query              | limit | resource_type |
      | Find 5 articles about CRISPR              | CRISPR             | 5     | article       |
      | I need books on medieval history, 3 items | medieval history   | 3     | book          |

  Scenario: FR-5 Library Search and Display
    Given the search service is available
    And the library returns a response with docs and info.total = 2
    When the user triggers a search for "machine learning"
    Then the UI displays a results table with 2 rows
    And the results include links to the Primo fulldisplay
