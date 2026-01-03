"""Tests for Japanese address extraction."""

import json
import pytest
from extract_address_tool.extract import (
    extract_addresses,
    extract_addresses_list,
    extract_addresses_detailed
)


class TestExtractAddresses:
    """Test suite for extract_addresses function."""

    def test_single_address(self):
        """Test extracting a single address."""
        text = "本社は東京都渋谷区にあります。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert "東京都渋谷区" in addresses

    def test_multiple_addresses(self):
        """Test extracting multiple addresses."""
        text = "本社は東京都渋谷区にあります。支社は大阪府大阪市です。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 2
        assert "東京都渋谷区" in addresses
        assert "大阪府大阪市" in addresses

    def test_hokkaido_address(self):
        """Test extracting Hokkaido address (no 県 suffix)."""
        text = "北海道札幌市中央区に行きました。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert "北海道札幌市中央区" in addresses

    def test_kyoto_address(self):
        """Test extracting Kyoto address with 府."""
        text = "京都府京都市中京区の店舗"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert "京都府京都市中京区" in addresses

    def test_town_address(self):
        """Test extracting town (町) level address."""
        text = "青森県上北郡六戸町に住んでいます。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert "青森県上北郡六戸町" in addresses

    def test_village_address(self):
        """Test extracting village (村) level address."""
        text = "長野県下高井郡山ノ内町と群馬県吾妻郡草津町があります。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) >= 2

    def test_no_addresses(self):
        """Test text with no addresses."""
        text = "これは住所を含まないテキストです。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 0

    def test_empty_text(self):
        """Test with empty text."""
        result = extract_addresses("")
        addresses = json.loads(result)
        assert len(addresses) == 0

    def test_duplicate_addresses(self):
        """Test that duplicate addresses are not returned."""
        text = "東京都渋谷区にあります。また、東京都渋谷区に行きます。"
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert "東京都渋谷区" in addresses

    def test_various_prefectures(self):
        """Test addresses from various prefectures."""
        text = """
        福岡県福岡市、北海道札幌市、沖縄県那覇市、
        神奈川県横浜市、愛知県名古屋市
        """
        result = extract_addresses(text)
        addresses = json.loads(result)
        assert len(addresses) == 5
        assert "福岡県福岡市" in addresses
        assert "北海道札幌市" in addresses
        assert "沖縄県那覇市" in addresses
        assert "神奈川県横浜市" in addresses
        assert "愛知県名古屋市" in addresses


class TestExtractAddressesList:
    """Test suite for extract_addresses_list function."""

    def test_returns_list(self):
        """Test that function returns a Python list."""
        text = "東京都渋谷区にあります。"
        result = extract_addresses_list(text)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "東京都渋谷区"

    def test_empty_list(self):
        """Test empty text returns empty list."""
        result = extract_addresses_list("")
        assert isinstance(result, list)
        assert len(result) == 0


class TestExtractAddressesDetailed:
    """Test suite for extract_addresses_detailed function."""

    def test_detailed_structure(self):
        """Test detailed output structure."""
        text = "東京都渋谷区にあります。"
        result = extract_addresses_detailed(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert addresses[0]["full_address"] == "東京都渋谷区"
        assert addresses[0]["prefecture"] == "東京都"
        assert addresses[0]["city"] == "渋谷区"
        assert addresses[0]["county"] is None

    def test_detailed_with_county(self):
        """Test detailed output with county (郡)."""
        text = "青森県上北郡六戸町にあります。"
        result = extract_addresses_detailed(text)
        addresses = json.loads(result)
        assert len(addresses) == 1
        assert addresses[0]["prefecture"] == "青森県"
        assert addresses[0]["county"] == "上北郡"
        assert addresses[0]["city"] == "六戸町"

    def test_detailed_multiple(self):
        """Test detailed output with multiple addresses."""
        text = "東京都渋谷区と大阪府大阪市"
        result = extract_addresses_detailed(text)
        addresses = json.loads(result)
        assert len(addresses) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
