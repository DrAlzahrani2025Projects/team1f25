from core.services.result_formatter import ResultFormatter


def test_is_peer_reviewed_from_facets_variants():
    variants = [
        ["peer_reviewed"],
        ["Peer Reviewed"],
        ["peer-reviewed"],
        ["some", "Peer Reviewed"],
    ]

    for tlevel in variants:
        assert ResultFormatter._is_peer_reviewed_from_facets(tlevel) is True


def test_is_not_peer_reviewed_when_missing_or_other():
    assert ResultFormatter._is_peer_reviewed_from_facets([]) is False
    assert ResultFormatter._is_peer_reviewed_from_facets(["other"]) is False
"""
Unit tests for ResultFormatter service.
Tests parsing and formatting logic without external dependencies.
"""
import pytest
from core.services.result_formatter import ResultFormatter


class TestResultFormatter:
    """Unit tests for ResultFormatter class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.formatter = ResultFormatter()
        
        # Mock document data
        self.mock_doc = {
            "pnx": {
                "display": {
                    "title": ["Test Article Title"],
                    "creator": ["John Doe", "Jane Smith"],
                    "type": ["article"],
                    "source": ["Test Journal"],
                    "creationdate": ["2023"]
                },
                "addata": {
                    "pub": ["Test Publisher"],
                    "issn": ["1234-5678"],
                    "doi": ["10.1234/test"],
                    "date": ["2023-01-15"]
                },
                "control": {
                    "recordid": ["TN_test123"]
                }
            },
            "context": "L"
        }
    
    def test_parse_document_basic(self):
        """Test basic document parsing."""
        result = ResultFormatter.parse_document(self.mock_doc)
        
        assert result["title"] == "Test Article Title"
        assert result["author"] == "John Doe"
        assert result["type"] == "article"
        assert result["source"] == "Test Journal"
        assert result["publisher"] == "Test Publisher"
        assert result["issn"] == "1234-5678"
        assert result["doi"] == "10.1234/test"
    
    def test_parse_document_year_extraction(self):
        """Test year extraction from dates."""
        result = ResultFormatter.parse_document(self.mock_doc)
        assert result["date"] == "2023"
    
    def test_parse_document_link_generation(self):
        """Test discovery link generation."""
        result = ResultFormatter.parse_document(self.mock_doc)
        
        assert "https://csu-sb.primo.exlibrisgroup.com/discovery/fulldisplay" in result["link"]
        assert "docid=TN_test123" in result["link"]
        assert "context=L" in result["link"]
    
    def test_parse_document_missing_fields(self):
        """Test parsing with missing fields."""
        minimal_doc = {"pnx": {"display": {}, "addata": {}, "control": {}}}
        result = ResultFormatter.parse_document(minimal_doc)
        
        assert result["title"] == "N/A"
        assert result["author"] == "N/A"
        assert result["date"] == "N/A"
    
    def test_filter_by_resource_type_article(self):
        """Test filtering by article type."""
        docs = [self.mock_doc]
        filtered = ResultFormatter.filter_by_resource_type(docs, "article")
        
        assert len(filtered) == 1
    
    def test_filter_by_resource_type_book(self):
        """Test filtering by book type."""
        docs = [self.mock_doc]
        filtered = ResultFormatter.filter_by_resource_type(docs, "book")
        
        assert len(filtered) == 0  # Mock doc is an article
    
    def test_format_table_data(self):
        """Test table data formatting."""
        docs = [self.mock_doc]
        table_data = ResultFormatter.format_table_data(docs)
        
        assert len(table_data) == 1
        assert table_data[0]["#"] == 1
        assert table_data[0]["Title"] == "Test Article Title"
        assert table_data[0]["Authors"] == "John Doe"
        assert table_data[0]["Year"] == "2023"
        assert table_data[0]["Type"] == "article"
    
    def test_format_table_data_truncation(self):
        """Test title and author truncation in table."""
        long_title_doc = self.mock_doc.copy()
        long_title_doc["pnx"]["display"]["title"] = ["A" * 100]
        long_title_doc["pnx"]["display"]["creator"] = ["B" * 50]
        
        table_data = ResultFormatter.format_table_data([long_title_doc])
        
        assert len(table_data[0]["Title"]) <= 83  # 80 + "..."
        assert len(table_data[0]["Authors"]) <= 43  # 40 + "..."
    
    def test_resource_type_mappings(self):
        """Test resource type mappings."""
        assert "article" in ResultFormatter.RESOURCE_TYPE_MAPPINGS
        assert "book" in ResultFormatter.RESOURCE_TYPE_MAPPINGS
        assert "journal" in ResultFormatter.RESOURCE_TYPE_MAPPINGS
        assert "thesis" in ResultFormatter.RESOURCE_TYPE_MAPPINGS
